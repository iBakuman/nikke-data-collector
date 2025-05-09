"""
Screen state classes for the automation framework.

This module provides classes for detecting and representing different screen states
in the game, which are essential for navigation and automation logic.
"""

from typing import Dict, List, Optional

from PIL import Image

from .context import Result
from .elements import UIElement
from .enums import StateType


class ScreenState:
    """Represents a specific screen state in the application.

    A screen state is defined by a set of UI elements that should be present
    and a set that should be absent when the application is in this state.
    """

    def __init__(self,
                 state_type: StateType,
                 required_elements: Optional[List[UIElement]] = None,
                 excluded_elements: Optional[List[UIElement]] = None,
                 confidence_threshold: float = 0.8):
        """Initialize a screen state.

        Args:
            state_type: The type of screen state
            required_elements: UI elements that must be present in this state
            excluded_elements: UI elements that must not be present in this state
            confidence_threshold: Minimum confidence level required (0.0 to 1.0)
        """
        self.state_type = state_type
        self.required_elements = required_elements or []
        self.excluded_elements = excluded_elements or []
        self.confidence_threshold = confidence_threshold

    def is_active(self, screenshot: Image.Image) -> Result[bool]:
        """Check if this state is active in the given screenshot.

        Args:
            screenshot: The screenshot to check

        Returns:
            Result indicating whether this state is active
        """
        # Check for required elements
        required_matches = 0
        missing_elements = []

        for element in self.required_elements:
            ok = element.is_visible(screenshot)
            if ok:
                required_matches += 1
            else:
                missing_elements.append(element)

        # Check for excluded elements
        excluded_matches = 0
        unexpected_elements = []

        for element in self.excluded_elements:
            ok = element.is_visible(screenshot)
            if not ok:
                excluded_matches += 1
            else:
                unexpected_elements.append(element)

        # Calculate confidence level
        required_confidence = 1.0 if not self.required_elements else required_matches / len(self.required_elements)
        excluded_confidence = 1.0 if not self.excluded_elements else excluded_matches / len(self.excluded_elements)

        # Combine confidence scores
        overall_confidence = (required_confidence + excluded_confidence) / 2

        # Check if confidence meets the threshold
        if overall_confidence >= self.confidence_threshold:
            return Result.success(True)

        # If we have errors, report them
        if missing_elements or unexpected_elements:
            error_message = "missing: " + "; ".join(missing_elements) + " unexpected: " + "; ".join(unexpected_elements)
            return Result.failure(f"State check failed: {error_message}")
        # Otherwise, just report that the state is not active
        return Result.success(False)


class StateDetector:
    """Detects the current screen state from a screenshot.

    This class manages a collection of screen states and determines which one
    best matches the current screenshot.
    """

    def __init__(self, states: Optional[List[ScreenState]] = None):
        """Initialize a state detector.

        Args:
            states: List of screen states to detect
        """
        self.states = states or []
        self._state_map: Dict[StateType, ScreenState] = {state.state_type: state for state in self.states}

    def add_state(self, state: ScreenState) -> None:
        """Add a screen state to the detector.

        Args:
            state: The screen state to add
        """
        self.states.append(state)
        self._state_map[state.state_type] = state

    def detect_state(self, screenshot: Image.Image) -> Result[Optional[StateType]]:
        """Detect the current screen state from a screenshot.

        Args:
            screenshot: The screenshot to analyze

        Returns:
            Result containing the detected state type or None if no match
        """
        best_state = None
        best_confidence = 0.0
        errors = []

        # Check each state
        for state in self.states:
            result = state.is_active(screenshot)

            if not result.success:
                errors.append(f"Error checking state {state.state_type}: {result.error}")
                continue

            if result.data:
                # This state is active, get its confidence
                required_matches = sum(1 for element in state.required_elements
                                       if element.is_visible(screenshot))

                excluded_matches = sum(1 for element in state.excluded_elements
                                       if not element.is_visible(screenshot))

                total_elements = len(state.required_elements) + len(state.excluded_elements)

                if total_elements > 0:
                    confidence = (required_matches + excluded_matches) / total_elements

                    # Update best match if this state has higher confidence
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_state = state.state_type

        # Return the best matching state, or None if no match
        if best_state:
            return Result.success(best_state)

        # If we have errors and no match, report the errors
        if errors and not best_state:
            error_message = "; ".join(errors)
            return Result.failure(f"State detection failed: {error_message}")

        # No match, but no errors either
        return Result.success(None)

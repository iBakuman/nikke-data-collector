"""
Condition classes for the automation framework.

This module provides classes for defining various conditions that can be
checked during the automation process.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from PIL import Image

from .context import AutomationContext, Result
from .elements import UIElement
from .enums import StateType


class AutomationCondition(ABC):
    """Base class for all conditions in the automation framework.
    
    Conditions are used to determine whether certain criteria are met
    during automation, such as waiting for elements to appear or 
    checking the current screen state.
    """
    
    @abstractmethod
    def check(self, context: AutomationContext, screenshot: Image.Image) -> Result[bool]:
        """Check if the condition is met.
        
        Args:
            context: The current automation context
            screenshot: The current screenshot
            
        Returns:
            Result indicating whether the condition is met
        """
        pass


class WaitCondition(AutomationCondition):
    """Condition for waiting a specific amount of time.
    
    This condition is always successful after the specified time has passed.
    """
    
    def __init__(self, wait_seconds: float):
        """Initialize a wait condition.
        
        Args:
            wait_seconds: The number of seconds to wait
        """
        self.wait_seconds = wait_seconds
        self.start_time = None
    
    def check(self, context: AutomationContext, screenshot: Image.Image) -> Result[bool]:
        """Check if the wait time has elapsed.
        
        Args:
            context: The current automation context
            screenshot: The current screenshot
            
        Returns:
            Result indicating whether the wait time has elapsed
        """
        import time

        # Initialize start time if not set
        if self.start_time is None:
            self.start_time = time.time()
        
        # Check if enough time has passed
        elapsed = time.time() - self.start_time
        if elapsed >= self.wait_seconds:
            return Result.success(True)
        
        return Result.success(False)


class ElementCondition(AutomationCondition):
    """Condition for checking if UI elements are present or absent.
    
    This condition checks for the presence or absence of specific UI elements
    on the screen.
    """
    
    def __init__(self, elements: List[UIElement], all_must_match: bool = True, 
                 should_exist: bool = True):
        """Initialize an element condition.
        
        Args:
            elements: List of UI elements to check
            all_must_match: Whether all elements must match the condition
            should_exist: Whether the elements should exist or be absent
        """
        self.elements = elements
        self.all_must_match = all_must_match
        self.should_exist = should_exist
    
    def check(self, context: AutomationContext, screenshot: Image.Image) -> Result[bool]:
        """Check if the elements exist or are absent as specified.
        
        Args:
            context: The current automation context
            screenshot: The current screenshot
            
        Returns:
            Result indicating whether the condition is met
        """
        results = {}
        
        # Check each element
        for element in self.elements:
            result = element.is_visible(screenshot)
            elements_match = result.success and result.data == self.should_exist
            results[element] = elements_match
            
            # Early return if using any_must_match and we found a match
            if not self.all_must_match and elements_match:
                return Result.success(True)
            
            # Early return if using all_must_match and we found a non-match
            if self.all_must_match and not elements_match:
                return Result.success(False)
        
        # If all_must_match, all elements must match
        # If not all_must_match, at least one element must match
        return Result.success(self.all_must_match)


class StateCondition(AutomationCondition):
    """Condition for checking the current screen state.
    
    This condition checks if the current screen matches a specific state
    or one of several possible states.
    """
    
    def __init__(self, states: List[StateType]):
        """Initialize a state condition.
        
        Args:
            states: List of states to check for
        """
        self.states = states
    
    def check(self, context: AutomationContext, screenshot: Image.Image) -> Result[bool]:
        """Check if the current screen matches one of the specified states.
        
        Args:
            context: The current automation context
            screenshot: The current screenshot
            
        Returns:
            Result indicating whether the condition is met
        """
        # Get the current state from the context
        current_state = context.current_state
        
        # Check if the current state is one of the specified states
        if current_state in self.states:
            return Result.success(True)
        
        return Result.success(False)


class MultiCondition(AutomationCondition):
    """Condition that combines multiple conditions with logical operations.
    
    This condition allows combining other conditions with AND or OR logic.
    """
    
    def __init__(self, conditions: List[AutomationCondition], require_all: bool = True):
        """Initialize a multi-condition.
        
        Args:
            conditions: List of conditions to check
            require_all: Whether all conditions must be met (AND) or just one (OR)
        """
        self.conditions = conditions
        self.require_all = require_all
    
    def check(self, context: AutomationContext, screenshot: Image.Image) -> Result[bool]:
        """Check if the combined conditions are met.
        
        Args:
            context: The current automation context
            screenshot: The current screenshot
            
        Returns:
            Result indicating whether the conditions are met
        """
        results = {}
        
        # Check each condition
        for condition in self.conditions:
            result = condition.check(context, screenshot)
            
            # Handle errors
            if not result.success:
                return Result.failure(f"Condition check failed: {result.error}")
            
            results[condition] = result.data
            
            # Early return for OR logic if any condition is true
            if not self.require_all and result.data:
                return Result.success(True)
            
            # Early return for AND logic if any condition is false
            if self.require_all and not result.data:
                return Result.success(False)
        
        # If we get here with AND logic, all conditions were true
        # If we get here with OR logic, all conditions were false
        return Result.success(self.require_all) 

"""
Controller class for the automation framework.

This module provides the main controller class that coordinates the automation
process, including capturing screenshots, executing steps, and managing state.
"""

import time
from typing import Dict, List, Optional

from PIL import Image

from .context import AutomationContext, Result
from .enums import StateType, StepId
from .states import ScreenState, StateDetector
from .steps import AutomationStep


class AutomationController:
    """Main controller for the automation framework.
    
    This class coordinates the automation process, including capturing screenshots,
    detecting screen states, executing steps, and managing the automation context.
    """
    
    def __init__(self, 
                 state_detector: Optional[StateDetector] = None,
                 steps: Optional[Dict[StepId, AutomationStep]] = None):
        """Initialize an automation controller.
        
        Args:
            state_detector: Detector for identifying screen states
            steps: Dictionary of automation steps by ID
        """
        self.state_detector = state_detector or StateDetector()
        self.steps = steps or {}
        self.context = AutomationContext()
    
    def add_state(self, state: ScreenState) -> None:
        """Add a screen state to the detector.
        
        Args:
            state: The screen state to add
        """
        self.state_detector.add_state(state)
    
    def add_step(self, step: AutomationStep) -> None:
        """Add an automation step.
        
        Args:
            step: The automation step to add
        """
        self.steps[step.step_id] = step
    
    def get_screenshot(self) -> Result[Image.Image]:
        """Capture a screenshot of the screen.
        
        Returns:
            Result containing the captured screenshot or error
        """
        try:
            # TODO: Implement actual screenshot capturing
            # This is a placeholder implementation
            # Example implementation with PIL:
            # import pyautogui
            # screenshot = pyautogui.screenshot()
            
            # Placeholder implementation with a dummy image
            from PIL import Image, ImageDraw

            # Create a dummy image for testing
            image = Image.new('RGB', (1280, 720), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            draw.rectangle([(0, 0), (1279, 719)], outline=(0, 0, 0))
            draw.text((640, 360), "Placeholder Screenshot", fill=(0, 0, 0))
            
            return Result.success(image)
        except Exception as e:
            return Result.failure(f"Screenshot capture failed: {str(e)}")
    
    def detect_state(self) -> Result[StateType]:
        """Detect the current screen state.
        
        Returns:
            Result containing the detected state type or None if no match
        """
        # Capture a screenshot
        screenshot_result = self.get_screenshot()
        if not screenshot_result.success:
            return Result.failure(f"State detection failed: {screenshot_result.error}")
        
        # Detect the state
        state_result = self.state_detector.detect_state(screenshot_result.data)
        if not state_result.success:
            return Result.failure(f"State detection failed: {state_result.error}")
        
        # Update the context with the detected state
        self.context.current_state = state_result.data
        
        return state_result
    
    def execute_step(self, step_id: StepId) -> Result:
        """Execute a specific automation step.
        
        Args:
            step_id: ID of the step to execute
            
        Returns:
            Result of the step execution
        """
        # Check if step exists
        if step_id not in self.steps:
            return Result.failure(f"Step {step_id} not found")
        
        # Get the step
        step = self.steps[step_id]
        
        # Capture a screenshot
        screenshot_result = self.get_screenshot()
        if not screenshot_result.success:
            return Result.failure(f"Step execution failed: {screenshot_result.error}")
        
        # Execute the step
        result = step.execute(self.context, screenshot_result.data)
        
        # Store the result in the context
        self.context.add_step_result(step_id, result)
        
        return result
    
    def execute_steps(self, step_ids: List[StepId], 
                      stop_on_failure: bool = True) -> Dict[StepId, Result]:
        """Execute a sequence of automation steps.
        
        Args:
            step_ids: IDs of the steps to execute in order
            stop_on_failure: Whether to stop execution if a step fails
            
        Returns:
            Dictionary of step IDs to results
        """
        results = {}
        
        for step_id in step_ids:
            result = self.execute_step(step_id)
            results[step_id] = result
            
            if not result.success and stop_on_failure:
                break
        
        return results
    
    def wait_for_state(self, 
                       states: List[StateType], 
                       timeout: float = 30.0,
                       check_interval: float = 1.0) -> Result[StateType]:
        """Wait for the screen to enter one of the specified states.
        
        Args:
            states: The states to wait for
            timeout: Maximum time to wait in seconds
            check_interval: Interval between state checks in seconds
            
        Returns:
            Result containing the detected state or error
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Detect the current state
            state_result = self.detect_state()
            
            if not state_result.success:
                return Result.failure(f"Wait for state failed: {state_result.error}")
            
            # Check if the detected state is one of the target states
            if state_result.data in states:
                return Result.success(state_result.data)
            
            # Wait before next check
            time.sleep(check_interval)
        
        # If we get here, we've timed out
        current_state = self.context.current_state
        return Result.failure(f"Timed out waiting for states {states}. Current state: {current_state}")
    
    def reset_context(self) -> None:
        """Reset the automation context to its initial state."""
        self.context = AutomationContext()
    
    def run_workflow(self, workflow: List[StepId]) -> Dict[StepId, Result]:
        """Run a complete automation workflow.
        
        A workflow is a sequence of steps to execute in order.
        
        Args:
            workflow: The sequence of step IDs to execute
            
        Returns:
            Dictionary of step IDs to results
        """
        # Reset the context for a fresh workflow
        self.reset_context()
        
        # Execute the workflow steps
        return self.execute_steps(workflow)
        
    def refresh_screen(self) -> Result[Image.Image]:
        """Refresh the screen and return a new screenshot.
        
        This method captures a new screenshot and updates the current state
        in the context.
        
        Returns:
            Result containing the new screenshot or error
        """
        # Capture a new screenshot
        screenshot_result = self.get_screenshot()
        if not screenshot_result.success:
            return screenshot_result
            
        # Update the current state
        state_result = self.state_detector.detect_state(screenshot_result.data)
        if state_result.success:
            self.context.current_state = state_result.data
            
        return screenshot_result 

"""
Automation step classes for the automation framework.

This module provides classes for defining automation steps, which are the building
blocks of automation workflows.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Tuple, Any

from PIL import Image

from .collectors import DataCollector
from .conditions import AutomationCondition
from .context import AutomationContext, Result
from .elements import UIElement
from .enums import StepId


class AutomationStep(ABC):
    """Base class for all automation steps.

    An automation step represents a discrete action or operation in an
    automation workflow, such as clicking a button or collecting data.
    """

    def __init__(self, step_id: StepId, name: Optional[str] = None):
        """Initialize an automation step.

        Args:
            step_id: Unique identifier for this step
            name: Human-readable name for this step
        """
        self.step_id = step_id
        self.name = name or f"Step {step_id}"

    @abstractmethod
    def execute(self, context: AutomationContext, screenshot: Image.Image) -> Result:
        """Execute this automation step.

        Args:
            context: The current automation context
            screenshot: The current screenshot

        Returns:
            Result of the step execution
        """
        pass


class InteractionStep(AutomationStep):
    """Step for interacting with UI elements.

    This step performs interactions such as clicking on UI elements.
    """

    def __init__(self,
                 step_id: StepId,
                 element: UIElement,
                 name: Optional[str] = None,
                 pre_conditions: Optional[List[AutomationCondition]] = None,
                 post_conditions: Optional[List[AutomationCondition]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """Initialize an interaction step.

        Args:
            step_id: Unique identifier for this step
            element: The UI element to interact with
            name: Human-readable name for this step
            pre_conditions: Conditions that must be met before execution
            post_conditions: Conditions that must be met after execution
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        super().__init__(step_id, name)
        self.element = element
        self.pre_conditions = pre_conditions or []
        self.post_conditions = post_conditions or []
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute(self, context: AutomationContext, screenshot: Image.Image) -> Result:
        """Execute the interaction step.

        Args:
            context: The current automation context
            screenshot: The current screenshot

        Returns:
            Result of the step execution
        """
        import time

        # Check pre-conditions
        for condition in self.pre_conditions:
            result = condition.check(context, screenshot)
            if not result.success or not result.data:
                return Result.failure(f"Pre-condition failed: {result.error or 'Condition not met'}")

        # Try to interact with the element
        retries = 0
        while retries <= self.max_retries:
            # Check if element is visible
            visibility_result = self.element.is_visible(screenshot)
            if not visibility_result.success:
                return Result.failure(f"Failed to check element visibility: {visibility_result.error}")

            if not visibility_result.data:
                if retries == self.max_retries:
                    return Result.failure(f"Element not visible after {retries} retries")

                retries += 1
                time.sleep(self.retry_delay)
                continue

            # Element is visible, interact with it
            interaction_result = self.element.interact(screenshot)
            if not interaction_result.success:
                if retries == self.max_retries:
                    return Result.failure(f"Interaction failed after {retries} retries: {interaction_result.error}")

                retries += 1
                time.sleep(self.retry_delay)
                continue

            # Interaction successful, check post-conditions
            time.sleep(0.5)  # Give time for UI to update after interaction
            new_screenshot = None  # Would be captured by the controller

            for condition in self.post_conditions:
                result = condition.check(context, new_screenshot or screenshot)
                if not result.success or not result.data:
                    if retries == self.max_retries:
                        return Result.failure(
                            f"Post-condition failed after {retries} retries: {result.error or 'Condition not met'}")

                    retries += 1
                    time.sleep(self.retry_delay)
                    continue

            # All post-conditions met, step successful
            return Result.success(True)

        # If we get here, we've exceeded max retries
        return Result.failure(f"Step failed after {self.max_retries} retries")


class WaitStep(AutomationStep):
    """Step for waiting for conditions to be met.

    This step waits for specified conditions to be met before proceeding.
    """

    def __init__(self,
                 step_id: StepId,
                 conditions: List[AutomationCondition],
                 name: Optional[str] = None,
                 timeout: float = 30.0,
                 check_interval: float = 1.0,
                 all_required: bool = True):
        """Initialize a wait step.

        Args:
            step_id: Unique identifier for this step
            conditions: Conditions to wait for
            name: Human-readable name for this step
            timeout: Maximum time to wait in seconds
            check_interval: Interval between condition checks in seconds
            all_required: Whether all conditions must be met (AND) or just one (OR)
        """
        super().__init__(step_id, name)
        self.conditions = conditions
        self.timeout = timeout
        self.check_interval = check_interval
        self.all_required = all_required

    def execute(self, context: AutomationContext, screenshot: Image.Image) -> Result:
        """Execute the wait step.

        Args:
            context: The current automation context
            screenshot: The current screenshot

        Returns:
            Result of the step execution
        """
        import time

        start_time = time.time()
        elapsed = 0

        errors = []
        while elapsed < self.timeout:
            # Check each condition
            all_met = True
            any_met = False

            for condition in self.conditions:
                result = condition.check(context, screenshot)

                if not result.success:
                    errors.append(f"Error checking condition: {result.error}")
                    all_met = False
                    continue

                if result.data:
                    any_met = True
                else:
                    all_met = False

            # Check if conditions are met based on logic
            if (self.all_required and all_met) or (not self.all_required and any_met):
                return Result.success(True)

            # Not met, check if we've timed out
            elapsed = time.time() - start_time
            if elapsed >= self.timeout:
                break

            # Wait before next check
            time.sleep(min(self.check_interval, self.timeout - elapsed))

            # Would get a new screenshot from controller here
            # screenshot = controller.get_screenshot()

        # If we get here, we've timed out
        if errors:
            return Result.failure(f"Wait timed out with errors: {'; '.join(errors)}")

        return Result.failure(f"Wait timed out after {self.timeout} seconds")


class CollectionStep(AutomationStep):
    """Step for collecting data from the screen.

    This step uses data collectors to extract information from the screen.
    """

    def __init__(self,
                 step_id: StepId,
                 collectors: Dict[str, DataCollector],
                 name: Optional[str] = None,
                 pre_conditions: Optional[List[AutomationCondition]] = None):
        """Initialize a collection step.

        Args:
            step_id: Unique identifier for this step
            collectors: Data collectors to use, with keys for storing results
            name: Human-readable name for this step
            pre_conditions: Conditions that must be met before collection
        """
        super().__init__(step_id, name)
        self.collectors = collectors
        self.pre_conditions = pre_conditions or []

    def execute(self, context: AutomationContext, screenshot: Image.Image) -> Result[Dict[str, Any]]:
        """Execute the collection step.

        Args:
            context: The current automation context
            screenshot: The current screenshot

        Returns:
            Result containing collected data or error
        """

        # Check pre-conditions
        for condition in self.pre_conditions:
            result = condition.check(context, screenshot)
            if not result.success or not result.data:
                return Result.failure(f"Pre-condition failed: {result.error or 'Condition not met'}")

        # Collect data using each collector
        collected_data = {}
        errors = []

        for key, collector in self.collectors.items():
            result = collector.collect(screenshot)

            if result.success:
                collected_data[key] = result.data
            else:
                errors.append(f"Collection failed for '{key}': {result.error}")

        # Return results
        if errors:
            return Result.failure(f"Collection errors: {'; '.join(errors)}")

        return Result.success(collected_data)


class ConditionalStep(AutomationStep):
    """Step that executes different steps based on conditions.

    This step checks conditions and executes different steps based on which
    conditions are met.
    """

    def __init__(self,
                 step_id: StepId,
                 condition_steps: List[Tuple[AutomationCondition, AutomationStep]],
                 default_step: Optional[AutomationStep] = None,
                 name: Optional[str] = None):
        """Initialize a conditional step.

        Args:
            step_id: Unique identifier for this step
            condition_steps: Pairs of conditions and steps to execute if met
            default_step: Step to execute if no conditions are met
            name: Human-readable name for this step
        """
        super().__init__(step_id, name)
        self.condition_steps = condition_steps
        self.default_step = default_step

    def execute(self, context: AutomationContext, screenshot: Image.Image) -> Result:
        """Execute the conditional step.

        Args:
            context: The current automation context
            screenshot: The current screenshot

        Returns:
            Result of the executed sub-step
        """
        # Check each condition
        for condition, step in self.condition_steps:
            result = condition.check(context, screenshot)

            if result.success and result.data:
                # Condition met, execute corresponding step
                return step.execute(context, screenshot)

        # No conditions met, execute default step if provided
        if self.default_step:
            return self.default_step.execute(context, screenshot)

        # No default step, return success
        return Result.success(None)


class LoopStep(AutomationStep):
    """Step for looping through a series of similar actions.

    This step allows repeating similar steps with different parameters
    for each iteration, such as clicking different positions in sequence.
    """

    def __init__(self,
                 step_id: StepId,
                 iteration_factory: Callable[[int, AutomationContext], AutomationStep],
                 max_iterations: int = 0,
                 continue_condition: Optional[AutomationCondition] = None,
                 name: Optional[str] = None):
        """Initialize a loop step.

        Args:
            step_id: Unique identifier for this step
            iteration_factory: Function that creates the step for each iteration
                               Takes iteration index and context as parameters
            max_iterations: Maximum number of iterations (0 for unlimited)
            continue_condition: Condition to check if loop should continue
                               If None, only max_iterations will control the loop
            name: Human-readable name for this step
        """
        super().__init__(step_id, name)
        self.iteration_factory = iteration_factory
        self.max_iterations = max_iterations
        self.continue_condition = continue_condition

    def execute(self, context: AutomationContext, screenshot: Image.Image) -> Result:
        """Execute the loop step.

        Args:
            context: The current automation context
            screenshot: The current screenshot

        Returns:
            Result of the step execution
        """
        iteration = 0
        results = []
        errors = []

        # Add loop index to context
        context.add_data("loop_iteration", iteration)

        # Loop until max_iterations reached or continue_condition fails
        while self.max_iterations == 0 or iteration < self.max_iterations:
            # Check continue condition if provided
            if self.continue_condition and iteration > 0:
                condition_result = self.continue_condition.check(context, screenshot)

                if not condition_result.success:
                    errors.append(f"Continue condition check failed: {condition_result.error}")
                    break

                if not condition_result.data:
                    # Condition indicates loop should stop
                    break

            # Create step for this iteration
            iteration_step = self.iteration_factory(iteration, context)

            # Execute the step
            result = iteration_step.execute(context, screenshot)
            results.append(result)

            # Store result in context
            context.add_data(f"loop_result_{iteration}", result)

            if not result.success:
                errors.append(f"Iteration {iteration} failed: {result.error}")
                break

            # Update iteration counter
            iteration += 1
            context.add_data("loop_iteration", iteration)

            # Get a fresh screenshot for the next iteration
            # In a real implementation, this would come from the controller
            screenshot_result = context.get_screenshot()
            if screenshot_result.success:
                screenshot = screenshot_result.data

        # Store final results
        context.add_data("loop_iterations_completed", iteration)
        context.add_data("loop_results", results)

        # Return success if all iterations completed successfully
        if not errors:
            return Result.success(results)

        return Result.failure(f"Loop errors: {'; '.join(errors)}")

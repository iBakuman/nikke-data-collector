"""
Context and result classes for the automation framework.

These classes provide type-safe containers for passing data and tracking
results throughout the automation process.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from PIL import Image

from .enums import StateType, StepId

T = TypeVar('T')  # Generic type for result data


@dataclass
class Result(Generic[T]):
    """Type-safe container for operation results.
    
    Attributes:
        success: Whether the operation succeeded
        data: The result data (if successful)
        error: Error message (if failed)
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    
    @classmethod
    def success(cls, data: T) -> 'Result[T]':
        """Create a successful result with data.
        
        Args:
            data: The result data
            
        Returns:
            A successful Result object
        """
        return cls(success=True, data=data)
    
    @classmethod
    def failure(cls, error: str) -> 'Result[T]':
        """Create a failed result with error message.
        
        Args:
            error: The error message
            
        Returns:
            A failed Result object
        """
        return cls(success=False, error=error)


@dataclass
class AutomationContext:
    """Context object for the automation process.
    
    This class holds state and data during automation workflow execution,
    providing a type-safe way to share information between steps.
    
    Attributes:
        current_state: The current detected screen state
        captured_images: Images captured during automation
        collected_data: Data collected during automation
        state_data: State-specific data
        step_results: Results of executed steps
    """
    current_state: Optional[StateType] = None
    captured_images: Dict[str, Image.Image] = field(default_factory=dict)
    collected_data: Dict[Enum, Any] = field(default_factory=dict)
    state_data: Dict[StateType, Dict[str, Any]] = field(default_factory=dict)
    step_results: Dict[StepId, Result[Any]] = field(default_factory=dict)
    
    def add_image(self, key: str, image: Image.Image) -> None:
        """Add a captured image to the context.
        
        Args:
            key: Unique identifier for the image
            image: The captured image
        """
        self.captured_images[key] = image
    
    def add_data(self, key: Enum, data: Any) -> None:
        """Add collected data to the context.
        
        Args:
            key: Unique identifier for the data (enum)
            data: The collected data
        """
        self.collected_data[key] = data
    
    def get_data(self, key: Enum) -> Optional[Any]:
        """Get collected data from the context.
        
        Args:
            key: Unique identifier for the data (enum)
            
        Returns:
            The collected data or None if not found
        """
        return self.collected_data.get(key)
    
    def add_step_result(self, step_id: StepId, result: Result[Any]) -> None:
        """Add a step execution result.
        
        Args:
            step_id: ID of the executed step
            result: Result of the step execution
        """
        self.step_results[step_id] = result
    
    def get_step_result(self, step_id: StepId) -> Optional[Result[Any]]:
        """Get the result of a specific step.
        
        Args:
            step_id: ID of the step
            
        Returns:
            Result of the step or None if not found
        """
        return self.step_results.get(step_id)
    
    def add_state_data(self, state: StateType, key: str, value: Any) -> None:
        """Add data for a specific state.
        
        Args:
            state: The state the data belongs to
            key: Data key
            value: Data value
        """
        if state not in self.state_data:
            self.state_data[state] = {}
        self.state_data[state][key] = value
    
    def get_state_data(self, state: StateType, key: str) -> Optional[Any]:
        """Get data for a specific state.
        
        Args:
            state: The state the data belongs to
            key: Data key
            
        Returns:
            The data value or None if not found
        """
        return self.state_data.get(state, {}).get(key) 

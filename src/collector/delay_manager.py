"""
Delay Manager

This module provides a centralized way to manage delays in automation scripts.
It supports configurable delay ranges and randomization to make automation
appear more natural and less detectable.
"""
import random
import time
from typing import Tuple


class DelayManager:
    """
    Manages application-wide delay settings with randomization capabilities.
    
    This class centralizes all delay operations to ensure consistent timing
    throughout the application. It provides methods to adjust delay ranges
    and generate random delays within specified bounds.
    """

    def __init__(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """
        Initialize the delay manager with default or custom delay range.
        
        Args:
            min_delay: Minimum delay in seconds (default: 0.5)
            max_delay: Maximum delay in seconds (default: 2.0)
        """
        self._min_delay = min_delay
        self._max_delay = max_delay

    @property
    def delay_range(self) -> Tuple[float, float]:
        """Get the current delay range (min, max)."""
        return self._min_delay, self._max_delay

    def set_delay_range(self, min_delay: float, max_delay: float) -> None:
        """
        Set a new delay range.
        
        Args:
            min_delay: New minimum delay in seconds
            max_delay: New maximum delay in seconds
            
        Raises:
            ValueError: If min_delay is negative or max_delay < min_delay
        """
        if min_delay < 0:
            raise ValueError("Minimum delay cannot be negative")
        if max_delay < min_delay:
            raise ValueError("Maximum delay must be greater than or equal to minimum delay")

        self._min_delay = min_delay
        self._max_delay = max_delay

    def get_random_delay(self) -> float:
        """
        Generate a random delay within the configured range.
        
        Returns:
            A random float between min_delay and max_delay
        """
        return random.uniform(self._min_delay, self._max_delay)

    def sleep(self) -> float:
        """
        Sleep for a random duration within the configured range.
        
        Returns:
            The actual sleep duration in seconds
        """
        delay = self.get_random_delay()
        time.sleep(delay)
        return delay

    def sleep_with_factor(self, factor: float = 1.0) -> float:
        """
        Sleep for a random duration multiplied by a factor.
        Useful for operations that need proportionally longer/shorter delays.
        
        Args:
            factor: Multiplier for the delay (default: 1.0)
            
        Returns:
            The actual sleep duration in seconds
        """
        delay = self.get_random_delay() * factor
        time.sleep(delay)
        return delay

"""
Screen regions module for the NIKKE data collection system.

This module provides classes for defining, managing, and interacting with 
screen regions - rectangular areas of the screen used for capturing, analyzing,
and detecting UI elements.
"""

from typing import (Callable, Dict, Optional, Protocol,
                    Tuple)

import numpy as np
from PIL import Image

from src.processor.enums import RegionKey

# Type definitions
Bounds = Tuple[int, int, int, int]  # left, top, right, bottom
Point = Tuple[int, int]  # x, y


class ScreenCaptureProvider(Protocol):
    """Protocol for providing screen captures."""

    def get_screenshot(self) -> Image.Image:
        """
        Get a screenshot of the current screen.
        
        Returns:
            Image.Image: The screenshot as a PIL Image.
        """
        ...


class Region:
    """
    Base class for screen regions.
    
    A region represents a rectangular area of the screen that can be captured,
    analyzed, and used for detecting UI elements.
    """

    def __init__(self, name: str = ""):
        """
        Initialize a Region.
        
        Args:
            name: A descriptive name for the region
        """
        self.name = name

    def get_bounds(self) -> Bounds:
        """
        Get the bounds of the region.
        
        Returns:
            Bounds: (left, top, right, bottom) coordinates
        """
        raise NotImplementedError("Subclasses must implement get_bounds()")

    def capture(self, provider: ScreenCaptureProvider) -> Image.Image:
        """
        Capture the region from the screen.
        
        Args:
            provider: Object that provides screen captures
            
        Returns:
            Image.Image: The captured region as a PIL Image
        """
        bounds = self.get_bounds()
        screenshot = provider.get_screenshot()
        return screenshot.crop(bounds)

    def capture_to_array(self, provider: ScreenCaptureProvider) -> np.ndarray:
        """
        Capture the region and convert to numpy array.
        
        Args:
            provider: Object that provides screen captures
            
        Returns:
            np.ndarray: The captured region as a numpy array
        """
        img = self.capture(provider)
        return np.array(img)

    def contains_point(self, point: Point) -> bool:
        """
        Check if the region contains the given point.
        
        Args:
            point: (x, y) coordinates to check
            
        Returns:
            bool: True if the point is within this region
        """
        left, top, right, bottom = self.get_bounds()
        x, y = point
        return (left <= x <= right) and (top <= y <= bottom)

    def relative_to_absolute(self, rel_x: float, rel_y: float) -> Point:
        """
        Convert relative coordinates within the region to absolute screen coordinates.
        
        Args:
            rel_x: Relative x coordinate (0.0 to 1.0)
            rel_y: Relative y coordinate (0.0 to 1.0)
            
        Returns:
            Point: Absolute (x, y) coordinates
        """
        left, top, right, bottom = self.get_bounds()
        width = right - left
        height = bottom - top

        abs_x = left + int(width * rel_x)
        abs_y = top + int(height * rel_y)

        return abs_x, abs_y

    def absolute_to_relative(self, abs_x: int, abs_y: int) -> Tuple[float, float]:
        """
        Convert absolute screen coordinates to relative coordinates within the region.
        
        Args:
            abs_x: Absolute x coordinate
            abs_y: Absolute y coordinate
            
        Returns:
            Tuple[float, float]: Relative (x, y) coordinates (0.0 to 1.0)
        """
        left, top, right, bottom = self.get_bounds()
        width = right - left
        height = bottom - top

        if width == 0 or height == 0:
            return 0.0, 0.0

        rel_x = (abs_x - left) / width
        rel_y = (abs_y - top) / height

        return rel_x, rel_y

    def __repr__(self) -> str:
        """String representation of the region."""
        bounds = self.get_bounds()
        return f"{self.__class__.__name__}(name='{self.name}', bounds={bounds})"


class FixedRegion(Region):
    """
    A region with fixed bounds.
    
    These bounds are defined by absolute pixel coordinates and don't change
    regardless of screen size or resolution.
    """

    def __init__(self, left: int, top: int, right: int, bottom: int, name: str = ""):
        """
        Initialize a FixedRegion with absolute coordinates.
        
        Args:
            left: Left coordinate
            top: Top coordinate
            right: Right coordinate
            bottom: Bottom coordinate
            name: A descriptive name for the region
        """
        super().__init__(name)
        self._bounds = (left, top, right, bottom)

    def get_bounds(self) -> Bounds:
        """
        Get the fixed bounds of the region.
        
        Returns:
            Bounds: (left, top, right, bottom) coordinates
        """
        return self._bounds

    def update_bounds(self, left: int, top: int, right: int, bottom: int) -> None:
        """
        Update the fixed bounds of the region.
        
        Args:
            left: New left coordinate
            top: New top coordinate
            right: New right coordinate
            bottom: New bottom coordinate
        """
        self._bounds = (left, top, right, bottom)


class RelativeRegion(Region):
    """
    A region with bounds defined relative to the screen size.
    
    The bounds are specified as percentages (0.0 to 1.0) of the screen dimensions.
    This allows the region to adapt to different screen sizes and resolutions.
    """

    def __init__(
            self,
            rel_left: float,
            rel_top: float,
            rel_right: float,
            rel_bottom: float,
            screen_width: int,
            screen_height: int,
            name: str = ""
    ):
        """
        Initialize a RelativeRegion with relative coordinates.
        
        Args:
            rel_left: Left coordinate as a fraction of screen width (0.0 to 1.0)
            rel_top: Top coordinate as a fraction of screen height (0.0 to 1.0)
            rel_right: Right coordinate as a fraction of screen width (0.0 to 1.0)
            rel_bottom: Bottom coordinate as a fraction of screen height (0.0 to 1.0)
            screen_width: The width of the screen in pixels
            screen_height: The height of the screen in pixels
            name: A descriptive name for the region
        """
        super().__init__(name)
        self.rel_left = rel_left
        self.rel_top = rel_top
        self.rel_right = rel_right
        self.rel_bottom = rel_bottom
        self.screen_width = screen_width
        self.screen_height = screen_height

    def get_bounds(self) -> Bounds:
        """
        Calculate the absolute bounds based on relative coordinates.
        
        Returns:
            Bounds: (left, top, right, bottom) absolute coordinates
        """
        left = int(self.rel_left * self.screen_width)
        top = int(self.rel_top * self.screen_height)
        right = int(self.rel_right * self.screen_width)
        bottom = int(self.rel_bottom * self.screen_height)

        return left, top, right, bottom

    def update_screen_size(self, screen_width: int, screen_height: int) -> None:
        """
        Update the screen dimensions used for calculating absolute bounds.
        
        Args:
            screen_width: The new width of the screen in pixels
            screen_height: The new height of the screen in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height


class DynamicRegion(Region):
    """
    A region with bounds determined dynamically at runtime.
    
    The bounds are calculated by a provided function, which allows for complex
    logic to determine the region's position and size.
    """

    def __init__(
            self,
            bounds_function: Callable[[], Bounds],
            name: str = ""
    ):
        """
        Initialize a DynamicRegion with a function to calculate bounds.
        
        Args:
            bounds_function: A function that returns (left, top, right, bottom)
            name: A descriptive name for the region
        """
        super().__init__(name)
        self.bounds_function = bounds_function

    def get_bounds(self) -> Bounds:
        """
        Calculate the bounds using the provided function.
        
        Returns:
            Bounds: (left, top, right, bottom) coordinates
        """
        return self.bounds_function()

    def update_bounds_function(self, bounds_function: Callable[[], Bounds]) -> None:
        """
        Update the function used to calculate bounds.
        
        Args:
            bounds_function: A new function that returns (left, top, right, bottom)
        """
        self.bounds_function = bounds_function


class RegionManager:
    """
    Manages a collection of screen regions.
    
    This class provides methods for registering, retrieving, and capturing
    regions by their keys.
    """

    def __init__(self):
        """Initialize an empty region manager."""
        self.regions: Dict[RegionKey, Region] = {}

    def register_region(self, key: RegionKey, region: Region) -> None:
        """
        Register a region with the specified key.
        
        Args:
            key: The unique key for the region
            region: The region to register
        """
        self.regions[key] = region

    def get_region(self, key: RegionKey) -> Optional[Region]:
        """
        Get a region by its key.
        
        Args:
            key: The key of the region to retrieve
            
        Returns:
            Optional[Region]: The region or None if not found
        """
        return self.regions.get(key)

    def capture_region(
            self,
            key: RegionKey,
            provider: ScreenCaptureProvider
    ) -> Optional[Image.Image]:
        """
        Capture a specific region by its key.
        
        Args:
            key: The key of the region to capture
            provider: Object that provides screen captures
            
        Returns:
            Optional[Image.Image]: The captured region or None if the region wasn't found
        """
        region = self.get_region(key)
        if region:
            return region.capture(provider)
        return None

    def capture_all_regions(
            self,
            provider: ScreenCaptureProvider
    ) -> Dict[RegionKey, Image.Image]:
        """
        Capture all registered regions.
        
        Args:
            provider: Object that provides screen captures
            
        Returns:
            Dict[RegionKey, Image.Image]: A dictionary of captured regions
        """
        result = {}
        for key, region in self.regions.items():
            result[key] = region.capture(provider)
        return result

    def get_all_regions(self) -> Dict[RegionKey, Region]:
        """
        Get all registered regions.
        
        Returns:
            Dict[RegionKey, Region]: A dictionary of all registered regions
        """
        return self.regions.copy()


def setup_default_regions(screen_width: int, screen_height: int) -> RegionManager:
    """
    Set up a RegionManager with default regions based on screen dimensions.
    
    Args:
        screen_width: The width of the screen in pixels
        screen_height: The height of the screen in pixels
        
    Returns:
        RegionManager: A manager configured with default regions
    """
    manager = RegionManager()

    # Register full screen region
    full_screen = FixedRegion(0, 0, screen_width, screen_height, "Full Screen")
    manager.register_region(RegionKey.FULL_SCREEN, full_screen)

    # Register header region (top 10% of screen)
    header = RelativeRegion(0.0, 0.0, 1.0, 0.1, screen_width, screen_height, "Header")
    manager.register_region(RegionKey.HEADER, header)

    # Register footer region (bottom 10% of screen)
    footer = RelativeRegion(0.0, 0.9, 1.0, 1.0, screen_width, screen_height, "Footer")
    manager.register_region(RegionKey.FOOTER, footer)

    # Register main content region (middle 80% of screen)
    content = RelativeRegion(0.0, 0.1, 1.0, 0.9, screen_width, screen_height, "Main Content")
    manager.register_region(RegionKey.MAIN_CONTENT, content)

    # Register side menu region (left 20% of screen)
    side_menu = RelativeRegion(0.0, 0.1, 0.2, 0.9, screen_width, screen_height, "Side Menu")
    manager.register_region(RegionKey.SIDE_MENU, side_menu)

    return manager

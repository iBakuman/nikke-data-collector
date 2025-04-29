from dataclasses import dataclass
from typing import Tuple

@dataclass
class Region:
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int

class WindowInfo:
    """Class to hold window information including position, size and scale ratio."""

    def __init__(self, hwnd: int, rect: Region, standard_width: int, standard_height: int):
        self.hwnd = hwnd
        self.rect = rect
        self.left, self.top, self.right, self.bottom = rect.left, rect.top, rect.right, rect.bottom
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        self.width_ratio = self.width / standard_width
        self.height_ratio = self.height / standard_height

    def get_scaled_position(self, standard_x: int, standard_y: int) -> Tuple[int, int]:
        """
        Convert a position from standard coordinates to the current window scale

        Args:
            standard_x (int): X coordinate in standard window size (3580x2014)
            standard_y (int): Y coordinate in standard window size (3580x2014)

        Returns:
            Tuple[int, int]: Scaled (x, y) coordinates for the current window
        """
        scaled_x = int(standard_x * self.width_ratio)
        scaled_y = int(standard_y * self.height_ratio)
        return scaled_x, scaled_y

    def get_absolute_position(self, standard_x: int, standard_y: int) -> Tuple[int, int]:
        """
        Convert standard coordinates to absolute screen coordinates

        Args:
            standard_x (int): X coordinate in standard window size (3580x2014)
            standard_y (int): Y coordinate in standard window size (3580x2014)

        Returns:
            Tuple[int, int]: Absolute screen (x, y) coordinates
        """
        scaled_x, scaled_y = self.get_scaled_position(standard_x, standard_y)
        abs_x = self.left + scaled_x
        abs_y = self.top + scaled_y
        return abs_x, abs_y

    def __str__(self) -> str:
        return (f"Window: {self.left},{self.top} - {self.right},{self.bottom} "
                f"(Size: {self.width}x{self.height}) "
                f"Scale: {self.width_ratio:.4f}x{self.height_ratio:.4f}")


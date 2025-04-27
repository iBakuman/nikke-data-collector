"""
UI Element Detection Module for NIKKE data collection system.

This module provides classes for detecting and interacting with UI elements
in the game. It supports multiple detection methods including:
- Template matching (for image-based elements)
- Pixel color checking (for color-based indicators)
- OCR text detection (for text-based elements)

Each element can be detected, clicked, and its state can be queried.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from .enums import ElementType
from .regions import Region

# Type definitions
Point = Tuple[int, int]  # x, y
Color = Tuple[int, int, int]  # BGR color tuple


@dataclass
class DetectionResult:
    """Result of a UI element detection attempt."""

    found: bool
    bounds: Optional[Region] = None
    confidence: float = 0.0
    text: Optional[str] = None

    @property
    def center(self) -> Optional[Point]:
        """Get the center point of the detected element."""
        if not self.bounds:
            return None
        x, y, w, h = self.bounds
        return x + w // 2, y + h // 2


class UIElement(ABC):
    """Base class for all UI elements."""

    def __init__(
            self,
            name: str,
            region: Optional[Region] = None,
    ):
        """Initialize a UI element.

        Args:
            name: Unique name for the element
            region: Optional region to restrict detection
        """
        self.name = name
        self.region = region
        self.logger = logging.getLogger(f"UIElement.{name}")

    @abstractmethod
    def detect(self, screenshot: Image.Image) -> DetectionResult:
        """Detect this element in the given screenshot.

        Args:
            screenshot: BGR image of the game window

        Returns:
            DetectionResult: Detection result with bounds if found
        """
        pass

    def is_visible(self, screenshot: Image.Image) -> bool:
        """Check if this element is visible in the screenshot.

        Args:
            screenshot: BGR image of the game window

        Returns:
            bool: True if the element is visible
        """
        result = self.detect(screenshot)
        return result.found

    def get_region_from_screenshot(self, screenshot: Image.Image) -> Image.Image:
        """Extract the region of interest from the screenshot.

        Args:
            screenshot: BGR image of the game window

        Returns:
            np.ndarray: Region of interest from the screenshot
        """
        if self.region:
            x, y, w, h = self.region
            return screenshot.crop((x, y, x + w, y + h))
        return screenshot


@dataclass
class ImageRegion():
    name: str
    enclosing_region: Region
    image: Image.Image


class ImageElement(UIElement):
    """UI element detected by template matching."""

    def __init__(
            self,
            name: str,
            template_path: Union[str, Path],
            threshold: float = 0.8,
            region: Optional[Region] = None,
    ):
        """Initialize an image element.

        Args:
            name: Unique name for the element
            template_path: Path to the template image
            threshold: Confidence threshold for detection (0.0-1.0)
            region: Optional region to restrict detection
            method: OpenCV template matching method
        """
        super().__init__(name, region)
        self.template_path = Path(template_path)
        self.threshold = threshold
        self._template: Optional[np.ndarray] = None

    @property
    def template(self) -> Image.Image:
        """Load the template image lazily."""
        if self._template is None:
            if not self.template_path.exists():
                self.logger.error(f"Template image not found: {self.template_path}")
                raise FileNotFoundError(f"Template image not found: {self.template_path}")

            self._template = cv2.imread(str(self.template_path))
            if self._template is None:
                self.logger.error(f"Failed to load template image: {self.template_path}")
                raise ValueError(f"Failed to load template image: {self.template_path}")

        return self._template

    def detect(self, screenshot: Image.Image) -> DetectionResult:
        """Detect this element in the given screenshot using template matching.

        Args:
            screenshot: BGR image of the game window

        Returns:
            DetectionResult: Detection result with bounds if found
        """
        try:
            region_img = self.get_region_from_screenshot(screenshot)
            template = self.template

            # Check if template is larger than the region
            if (template.shape[1] > region_img.shape[1] or
                    template.shape[0] > region_img.shape[0]):
                return DetectionResult(found=False)

            # Perform template matching
            result = cv2.matchTemplate(region_img, template, self.method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # Different methods use different values
            if self.method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                confidence = 1 - min_val
                loc = min_loc
            else:
                confidence = max_val
                loc = max_loc

            if confidence >= self.threshold:
                x, y = loc
                w, h = template.shape[1], template.shape[0]

                # Adjust coordinates if using region
                if self.region:
                    x += self.region[0]
                    y += self.region[1]

                return DetectionResult(
                    found=True,
                    bounds=(x, y, w, h),
                    confidence=confidence
                )

            return DetectionResult(found=False, confidence=confidence)

        except Exception as e:
            self.logger.error(f"Error detecting image element: {e}")
            return DetectionResult(found=False)


class PixelColorElement(UIElement):
    """UI element detected by checking pixel colors."""

    def __init__(
            self,
            name: str,
            points_colors: List[Tuple[Point, Color]],
            tolerance: int = 10,
            region: Optional[Region] = None,
            match_all: bool = True,
    ):
        """Initialize a pixel color element.

        Args:
            name: Unique name for the element
            points_colors: List of (point, color) tuples to check
            tolerance: Color matching tolerance (0-255)
            region: Optional region to restrict detection
            match_all: If True, all points must match; otherwise, any match succeeds
        """
        super().__init__(name, region)
        self.points_colors = points_colors
        self.tolerance = tolerance
        self.match_all = match_all

    def detect(self, screenshot: Image.Image) -> DetectionResult:
        """Detect this element by checking pixel colors in the screenshot.

        Args:
            screenshot: BGR image of the game window

        Returns:
            DetectionResult: Detection result
        """
        try:
            # Calculate bounds from points
            if not self.points_colors:
                return DetectionResult(found=False)

            points = [p for p, _ in self.points_colors]
            min_x = min(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_x = max(p[0] for p in points)
            max_y = max(p[1] for p in points)
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            bounds = (min_x, min_y, width, height)

            matches = 0
            for point, expected_color in self.points_colors:
                x, y = point

                # Check if point is within the screenshot bounds
                if (y >= screenshot.shape[0] or x >= screenshot.shape[1] or
                        x < 0 or y < 0):
                    if self.match_all:
                        return DetectionResult(found=False)
                    continue

                actual_color = screenshot[y, x]

                # Check if the colors match within tolerance
                if all(abs(int(a) - int(e)) <= self.tolerance for a, e in zip(actual_color, expected_color)):
                    matches += 1
                    if not self.match_all:
                        return DetectionResult(found=True, bounds=bounds)
                elif self.match_all:
                    return DetectionResult(found=False)

            return DetectionResult(
                found=matches == len(self.points_colors),
                bounds=bounds if matches == len(self.points_colors) else None
            )

        except Exception as e:
            self.logger.error(f"Error detecting pixel color element: {e}")
            return DetectionResult(found=False)


class TextElement(UIElement):
    """UI element detected by OCR text recognition."""

    def __init__(
            self,
            name: str,
            text: str,
            region: Optional[Region] = None,
            case_sensitive: bool = False,
            exact_match: bool = False,
    ):
        """Initialize a text element.

        Args:
            name: Unique name for the element
            text: Text to search for
            region: Optional region to restrict detection
            case_sensitive: Whether text matching is case-sensitive
            exact_match: If True, the text must match exactly; otherwise, partial matches count
        """
        super().__init__(name, region)
        self.text = text
        self.case_sensitive = case_sensitive
        self.exact_match = exact_match

    def detect(self, screenshot: Image.Image) -> DetectionResult:
        """Detect this element by finding text in the screenshot using OCR.

        Args:
            screenshot: BGR image of the game window

        Returns:
            DetectionResult: Detection result with bounds if found
        """
        try:
            # This implementation requires a separate OCR module or service
            # For now, we'll just log a message and return a not found result
            self.logger.warning("TextElement detection requires OCR implementation")

            # Placeholder implementation - in a real system, this would use
            # Tesseract OCR, pytesseract, or another OCR library to find text
            # in the specified region of the screenshot

            # TODO: Implement OCR-based text detection

            return DetectionResult(found=False)

        except Exception as e:
            self.logger.error(f"Error detecting text element: {e}")
            return DetectionResult(found=False)

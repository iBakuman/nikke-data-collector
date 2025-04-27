"""
UI Element Detection Module for NIKKE data collection system.

This module provides classes for detecting and interacting with UI elements
in the game. It supports multiple detection methods including:
- Template matching (for image-based elements)
- Pixel color checking (for color-based indicators)
- OCR text detection (for text-based elements)

Each element can be detected, clicked, and its state can be queried.
"""
import io
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pyautogui
from PIL import Image

from domain.image_element import ImageElement
from log.config import get_logger
from .regions import Point, Region

logger = get_logger(__name__)

Color = Tuple[int, int, int]  # BGR color tuple


@dataclass
class DetectionResult:
    """Result of a UI element detection attempt."""

    found: bool
    region: Optional[Region] = None
    confidence: float = 0.0
    text: Optional[str] = None

    @property
    def center(self) -> Optional[Point]:
        """Get the center point of the detected element."""
        if not self.region:
            return None
        x, y, w, h = self.region
        return Point(x=x + w // 2, y=y + h // 2, total_width=self.region.total_width,
                     total_height=self.region.total_height)


class UIElement(ABC):
    """Base class for all UI elements."""

    def __init__(
            self,
            name: str,
    ):
        """Initialize a UI element.

        Args:
            name: Unique name for the element
        """
        self.name = name
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


class ImageElement(UIElement):
    """UI element detected by template matching."""

    def __init__(
            self,
            name: str,
            region: Region,
            target_image: Image.Image,
            debug_path: Optional[Path] = None,
            threshold: float = 0.8,
    ):
        """Initialize an image element.

        Args:
            name: Unique name for the element
            region: Optional region to restrict detection
            target_image: Image to detect
            threshold: Confidence threshold for detection (0.0-1.0)
        """
        super().__init__(name)
        self.region = region
        self.target_image = target_image
        self.threshold = threshold
        self._template: Optional[np.ndarray] = None
        self.debug_path = debug_path

    @classmethod
    def from_dto(cls, dto: ImageElement, debug_path: Optional[Path] = None) -> 'ImageElement':
        """Create an ImageElement from a DTO object.

        This factory method converts a database-sourced DTO into a fully functional
        ImageElement instance by loading the necessary resources.

        Args:
            dto: The ImageElement from the database
            debug_path: Optional path for debug images

        Returns:
            A new ImageElement instance

        Raises:
            ValueError: If the DTO contains invalid data
        """
        if not isinstance(dto, ImageElement):
            raise TypeError(f"Expected ImageElement, got {type(dto).__name__}")

        # Create Region from DTO fields
        region = Region(
            name=dto.name,
            start_x=dto.region_x,
            start_y=dto.region_y,
            width=dto.region_width,
            height=dto.region_height,
            total_width=dto.region_total_width,
            total_height=dto.region_total_height
        )

        # Load image from binary data
        if not dto.image_data:
            raise ValueError("Image data is empty in DTO")

        target_image = Image.open(io.BytesIO(dto.image_data))

        # Create and return new ImageElement
        return cls(
            name=dto.name,
            region=region,
            target_image=target_image,
            debug_path=debug_path,
            threshold=dto.threshold
        )

    def to_dto(self) -> ImageElement:
        """Convert this ImageElement to a DTO for database storage.

        Returns:
            An ImageElement representing this element
        """
        from domain.image_element import ImageElement
        img_byte_arr = io.BytesIO()
        self.target_image.save(img_byte_arr, format='PNG')
        image_data = img_byte_arr.getvalue()

        # Create DTO with region data and image binary data
        return ImageElement(
            name=self.name,
            region_x=self.region.start_x,
            region_y=self.region.start_y,
            region_width=self.region.width,
            region_height=self.region.height,
            region_total_width=self.region.total_width,
            region_total_height=self.region.total_height,
            image_data=image_data,
            threshold=self.threshold
        )

    def detect(self, screenshot: Image.Image) -> DetectionResult:
        target_image = self._scale_image(self.target_image, self.region, screenshot)

        if self.debug_path:
            target_image.save(os.path.join(self.debug_path, f"target_{self.name}.png"))

        # Use PIL Image with pyautogui
        location = pyautogui.locate(
            target_image,
            screenshot,
            confidence=self.threshold
        )

        if not location:
            self.logger.info(f"Image {self.target_image} not found in region")
            return DetectionResult(found=False)

        x, y, width, height = location
        return DetectionResult(found=True,
                               region=Region(name=self.name, start_x=x, start_y=y, width=width, height=height,
                                             total_width=screenshot.width, total_height=screenshot.height))

    @classmethod
    def _scale_image(cls, image: Image.Image, region: Region, screenshot: Image.Image) -> Image.Image:
        width_ratio = region.width / screenshot.width
        height_ratio = region.height / screenshot.height

        # Only scale if ratios are not 1.0
        if abs(width_ratio - 1.0) < 0.01 and abs(height_ratio - 1.0) < 0.01:
            return image

        original_width, original_height = image.size
        new_width = int(original_width * width_ratio)
        new_height = int(original_height * height_ratio)

        # Don't scale if too small
        if new_width < 5 or new_height < 5:
            logger.warning(f"Scaled image would be too small: {new_width}x{new_height}, using original")
            return image

        # Resize image using LANCZOS for best quality
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


class PixelColorElement(UIElement):
    """UI element detected by checking pixel colors."""

    def __init__(
            self,
            name: str,
            points_colors: List[Tuple[Point, Color]],
            tolerance: int = 10,
            match_all: bool = True,
    ):
        """Initialize a pixel color element.

        Args:
            name: Unique name for the element
            points_colors: List of (point, color) tuples to check
            tolerance: Color matching tolerance (0-255)
            match_all: If True, all points must match; otherwise, any match succeeds
        """
        super().__init__(name)
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
            min_x = min(p.x for p in points)
            min_y = min(p.y for p in points)
            max_x = max(p.x for p in points)
            max_y = max(p.y for p in points)
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            region = Region(name=self.name, start_x=min_x, start_y=min_y, width=width, height=height,
                            total_width=screenshot.width, total_height=screenshot.height)

            matches = 0
            for point, expected_color in self.points_colors:
                x, y = point

                # Check if point is within the screenshot bounds
                if (y >= screenshot.height or x >= screenshot.width or
                        x < 0 or y < 0):
                    if self.match_all:
                        return DetectionResult(found=False)
                    continue

                r, g, b = screenshot.getpixel((x, y))

                # Check if the colors match within tolerance
                if all(abs(int(a) - int(e)) <= self.tolerance for a, e in zip((r, g, b), expected_color)):
                    matches += 1
                    if not self.match_all:
                        return DetectionResult(found=True, region=region)
                elif self.match_all:
                    return DetectionResult(found=False)

            return DetectionResult(
                found=matches == len(self.points_colors),
                region=region if matches == len(self.points_colors) else None
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
            case_sensitive: bool = False,
            exact_match: bool = False,
    ):
        """Initialize a text element.

        Args:
            name: Unique name for the element
            text: Text to search for
            case_sensitive: Whether text matching is case-sensitive
            exact_match: If True, the text must match exactly; otherwise, partial matches count
        """
        super().__init__(name)
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

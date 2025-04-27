"""
Data collector classes for the automation framework.

This module provides classes for extracting different types of data from the game,
such as text via OCR, numbers, and images.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from PIL import Image

from domain.regions import Region
from .context import Result
from .enums import CollectorType

T = TypeVar('T')  # Generic type for collected data


class DataCollector(Generic[T], ABC):
    """Base class for all data collectors.

    Data collectors are responsible for extracting specific types of data
    from screen regions during automation.
    """

    def __init__(self, region: Region, collector_type: CollectorType):
        """Initialize a data collector.

        Args:
            region: The screen region to collect data from
            collector_type: The type of collector
        """
        self.region = region
        self.collector_type = collector_type

    @abstractmethod
    def collect(self, screenshot: Image.Image) -> Result[T]:
        """Collect data from the specified region in the screenshot.

        Args:
            screenshot: The full screenshot to extract data from

        Returns:
            Result containing the collected data or error
        """
        pass


class OCRCollector(DataCollector[str]):
    """Collector for extracting text using OCR.

    This collector uses Optical Character Recognition to extract text
    from a screen region.
    """

    def __init__(self, region: Region, lang: str = 'eng'):
        """Initialize an OCR collector.

        Args:
            region: The screen region to extract text from
            lang: The language for OCR processing
        """
        super().__init__(region, CollectorType.OCR)
        self.lang = lang

    def collect(self, screenshot: Image.Image) -> Result[str]:
        """Extract text from the specified region using OCR.

        Args:
            screenshot: The full screenshot to extract text from

        Returns:
            Result containing the extracted text or error
        """
        try:
            # Extract region from screenshot
            region_img = self.region.extract_from_image(screenshot)

            # TODO: Implement actual OCR using appropriate library
            # For now, this is a placeholder
            # Example implementation with pytesseract:
            # import pytesseract
            # text = pytesseract.image_to_string(region_img, lang=self.lang)

            # Placeholder implementation
            text = "OCR placeholder result"

            return Result.success(text)
        except Exception as e:
            return Result.failure(f"OCR extraction failed: {str(e)}")


class NumberCollector(DataCollector[float]):
    """Collector for extracting numeric values.

    This collector extracts numbers from a screen region, typically
    by first using OCR and then converting to a numeric value.
    """

    def __init__(self, region: Region, allow_negative: bool = False):
        """Initialize a number collector.

        Args:
            region: The screen region to extract numbers from
            allow_negative: Whether to allow negative numbers
        """
        super().__init__(region, CollectorType.NUMBER)
        self.allow_negative = allow_negative
        self.ocr_collector = OCRCollector(region)

    def collect(self, screenshot: Image.Image) -> Result[float]:
        """Extract a numeric value from the specified region.

        Args:
            screenshot: The full screenshot to extract numbers from

        Returns:
            Result containing the extracted numeric value or error
        """
        # First extract text using OCR
        ocr_result = self.ocr_collector.collect(screenshot)
        if not ocr_result.success:
            return Result.failure(f"Number extraction failed: {ocr_result.error}")

        try:
            # Extract digits and convert to number
            text = ocr_result.data

            # Remove all non-digit characters (keeping decimal point and minus sign if needed)
            chars_to_keep = '0123456789.'
            if self.allow_negative:
                chars_to_keep += '-'

            filtered_text = ''.join(c for c in text if c in chars_to_keep)

            # Convert to float
            number = float(filtered_text)

            return Result.success(number)
        except ValueError:
            return Result.failure(f"Failed to convert '{ocr_result.data}' to a number")
        except Exception as e:
            return Result.failure(f"Number extraction failed: {str(e)}")


class ImageCollector(DataCollector[Image.Image]):
    """Collector for capturing images from screen regions.

    This collector extracts an image from a specified region.
    """

    def __init__(self, region: Region):
        """Initialize an image collector.

        Args:
            region: The screen region to capture
        """
        super().__init__(region, CollectorType.IMAGE)

    def collect(self, screenshot: Image.Image) -> Result[Image.Image]:
        """Capture an image from the specified region.

        Args:
            screenshot: The full screenshot to extract from

        Returns:
            Result containing the captured image or error
        """
        try:
            # Extract region from screenshot
            region_img = self.region.extract_from_image(screenshot)
            return Result.success(region_img)
        except Exception as e:
            return Result.failure(f"Image capture failed: {str(e)}")

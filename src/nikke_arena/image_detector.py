import os
from typing import Optional

import pyautogui
from PIL import Image
from pyscreeze import Box

from .logging_config import get_logger
from .ui_def import DetectableImage
from .window_capturer import WindowCapturer
from .window_info import WindowInfo
from .window_manager import WindowManager

logger = get_logger(__name__)


class ImageDetector:
    """
    Detects images within windows or specific regions of windows
    """

    def __init__(self, window_capturer: WindowCapturer, window_manager: WindowManager, debug_path: str = None):
        """
        Initialize with a WindowCapturer for the target window

        Args:
            window_capturer: The capturer for the target window
        """
        self.window_capturer = window_capturer
        self.window_manager = window_manager
        self.debug_path = None
        if debug_path is not None:
            self.debug_path = debug_path
            if not os.path.exists(self.debug_path):
                os.makedirs(self.debug_path, exist_ok=True)

    def detect_image(self, target: DetectableImage) -> Optional[Box]:
        """
        Detect if target image exists in the specified region

        Args:
            target: DetectableImage containing image name and region

        Returns:
            The location (left, top, width, height) if found, None otherwise
        """
        try:
            # Get target image path
            image_path = target.image_path
            if not image_path or not os.path.exists(image_path):
                return None

            # Get window info for scaling
            window_info = self.window_capturer.window_manager.get_window_info()
            if not window_info:
                logger.error("Failed to get window info")
                return None

            if target.region is None:
                logger.error("Region not specified for image detection")
                return None

            capture_result = self.window_capturer.capture_region(target.region)
            if capture_result is None:
                logger.error("Failed to capture region")
                return None

            target_image = Image.open(image_path)
            target_image = self._scale_image(target_image, window_info)

            if self.debug_path:
                capture_result.save(os.path.join(self.debug_path, f"region_{target.name}.png"))
                target_image.save(os.path.join(self.debug_path, f"target_{target.name}.png"))

            # Use PIL Image with pyautogui
            location = pyautogui.locate(
                target_image,
                capture_result.to_pil(),
                confidence=target.confidence
            )

            if not location:
                logger.info(f"Image {target.image_path} not found in region")
        except Exception as e:
            logger.error(f"Error detecting image: {e}")
            return None


        return location


    def is_image_present(self, target: DetectableImage) -> bool:
        """
        Check if target image exists in the specified region

        Args:
            target: DetectableImage containing image name and region

        Returns:
            True if image is found, False otherwise
        """
        location = self.detect_image(target)
        return location is not None

    @classmethod
    def _scale_image(cls, image: Image.Image, window_info: WindowInfo) -> Image.Image:
        """
        Scale the target image based on window scaling ratios

        Args:
            image: Original target image
            window_info: Window information with scaling ratios

        Returns:
            Scaled image
        """
        width_ratio = window_info.width_ratio
        height_ratio = window_info.height_ratio

        # Only scale if ratios are not 1.0
        if abs(width_ratio - 1.0) < 0.01 and abs(height_ratio - 1.0) < 0.01:
            return image

        try:
            original_width, original_height = image.size
            new_width = int(original_width * width_ratio)
            new_height = int(original_height * height_ratio)

            # Don't scale if too small
            if new_width < 5 or new_height < 5:
                logger.warning(f"Scaled image would be too small: {new_width}x{new_height}, using original")
                return image

            # Resize image using LANCZOS for best quality
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        except Exception as e:
            logger.error(f"Error scaling image: {e}")
            return image  # Return original if scaling fails

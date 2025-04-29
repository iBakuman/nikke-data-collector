import os
from dataclasses import dataclass
from typing import Optional

import mss.tools
from PIL.Image import Image, frombytes
from mss.screenshot import ScreenShot

from collector.ui_def import Region
from .logging_config import get_logger
from .window_manager import WindowManager

logger = get_logger(__name__)


@dataclass
class CaptureResult:
    screenshot: ScreenShot
    region: Region

    def save(self, filename: str):
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        mss.tools.to_png(self.screenshot.rgb, self.screenshot.size, output=filename)

    def to_pil(self) -> Image:
        return frombytes("RGB", self.screenshot.size, self.screenshot.bgra, "raw", "BGRX")


class WindowCapturer:
    def __init__(self, window_manager: WindowManager):
        self.sct = mss.mss()
        self.window_manager = window_manager

    def capture_window(self) -> Optional[CaptureResult]:
        try:
            rect = self.window_manager.get_rect()
            # Convert to mss format (left, top, width, height)
            screenshot = self.sct.grab({
                "top": rect.top,
                "left": rect.left,
                "width": rect.width,
                "height": rect.height,
            })
            # FIXME
            result = CaptureResult(screenshot=screenshot, region=Region(0, 0, rect.width, rect.height))
            return result

        except Exception as e:
            logger.error(f"Error capturing window: {e}")
            return None

    def capture_region(self, region: Region) -> Optional[CaptureResult]:
        try:
            # Calculate the scaled coordinates based on current window size
            scaled_x, scaled_y = self.window_manager.get_window_info().get_scaled_position(region.start_x,
                                                                                           region.start_y)
            scaled_width = int(region.width * self.window_manager.get_window_info().width_ratio)
            scaled_height = int(region.height * self.window_manager.get_window_info().height_ratio)

            # Calculate absolute screen coordinates
            abs_x = self.window_manager.get_window_info().left + scaled_x
            abs_y = self.window_manager.get_window_info().top + scaled_y

            screenshot = self.sct.grab({
                "top": abs_y,
                "left": abs_x,
                "width": scaled_width,
                "height": scaled_height
            })
            result = CaptureResult(screenshot=screenshot, region=region)
            return result

        except Exception as e:
            logger.error(f"Error capturing region: {e}")
            return None

    def __del__(self):
        """Cleanup mss instance."""
        self.sct.close()

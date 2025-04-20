
from typing import Optional

import pyperclip
from PIL import Image

from .logging_config import get_logger
from .models import User
from .mouse_control import MouseController
from .ui_def import PROFILE
from .window_capturer import WindowCapturer

logger = get_logger(__name__)

class ProfileCollector:
    def __init__(self, controller: MouseController, capturer: WindowCapturer):
        self.controller = controller
        self.capturer = capturer

    def collect(self)->User:
        self.controller.click_at_position(PROFILE.copy_id)
        logger.info(f"Clicked copy ID button")
        user_id = pyperclip.paste().strip()
        logger.info(f"Captured user ID: {user_id}")
        user = User(user_id=user_id, profile_image=self._capture_user_image())
        self.controller.click_at_position(PROFILE.close)
        return user

    def _capture_user_image(self)->Optional[Image.Image]:
        capture_result = self.capturer.capture_region(PROFILE.profile_region)
        return capture_result.to_pil()

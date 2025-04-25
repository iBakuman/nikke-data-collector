from dataclasses import dataclass
from typing import Optional

from PIL import Image

from .lineup_processor import LineupProcessor
from .logging_config import get_logger
from .models import User
from .mouse_control import MouseController
from .ui_def import CHEER

logger = get_logger(__name__)


@dataclass
class CheerResult:
    """Contains the results of a cheer (betting) capture operation"""
    left_user: User
    right_user: User
    image: Optional[Image.Image] = None


class CheerCapturer:
    """
    Handles the capture of user data and character lineups from the betting interface
    """

    def __init__(self, lineup_processor: LineupProcessor, controller: MouseController):
        self.lineup_processor = lineup_processor
        self.controller = controller

    def process(self) -> CheerResult:
        self.controller.click_at_position(CHEER.left_user)

        left_user = self.lineup_processor.process()

        self.controller.click_at_position(CHEER.right_user)

        right_user = self.lineup_processor.process()
        logger.info("Capturing current cheer screen")

        result = CheerResult(left_user=left_user, right_user=right_user)

        return result

"""
This module contains the BattleResultCollector class which is responsible
for collecting battle results from recorded matches.
"""
from .image_detector import ImageDetector
from .logging_config import get_logger
from .models import BattleResult, BattleData
from .mouse_control import MouseController
from .ui_def import BATTLE_RESULT, TEAM_INFO
from .utils import copy_id_then_back
from .window_capturer import WindowCapturer

# Get logger from centralized logging configuration
logger = get_logger(__name__)


class BattleDataCollector:
    """
    Collects arena battle results by:
    1. Retrieving user IDs by clicking on user avatars
    2. Detecting win/lose status for the left user
    """

    def __init__(self, detector: ImageDetector, controller: MouseController,
                 capturer: WindowCapturer):
        """
        Initialize the battle result analyzer

        Args:
            detector: Image detector for detecting UI elements
            controller: Mouse controller for clicking on UI elements
        """
        self.detector = detector
        self.capturer = capturer
        self.controller = controller

    def copy_user_id(self, is_left: bool) -> str:
        """
        Click on the left user avatar to open profile

        Returns:
            True if successful, False otherwise
        """
        if is_left:
            ok = self.controller.click_at_position(BATTLE_RESULT.left_user)
        else:
            ok = self.controller.click_at_position(BATTLE_RESULT.right_user)
        user_id = copy_id_then_back(logger, self.controller)

        self.controller.click_at_position(TEAM_INFO.close)
        return user_id

    def collect_battle(self) -> BattleData:
        left_user_id = self.copy_user_id(is_left=True)
        right_user_id = self.copy_user_id(is_left=False)
        battle_data = BattleData(left_user_id=left_user_id, right_user_id=right_user_id)

        for round_num in range(1, 6):
            if self.detector.is_image_present(BATTLE_RESULT.get_detectable_win_image(round_num)):
                battle_data.result.append(BattleResult.VICTORY)
            elif self.detector.is_image_present(BATTLE_RESULT.get_detectable_lose_image(round_num)):
                battle_data.result.append(BattleResult.DEFEAT)
            else:
                battle_data.result.append(BattleResult.UNKNOWN)
                logger.warning(f"Could not determine battle result for round {round_num}")
        capture_result = self.capturer.capture_region(BATTLE_RESULT.get_total_region())
        if capture_result:
            battle_data.image = capture_result.to_pil()
        self.controller.click_at_position(BATTLE_RESULT.close)
        return battle_data

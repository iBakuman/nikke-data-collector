"""
Group Result Processor

This module provides functionality to capture and combine character images
from the group result screen in NIKKE, along with user IDs.
"""
from typing import List, Optional

from PIL.Image import Image

from collector.window_capturer import WindowCapturer
from .lineup_processor import LineupProcessor
from .logging_config import get_logger
from .models import Group, User
from .mouse_control import MouseController
from .ui_def import GROUP_DETAIL
from .utils import combine_images

logger = get_logger(__name__)


class GroupProcessor:
    def __init__(self,
                 controller: MouseController,
                 capturer: WindowCapturer,
                 lineup_processor: LineupProcessor,
                 horizontal_gap: int = 60,
                 boundary_gap: int = 80,
                 ):
        self.controller = controller
        self.capturer = capturer
        self.lineup_capturer = lineup_processor
        self.horizontal_gap = horizontal_gap
        self.boundary_gap = boundary_gap

    def process(self, user_indices: Optional[List[int]] = None) -> Optional[Group]:
        """
        Process users and their rounds, optionally with character recognition.
        Args:
            user_indices: List of specific user indices to process (1-4). If None, uses participants_count or all users.
        Returns:
            Group: Object containing user results and combined image
        """
        try:
            if user_indices is None:
                process_indices = list(range(1, 5))
            else:
                process_indices = [idx for idx in user_indices if 1 <= idx <= 4]

            if not process_indices:
                logger.error("No valid user indices provided")
                return None

            result_image = self.capturer.capture_region(GROUP_DETAIL.result_region).to_pil()
            users: List[User] = []
            for user_index in process_indices:
                user = self._process_single_user(user_index)
                if user is None:
                    logger.error(f"Failed to process user {user_index}")
                users.append(user)

            user_images = [user.team_image for user in users if user.team_image is not None]

            combined_image: Optional[Image] = None
            if user_images:
                combined_image = combine_images(self.horizontal_gap, self.boundary_gap, user_images)
            return Group(users=users, combined_image=combined_image, result_image=result_image)

        except Exception as e:
            logger.error(f"Error processing users: {e}")
            return None

    def _process_single_user(self, user_index: int) -> Optional[User]:
        avatar_pos = GROUP_DETAIL.get_participant_avatar(user_index)
        self.controller.click_at_position(avatar_pos)
        logger.info(f"Clicked on user {user_index} avatar to show team info")
        return self.lineup_capturer.process()

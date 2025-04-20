"""
Group Batch Processor

This module provides functionality to batch process all 64 groups
in the NIKKE Arena tournament, capturing results for each group.
"""
import os
from email.headerregistry import Group
from typing import List, Optional

from .group_processor import GroupProcessor
from .logging_config import get_logger
from .mouse_control import MouseController
from .ui_def import GROUP_SELECTION, GROUP_DETAIL
from .window_capturer import WindowCapturer

logger = get_logger(__name__)


class GroupDataCollector:
    def __init__(self,
                 capturer: WindowCapturer,
                 controller: MouseController,
                 group_processor: GroupProcessor,
                 save_dir: str,
        ):
        self.capturer = capturer
        self.controller = controller
        self.save_dir = os.path.join(save_dir, "groups")
        self.group_processor = group_processor


    def navigate_to_group(self, group_number: int) :
        self.controller.click_at_position(GROUP_DETAIL.group_button)
        logger.info(f"Navigating to group {group_number}")
        group_pos = GROUP_SELECTION.get_group_position(group_number)
        self.controller.click_at_position(group_pos)
        logger.info(f"Clicked on group {group_number}")
        self.controller.click_at_position(GROUP_SELECTION.confirm)
        logger.info("Clicked confirm button to enter group")


    def process_group(self, group_number: int)->Optional[Group]:
        # Create group-specific save directory
        group_dir = os.path.join(self.save_dir, f"group_{group_number}")
        os.makedirs(group_dir, exist_ok=True)
        logger.info(f"Processing group {group_number}")
        group = self.group_processor.process()
        if group is None:
            logger.error(f"Failed to process group {group_number}")
            return None
        group.save_combined_image(os.path.join(group_dir, "combined.png"))
        group.save_result_image(os.path.join(group_dir, "result.png"))
        group.save_as_json(os.path.join(group_dir, "data.json"))
        logger.info(f"Saved group {group_number} data to {group_dir}")
        for user in group.users:
            user.save_profile_image(os.path.join(group_dir, f"user_{user.user_id}_profile.png"))
        return group

    def collect_groups(self, group_numbers: List[int]=None):
        if group_numbers is None or len(group_numbers) == 0:
            group_numbers = list(range(1, 65))
        for group_num in group_numbers:
            self.navigate_to_group(group_num)
            self.process_group(group_num)


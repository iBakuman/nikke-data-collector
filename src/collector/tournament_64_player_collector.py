"""
Tournament 64 Player Collector

This module provides functionality to collect lineup data from the 64-player tournament.
It collects lineup data for each player across 8 groups (8 players per group).
"""
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONWizard, JSONPyWizard

from .lineup_processor import LineupProcessor
from .logging_config import get_logger
from .mixin import JSONSerializableMixin
from .models import User
from .mouse_control import MouseController
from .ui_def import PROMOTION_TOURNAMENT

# Get logger from centralized logging configuration
logger = get_logger(__name__)


@dataclass
class Tournament64PlayerData(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True
    """Data for a 64-player tournament group"""
    group_id: int
    players: List[User] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class Tournament64PlayerCollector:
    """
    Collects lineup data from the 64-player tournament.

    Each group has 8 players, and this collector processes all players in specified groups.
    """

    def __init__(self,
                 controller: MouseController,
                 lineup_processor: LineupProcessor,
                 save_dir: str):
        """
        Initialize the Tournament64PlayerCollector.

        Args:
            controller: Mouse controller for UI interaction
            lineup_processor: Processor for collecting player lineup data
            save_dir: Base directory to save results
        """
        self.controller = controller
        self.lineup_processor = lineup_processor
        self.save_dir = os.path.join(save_dir, "01_tournament_64_player")

        # Ensure save directories exist
        os.makedirs(self.save_dir, exist_ok=True)

    def navigate_to_group(self, group_id: int) -> bool:
        """
        Navigate to a specific group in the tournament.

        Args:
            group_id: Group ID (1-8)

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Navigating to group {group_id}")

        # Get the position for the specified group
        group_pos = PROMOTION_TOURNAMENT.get_group_button_position(group_id)
        return self.controller.click_at_position(group_pos)

    def collect_player(self, group_id: int, player_index: int) -> Optional[User]:
        """
        Collect lineup data for a single player.

        Args:
            group_id: Group ID (1-8)
            player_index: Player index within the group (1-8)

        Returns:
            User object if successful, None otherwise
        """
        logger.info(f"Collecting data for player {player_index} in group {group_id}")

        # Get player avatar position and click on it
        avatar_pos = PROMOTION_TOURNAMENT.get_player_avatar_position(player_index)
        if not self.controller.click_at_position(avatar_pos):
            logger.error(f"Failed to click on avatar for player {player_index}")
            return None

        # Use lineup processor to collect user data
        user = self.lineup_processor.process()

        # Add metadata
        user.group_id = group_id
        user.player_index = player_index

        logger.info(f"Successfully collected data for player {player_index} (User ID: {user.user_id})")

        return user


    def collect_group(self, group_id: int) -> Optional[Tournament64PlayerData]:
        """
        Collect data for all players in a group.

        Args:
            group_id: Group ID (1-8)

        Returns:
            Tournament64PlayerData if successful, None otherwise
        """
        try:
            logger.info(f"Collecting data for group {group_id}")

            # Navigate to the group
            if not self.navigate_to_group(group_id):
                logger.error(f"Failed to navigate to group {group_id}")
                return None

            # Create directory for this group
            group_dir = os.path.join(self.save_dir, f"group_{group_id}")
            os.makedirs(group_dir, exist_ok=True)

            # Initialize group data
            group_data = Tournament64PlayerData(group_id=group_id)

            # Process each player in the group
            for player_index in range(1, 9):
                user = self.collect_player(group_id, player_index)

                if user:
                    # Add to group data
                    group_data.players.append(user)

                    user.save_as_json(os.path.join(group_dir, f"player_{player_index}.json"))
                    user.save_team_image(group_dir, f"player_{player_index}")
                    user.save_profile_image(group_dir, f"player_{player_index}")

            json_path = os.path.join(group_dir, "data.json")
            group_data.save_as_json(json_path)
            logger.info(f"Saved group data to {json_path}")

            return group_data

        except Exception as e:
            logger.error(f"Error collecting group data: {e}")
            return None

    def collect_all_groups(self, group_ids: Optional[List[int]] = None) -> List[Tournament64PlayerData]:
        """
        Collect data for all specified groups.

        Args:
            group_ids: List of group IDs to collect (default: all groups)

        Returns:
            List of Tournament64PlayerData objects
        """
        if group_ids is None:
            group_ids = list(range(1, 9))  # All 8 groups

        logger.info(f"Collecting data for groups {group_ids}")

        # Collect data for each group
        results = []
        for group_id in group_ids:
            # Collect group data
            group_data = self.collect_group(group_id)

            if group_data:
                results.append(group_data)

        logger.info(f"Collected data for {len(results)} groups")
        return results

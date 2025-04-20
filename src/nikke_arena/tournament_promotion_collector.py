"""
Promotion Tournament Collector

This module provides functionality to collect data from the promotion tournament
stages (64->32, 32->16, 16->8).
"""
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONWizard

from .battle_data_collector import BattleDataCollector
from .image_detector import ImageDetector
from .logging_config import get_logger
from .mixin import JSONSerializableMixin
from .models import BattleData, TournamentStage
from .mouse_control import MouseController
from .ui_def import BATTLE_RESULT, PROMOTION_TOURNAMENT
from .window_capturer import WindowCapturer

# Get logger from centralized logging configuration
logger = get_logger(__name__)


@dataclass
class PromotionTournamentData(JSONWizard, JSONSerializableMixin):
    """Data for a promotion tournament stage"""
    stage: TournamentStage
    group_id: int
    battles: List[BattleData] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class PromotionDataCollector:
    """
    Collects data from the promotion tournament stages (64->32, 32->16, 16->8).

    Each stage has 8 groups, and this collector can process specific stages and groups.
    """

    def __init__(self,
                 capturer: WindowCapturer,
                 controller: MouseController,
                 detector: ImageDetector,
                 save_dir: str,
                 ):
        """
        Initialize the PromotionTournamentCollector.

        Args:
            capturer: Window capturer for screenshots
            controller: Mouse controller for UI interaction
            detector: Image detector for UI elements
            save_dir: Base directory to save results
        """
        self.capturer = capturer
        self.controller = controller
        self.detector = detector
        self.save_dir = os.path.join(save_dir, "02_tournament_promotion")

        # Ensure save directories exist
        os.makedirs(self.save_dir, exist_ok=True)

        # Initialize battle data collector
        self.battle_collector = BattleDataCollector(
            detector=detector,
            controller=controller,
            capturer=capturer,
        )

    def navigate_to_group(self, group_id: int):
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
        ok = self.controller.click_at_position(group_pos)

        return ok

    def collect_group(self, stage: TournamentStage, group_id: int) -> Optional[PromotionTournamentData]:
        """
        Collect data for all battles in a group.

        Args:
            stage: Tournament stage
            group_id: Group ID (1-8)

        Returns:
            PromotionTournamentData if successful, None otherwise
        """
        try:
            logger.info(f"Collecting data for {stage.name}, group {group_id}")

            if not self.navigate_to_group(group_id):
                logger.error(f"Failed to navigate to group {group_id}")
                return None

            stage_group_dir = os.path.join(self.save_dir, stage.name, f"group_{group_id}")
            os.makedirs(stage_group_dir, exist_ok=True)
            battles = self._collect_battles(stage)
            # Create tournament data object
            tournament_data = PromotionTournamentData(
                stage=stage,
                group_id=group_id,
                battles=battles
            )

            # Save tournament data as JSON
            json_path = os.path.join(stage_group_dir, "data.json")
            tournament_data.save_as_json(json_path)
            logger.info(f"Saved group data to {json_path}")

            for i, battle in enumerate(battles):
                battle.save_image(os.path.join(stage_group_dir, f"battle_{i + 1}.png"))

            return tournament_data
        except Exception as e:
            logger.error(f"Error collecting group data: {e}")
            return None

    def _collect_battles(self, stage: TournamentStage) -> List[BattleData]:
        """
        Collect data for all battles in a group.
        """
        battles = []
        if stage.value == TournamentStage.STAGE_64_32.value:
            battles = self._collect_stage_64_32()
        elif stage.value == TournamentStage.STAGE_32_16.value:
            battles = self._collect_stage_32_16()
        elif stage.value == TournamentStage.STAGE_16_8.value:
            battles = self._collect_stage_16_8()
        return battles

    def _collect_stage_64_32(self) -> List[BattleData]:
        """
        Collect data for all battles in the 64->32 stage.
        """
        battles = []
        for idx in range(1, 5):
            self.controller.click_at_position(PROMOTION_TOURNAMENT.get_stage_64_32_position(idx))

            battles.append(self.battle_collector.collect_battle())

        return battles

    def _collect_stage_32_16(self) -> List[BattleData]:
        """
        Collect data for all battles in the 32->16 stage.
        """
        result = []
        for i in range(1, 3):
            self.controller.click_at_position(PROMOTION_TOURNAMENT.get_stage_32_16_position(i))

            detected = self.detector.is_image_present(PROMOTION_TOURNAMENT.BUTTON_16)
            if detected:
                self.controller.click_at_position(BATTLE_RESULT.stage_32_16)

            result.append(self.battle_collector.collect_battle())

        return result

    def _collect_stage_16_8(self) -> List[BattleData]:
        """
        Collect data for all battles in the 16->8 stage.
        """
        result = []
        for i in range(1, 3):
            self.controller.click_at_position(PROMOTION_TOURNAMENT.get_stage_32_16_position(i))
            detected = self.detector.is_image_present(PROMOTION_TOURNAMENT.BUTTON_16)
            if not detected:
                self.controller.click_at_position(BATTLE_RESULT.close)
                continue
            result.append(self.battle_collector.collect_battle())
            break
        return result

    def collect_stage(self, stage: TournamentStage, group_ids: Optional[List[int]] = None) -> List[
        PromotionTournamentData]:
        """
        Collect data for all groups in a stage.

        Args:
            stage: Tournament stage
            group_ids: List of group IDs to collect (default: all groups)

        Returns:
            List of PromotionTournamentData objects
        """
        if group_ids is None:
            group_ids = list(range(1, 9))  # All 8 groups

        logger.info(f"Collecting data for {stage.name}, groups {group_ids}")
        results = []
        for group_id in group_ids:
            group_data = self.collect_group(stage, group_id)
            if group_data:
                results.append(group_data)

        logger.info(f"Collected data for {len(results)} groups in {stage.name}")
        return results

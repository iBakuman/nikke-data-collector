"""
Championship Tournament Collector

This module provides functionality to collect data from the championship tournament
(8->4, 4->2, 2->1).
"""
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONWizard, JSONPyWizard

from mixin.json import JSONSerializableMixin
from .battle_data_collector import BattleDataCollector
from .image_detector import ImageDetector
from .logging_config import get_logger
from .models import BattleData, TournamentStage
from .mouse_control import MouseController
from .ui_def import CHAMPIONSHIP_TOURNAMENT, BATTLE_RESULT
from .window_capturer import WindowCapturer

# Get logger from centralized logging configuration
logger = get_logger(__name__)


@dataclass
class ChampionshipTournamentData(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True
    """Data for a championship tournament stage"""
    stage: TournamentStage
    battles: List[BattleData] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class ChampionshipTournamentCollector:
    """
    Collects data from the championship tournament (8->4, 4->2, 2->1).

    This tournament represents the final stages of the competition with the top 8 players.
    All participants are shown on a single page.
    """

    def __init__(self,
                 capturer: WindowCapturer,
                 controller: MouseController,
                 detector: ImageDetector,
                 save_dir: str,
        ):
        """
        Initialize the ChampionshipTournamentCollector.

        Args:
            capturer: Window capturer for screenshots
            controller: Mouse controller for UI interaction
            detector: Image detector for UI elements
            save_dir: Base directory to save results
        """
        self.capturer = capturer
        self.controller = controller
        self.detector = detector
        self.save_dir = os.path.join(save_dir, "03_tournament_championship")
        os.makedirs(self.save_dir, exist_ok=True)
        self.battle_collector = BattleDataCollector(
            detector=detector,
            controller=controller,
            capturer=capturer,
        )

    def _collect_stage_8_4(self) -> List[BattleData]:
        """
        Collect data for all battles in the 8->4 stage.
        """
        battles = []
        for i in range(1, 5):
            # Click on each match position
            match_pos = CHAMPIONSHIP_TOURNAMENT.get_stage_8_4_position(i)
            self.controller.click_at_position(match_pos)

            # Collect battle data
            battle_data = self.battle_collector.collect_battle()
            battles.append(battle_data)

        return battles

    def _collect_stage_4_2(self) -> List[BattleData]:
        """
        Collect data for all battles in the 4->2 stage.
        """
        battles = []
        for i in range(1, 3):
            self.controller.click_at_position(CHAMPIONSHIP_TOURNAMENT.get_stage_4_2_position(i))
            detected = self.detector.is_image_present(CHAMPIONSHIP_TOURNAMENT.CHAMPION_BUTTON)
            if detected:
                self.controller.click_at_position(CHAMPIONSHIP_TOURNAMENT.stage_4_2)

            battle_data = self.battle_collector.collect_battle()
            battles.append(battle_data)

        return battles

    def _collect_stage_2_1(self) -> List[BattleData]:
        """
        Collect data for the battle in the 2->1 stage.
        """
        battles = []
        for i in range(1, 3):
            self.controller.click_at_position(CHAMPIONSHIP_TOURNAMENT.get_stage_4_2_position(i))
            detected = self.detector.is_image_present(CHAMPIONSHIP_TOURNAMENT.CHAMPION_BUTTON)
            if not detected:
                self.controller.click_at_position(BATTLE_RESULT.close)
                continue
            battles.append(self.battle_collector.collect_battle())
            break
        return battles

    def _collect_battles(self, stage: TournamentStage) -> List[BattleData]:
        """
        Collect data for all battles in a stage.
        """
        battles = []
        if stage == TournamentStage.STAGE_8_4:
            battles = self._collect_stage_8_4()
        elif stage == TournamentStage.STAGE_4_2:
            battles = self._collect_stage_4_2()
        elif stage == TournamentStage.STAGE_2_1:
            battles = self._collect_stage_2_1()
        return battles

    def collect_stage(self, stage: TournamentStage) -> Optional[ChampionshipTournamentData]:
        """
        Collect data for all matches in a stage.

        Args:
            stage: Tournament stage

        Returns:
            ChampionshipTournamentData if successful, None otherwise
        """
        try:
            logger.info(f"Collecting data for {stage.name}")
            # Create directory for this stage
            stage_dir = os.path.join(self.save_dir, stage.name)
            os.makedirs(stage_dir, exist_ok=True)

            # Collect the battles
            battles = self._collect_battles(stage)

            # Create tournament data object
            tournament_data = ChampionshipTournamentData(
                stage=stage,
                battles=battles
            )

            tournament_data.save_as_json(os.path.join(stage_dir, "data.json"))
            logger.info(f"Saved stage data to {os.path.join(stage_dir, 'data.json')}")
            for (i, battle) in enumerate(battles):
                image_dir = os.path.join(stage_dir, f"battle_{i+1}.png")
                battle.save_image(image_dir)
                logger.info(f"Saved battle_{i+1} image to {image_dir}")

            return tournament_data
        except Exception as e:
            logger.error(f"Error collecting stage data: {e}")
            return None

    def collect_championship(self, stages: Optional[List[TournamentStage]] = None) -> List[ChampionshipTournamentData]:
        """
        Collect data for all specified stages of the championship tournament.

        Args:
            stages: List of stages to collect (default: all stages)

        Returns:
            List of ChampionshipTournamentData objects
        """
        if stages is None:
            stages = [
                TournamentStage.STAGE_8_4,
                TournamentStage.STAGE_4_2,
                TournamentStage.STAGE_2_1
            ]

        logger.info(f"Collecting data for championship tournament stages: {[s.name for s in stages]}")

        results = []
        for stage in stages:
            stage_data = self.collect_stage(stage)
            if stage_data:
                results.append(stage_data)

        logger.info(f"Collected data for {len(results)} stages in championship tournament")
        return results

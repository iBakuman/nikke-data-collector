import os
import time
from enum import Enum
from typing import Optional

from .image_detector import ImageDetector
from .logging_config import get_logger
from .mouse_control import MouseController
from .ui_def import BATTLE, BATTLE_RESULT
from .window_manager import WindowManager
from .window_recorder import WindowRecorder

logger = get_logger(__name__)


class MatchPhase(Enum):
    """Tournament match phases"""
    ROUND_32 = 1  # First 4 matches (8 players -> 4 players)
    ROUND_16 = 2  # Next 2 matches (4 players -> 2 players)
    QUARTERFINALS = 3
    SEMIFINALS = 4
    FINALS = 5


class TournamentRecorder:
    """Records tournament battles systematically."""

    def __init__(self,
                 window_manager: WindowManager,
                 controller: MouseController,
                 image_detector: ImageDetector,
                 recorder: WindowRecorder):
        """
        Initialize TournamentRecorder.

        Args:
            window_manager: WindowManager instance for window information
            image_detector: ImageDetector for UI navigation
        """
        self.window_manager = window_manager
        self.controller = controller
        self.image_detector = image_detector
        self.recorder = recorder

    def record_tournament(self, output_dir: str, phase: MatchPhase, groups: list[int] = None) -> bool:
        if groups is None:
            groups = range(1, 9)
        for group_num in groups:
            logger.info(f"Starting recordings for Group {group_num}")

            # Navigate to the specified group if needed
            if not self._navigate_to_group(group_num):
                logger.error(f"Failed to navigate to Group {group_num}")
                continue

            # Create group directory
            group_dir = os.path.join(output_dir, f"Group_{group_num}")
            os.makedirs(group_dir, exist_ok=True)

            # Record each phase of matches in this group
            self.record_group_matches(group_num, group_dir, phase)

        return True

    @classmethod
    def _validate_matches(cls, phase: MatchPhase, matches: Optional[list[int]] = None) -> Optional[list[int]]:
        if phase == MatchPhase.ROUND_32:
            if matches is None:
                matches = range(1, 5)
            elif not 1 <= len(matches) <= 4:
                raise ValueError("First match number must be between 1 and 4")
            elif not all(1 <= num <= 4 for num in matches):
                raise ValueError("Match numbers for ROUND_32 must be between 1 and 4")
            else:
                return matches
        elif phase == MatchPhase.ROUND_16:
            if matches is None:
                matches = range(1, 3)
            elif not 1 <= len(matches) <= 2:
                raise ValueError("Second match number must be between 1 and 2")
            elif not all(1 <= num <= 2 for num in matches):
                raise ValueError("Match numbers for ROUND_16 must be between 1 and 2")
            else:
                return matches
        elif phase == MatchPhase.QUARTERFINALS:
            if matches is None:
                matches = [1]
            elif len(matches) != 1:
                raise ValueError("Final round must have 1 match")
            elif matches[0] != 1:
                raise ValueError("Match number for QUARTERFINALS must be 1")
            else:
                return matches
        return matches

    def record_group_matches(self, group_num: int, group_dir: str, phase: MatchPhase,
                             matches: Optional[list[int]] = None) -> None:
        """
        Record all matches within a tournament group.

        Args:
            group_num: Group number (1-8)
            group_dir: Directory to save group recordings
            phase: Match phase to record
            matches: List of match numbers to record
        """
        match_dir = os.path.join(group_dir, f"Phase_{phase.value}")
        matches = self._validate_matches(phase, matches)
        for match_num in matches:
            self._record_match(group_num, match_dir, phase, match_num)

    def _record_match(self, group_num: int, match_dir: str, phase: MatchPhase, match_num: int) -> bool:
        """
        Record a specific match in the tournament.

        Args:
            group_num: Group number (1-8)
            match_dir: Directory to save match recordings
            phase: Tournament phase
            match_num: Match number within the phase

        Returns:
            bool: True if recording was successful
        """
        # Construct unique filename for this match
        save_dir = os.path.join(match_dir, f"Match_{match_num}")
        os.makedirs(save_dir, exist_ok=True)
        logger.info(f"Recording match: Group {group_num}, Phase {phase.name}, Match {match_num}")
        try:
            # Click on the match in the tournament bracket
            if not self._navigate_to_match(phase, match_num):
                logger.error(f"Failed to navigate to match: Phase {phase.name}, Match {match_num}")
                return False

            for round_num in range(1, 6):
                if not self._record_round(round_num, save_dir):
                    logger.error(f"Failed to record round {round_num}")
                    return False

            # Navigate back to tournament bracket view
            self._navigate_back_to_bracket()
            logger.info(f"Successfully recorded: {save_dir}")
            return True

        except Exception as e:
            logger.error(f"Error recording match: {e}")
            return False

    def _record_round(self, round_num: int, save_dir: str):
        # Find and click play button
        if not self._click_play_button(round_num):
            logger.error("Failed to find play button")
            return False

        filename = f"Round_{round_num}.mp4"
        if not self.recorder.start_recording(save_dir, filename=filename, audio=False, framerate=30):
            logger.error("Failed to start recording")
            return False

        if not self._wait_for_battle_end():
            logger.error("Failed to wait for battle end")
            return False

        if not self.recorder.stop_recording():
            logger.error("Failed to stop recording")
            return False

        self.controller.click_at_position(BATTLE.next)

        return True

    def _wait_for_battle_end(self, timeout: int = 100):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.image_detector.is_image_present(BATTLE_RESULT.STATISTIC_IMAGE):
                return True

        return False

    def _navigate_to_group(self, group_num: int) -> bool:
        """
        Navigate to the specified tournament group.

        Args:
            group_num: Group number to navigate to (1-8)

        Returns:
            bool: True if navigation was successful
        """
        # return self.controller.click_at_position(TOURNAMENT.get_group_button(group_num))

    def _navigate_to_match(self, phase: MatchPhase, match_num: int) -> bool:
        """
        Navigate to a specific match in the tournament bracket.

        Args:
            phase: Tournament phase
            match_num: Match number in the phase

        Returns:
            bool: True if navigation was successful
        """
        # if phase == MatchPhase.ROUND_32:
        #     if match_num == 1:
        #         return self.controller.click_at_position(TOURNAMENT.user_32_a_play)
        #     elif match_num == 2:
        #         return self.controller.click_at_position(TOURNAMENT.user_32_b_play)
        #     elif match_num == 3:
        #         return self.controller.click_at_position(TOURNAMENT.user_32_c_play)
        #     elif match_num == 4:
        #         return self.controller.click_at_position(TOURNAMENT.user_32_d_play)
        # elif phase == MatchPhase.ROUND_16:
        #     if match_num == 1:
        #         return self.controller.click_at_position(TOURNAMENT.user_16_a_play)
        #     elif match_num == 2:
        #         return self.controller.click_at_position(TOURNAMENT.user_16_b_play)
        # elif phase == MatchPhase.QUARTERFINALS:
        #     return self.controller.click_at_position(TOURNAMENT.user_8_a_play)
        return True

    def _click_play_button(self, round_num: int) -> bool:
        """
        Find and click the play button for a match.

        Returns:
            bool: True if play button was found and clicked
        """
        return self.controller.click_at_position(BATTLE_RESULT.get_play_position(round_num))

    def _navigate_back_to_bracket(self) -> bool:
        """
        Navigate back to the tournament bracket view.

        Returns:
            bool: True if navigation was successful
        """
        return self.controller.click_at_position(BATTLE_RESULT.close)

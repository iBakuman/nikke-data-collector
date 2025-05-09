from typing import List, Optional

from PIL import Image

from collector.profile_collector import ProfileCollector
from domain.character import Character
from .character_matcher import CharacterMatcher
from .logging_config import get_logger
from .models import Round, User
from .mouse_control import MouseController
from .ui_def import TEAM_INFO
from .window_capturer import WindowCapturer

logger = get_logger(__name__)


class LineupProcessor:

    def __init__(self, controller: MouseController, capturer: WindowCapturer, profile_collector: ProfileCollector, matcher:  CharacterMatcher= None):
        self.controller = controller
        self.capturer = capturer
        self.profile_collector = profile_collector
        self.matcher = matcher

    def process(self) -> User:
        self.controller.click_at_position(TEAM_INFO.avatar)
        logger.info(f"Clicked on avatar button to view profile")
        user = self.profile_collector.collect()
        self._capture_user_rounds(user)
        user.team_image = self.combine_round_images([_round.image for _round in user.rounds.values()])
        return user

    def _capture_user_rounds(self, user: User):
        try:
            for round_index in range(1, 6):
                round_pos = TEAM_INFO.get_round_button(round_index)
                self.controller.click_at_position(round_pos)
                logger.info(f"Clicked on round {round_index} button")
                capture_result = self.capturer.capture_region(TEAM_INFO.round_region)
                _round = Round(round_index=round_index, image=capture_result.to_pil())
                self._capture_character_images(_round)
                user.add_round(_round)

            # After capturing all rounds, click somewhere else to close the detail view
            self.controller.click_at_position(TEAM_INFO.close)
            logger.info("Clicked close button to exit detail view")


        except Exception as e:
            logger.error(f"Error capturing rounds for user {user.user_id}: {e}")

    def _capture_character_images(self, _round: Round):
        try:
            for position_idx in range(5):
                # Directly capture from screen
                capture_result = self.capturer.capture_region(TEAM_INFO.get_character_region(position_idx+1))
                if capture_result:
                    logger.debug(f"Captured character at position {position_idx + 1} in round {_round.round_index}")
                else:
                    logger.error(
                        f"Failed to capture character at position {position_idx + 1} in round {_round.round_index}")
                    return
                character_image = capture_result.to_pil()
                character = Character(position=position_idx + 1, image=character_image)
                if self.matcher:
                    match_result = self.matcher.match(character_image)
                    if match_result.has_match:
                        character.id = match_result.character.id
                        character.name = match_result.character.name
                _round.add_character(character)
        except Exception as e:
            logger.error(f"Error capturing character images for round {_round.round_index}: {e}")

    @classmethod
    def combine_round_images(cls, round_images: List[Image.Image]) -> Optional[Image.Image]:
        """
        Combine multiple round images vertically.

        Args:
            round_images: List of round images to combine

        Returns:
            Combined image or None if no images
        """
        # If we didn't get any images, return None
        if not round_images:
            return None

        # Create a new image to hold the vertical stack
        total_height = sum(img.height for img in round_images)
        max_width = max(img.width for img in round_images)

        combined = Image.new('RGBA', (max_width, total_height), (255, 255, 255, 0))

        # Paste each round image
        y_offset = 0
        for img in round_images:
            combined.paste(img, ((max_width - img.width) // 2, y_offset))  # Center horizontally
            y_offset += img.height

        return combined

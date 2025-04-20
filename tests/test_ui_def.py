import logging

from nikke_arena.mouse_control import MouseController
from nikke_arena.ui_def import CHAMPIONSHIP_TOURNAMENT, GROUP_DETAIL, PROFILE, PROMOTION_TOURNAMENT, TEAM_INFO
from nikke_arena.window_capturer import WindowCapturer
from tests.utils import keyboard_terminable

logger = logging.getLogger(__name__)

@keyboard_terminable()
def test_championship(controller):
    """Test championship tournament UI definition with subtests."""

    # Subtest for 8->4 stage positions
    for i in range(1, 5):
        controller.move_to_position(CHAMPIONSHIP_TOURNAMENT.get_stage_8_4_position(i))

    for i in range(1, 3):
        controller.move_to_position(CHAMPIONSHIP_TOURNAMENT.get_stage_4_2_position(i))

@keyboard_terminable()
def test_group_detail(controller: MouseController):
    """
    Test script for interacting with participants in a group view.
    """
    logger.info("Starting group view test")

    for participant_index in range(1, 5):
        # Click on participant avatar
        avatar_position = GROUP_DETAIL.get_participant_avatar(participant_index)
        logger.info(f"Checking participant {participant_index} avatar")
        controller.click_at_position(avatar_position)
        controller.click_at_position(TEAM_INFO.close)

    logger.info("Group view test completed")

def test_team_info(capturer: WindowCapturer):
    for i in range(1, 6):
        capturer.capture_region(TEAM_INFO.get_character_region(i)).save(f"testdata/ui_def/team_info/character_{i}.png")
    capturer.capture_region(TEAM_INFO.round_region).save(f"testdata/ui_def/team_info/round.png")


def test_profile(capturer: WindowCapturer):
    capturer.capture_region(PROFILE.profile_region).save(f"testdata/ui_def/profile/profile.png")

@keyboard_terminable()
def test_promotion_tournament(controller: MouseController):
    for i in range(1, 9):
        controller.move_to_position(PROMOTION_TOURNAMENT.get_player_avatar_position(i))



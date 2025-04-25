"""
Test script for Round Selection buttons in match details screen.

This script demonstrates how to interact with round buttons
in the match details screen.
"""
import logging

from collector.mouse_control import MouseController
from collector.ui_def import TEAM_INFO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_all_rounds_in_order(controller: MouseController):
    """
    Test clicking all round buttons in order from 1 to 5.
    """
    logger.info("Starting all rounds test")

    # Click on each round button in sequence (1-5)
    for round_number in range(1, 6):
        position = TEAM_INFO.get_round_button(round_number)
        logger.info(f"Clicking Round {round_number} button")
        controller.click_at_position(position)
        

    # Close the match details screen
    logger.info("Closing match details screen")
    controller.click_at_position(TEAM_INFO.close)

    logger.info("All rounds test completed")

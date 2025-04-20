"""
Test script for Group Selection screen automation.

This script demonstrates how to interact with the Group Selection interface
using the mouse controller and UI constants.
"""
import logging
from typing import List

from nikke_arena.mouse_control import MouseController
from nikke_arena.ui_def import GROUP_SELECTION
from tests.utils import keyboard_terminable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def select_groups(controller: MouseController, group_numbers: List[int]) -> bool:
    """
    Select multiple groups from the group selection screen.

    Args:
        controller: MouseController instance
        group_numbers: List of group numbers to select (1-based)

    Returns:
        bool: True if all operations completed successfully
    """
    window_info = controller.get_window_info()
    if not window_info:
        logger.error("Could not locate the NIKKE window")
        return False

    # Select each group in sequence
    for group_num in group_numbers:
        try:
            # Get position using the dynamic method
            group_position = GROUP_SELECTION.get_group_position(group_num)
            logger.info(f"Selecting group {group_num}")
            controller.click_at_position(group_position)
            
        except ValueError as e:
            logger.warning(f"Invalid group number: {e}")
            continue
    return True


def test_select_specified_group(controller: MouseController):
    """
    Test the group selection screen interaction.
    Demonstrates selecting groups and confirming the selection.
    """
    logger.info("Starting group selection test")
    # Note: In a real scenario, you would need to navigate to this screen first
    # Select multiple groups in sequence - now we can select any group from 1-64
    groups_to_select = [1, 3, 7, 20, 35]
    if select_groups(controller, groups_to_select):
        # Confirm the selection
        logger.info("Confirming group selection")
        controller.click_at_position(GROUP_SELECTION.confirm)
        
        logger.info("Group selection completed successfully")
    else:
        logger.error("Failed to complete group selection")
        # Example of how to cancel if needed
        controller.click_at_position(GROUP_SELECTION.cancel)


@keyboard_terminable()
def test_select_all_groups(controller: MouseController):
    """
    Demonstration of selecting all groups in the first three rows.
    """
    logger.info("Starting demo to select all groups")
    # Select all groups in first three rows (1-15)
    all_groups = list(range(1, 65))
    if select_groups(controller, all_groups):
        logger.info("Successfully selected all groups in rows 1-3")
        controller.click_at_position(GROUP_SELECTION.confirm)
    else:
        logger.error("Failed to select all groups")
        controller.click_at_position(GROUP_SELECTION.cancel)

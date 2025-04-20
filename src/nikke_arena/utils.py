from logging import Logger
from typing import List, Optional

import pyperclip
from PIL import Image

from nikke_arena.mouse_control import MouseController
from nikke_arena.ui_def import TEAM_INFO, PROFILE


def combine_images(horizontal_gap: int, boundary_gap: int, images: List[Image.Image]) -> Optional[Image.Image]:
    if len(images) == 0:
        return None
    max_height = max(img.height for img in images)
    total_width = sum(img.width for img in images) + \
                  horizontal_gap * (len(images) - 1) + \
                  (boundary_gap * 2)

    # Add boundary gap to height as well (top and bottom)
    total_height = max_height + (boundary_gap * 2)

    # Create the final image with white background (not transparent)
    combined_image = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 255))

    # Paste each user's combined image with the configured gaps
    x_offset = boundary_gap
    for img in images:
        # Calculate vertical offset to center the image and add boundary gap
        y_offset = boundary_gap + (max_height - img.height) // 2  # Center vertically with boundary gap

        # Add a border by creating a slightly larger background image
        border_width = 4  # Border thickness in pixels
        bordered_img = Image.new('RGBA',
                                 (img.width + 2 * border_width,
                                  img.height + 2 * border_width),
                                 (0, 0, 0, 255))  # Black border

        # Paste the user image onto the bordered background
        bordered_img.paste(img, (border_width, border_width))

        # Paste the bordered image onto the final image
        combined_image.paste(bordered_img, (x_offset, y_offset))

        # Update x_offset for next image
        x_offset += bordered_img.width + horizontal_gap

    return combined_image


def copy_id_then_back(logger: Logger, controller: MouseController) -> str:
    # Now in team info screen, click on avatar to go to profile
    controller.click_at_position(TEAM_INFO.avatar)
    logger.info(f"Clicked on avatar button to view profile")

    # In profile screen, click copy ID button
    controller.click_at_position(PROFILE.copy_id)
    logger.info(f"Clicked copy ID button")

    # Get user ID from clipboard
    user_id = pyperclip.paste().strip()
    logger.info(f"Captured user ID: {user_id}")

    # Close profile screen
    controller.click_at_position(PROFILE.close)
    return user_id

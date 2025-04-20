import time
from typing import Optional, Sequence, Tuple, Union

import pyautogui

from .delay_manager import DelayManager
from .logging_config import get_logger
from .ui_def import Position
from .window_info import WindowInfo
from .window_manager import WindowManager

logger = get_logger(__name__)


class MouseController:
    """
    Class to handle mouse interactions with the application window using standard coordinates.
    Automatically maintains a WindowCapturer instance.
    """

    def __init__(self, window_manager: WindowManager, delay_manager: DelayManager = None):
        self.window_manager = window_manager
        if delay_manager is None:
            self.delay_manager = DelayManager(1.5, 2.5)
        else:
            self.delay_manager = delay_manager

    def get_window_info(self) -> Optional[WindowInfo]:
        """
        Get current window information.

        Returns:
            Optional[WindowInfo]: Window information object or None if not found
        """
        return self.window_manager.get_window_info()

    def _prepare_position(self, x: Union[int, Position], y: Optional[int] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Prepare position coordinates for mouse operations.

        Args:
            x: Either a Position object or x coordinate in standard window size
            y: Y coordinate in standard window size (not needed if x is a Position)

        Returns:
            Optional[Tuple[int, int, int, int]]: (standard_x, standard_y, abs_x, abs_y) or None if failed
        """
        try:
            # Check if we received a Position object
            if isinstance(x, Position):
                standard_x, standard_y = x.x, x.y
            else:
                # Original behavior with separate x, y coordinates
                standard_x, standard_y = x, y

            if standard_y is None:
                logger.error("Y coordinate cannot be None when providing coordinates separately")
                return None

            window_info = self.get_window_info()

            if not window_info:
                logger.error(f"Failed to get window info for: {self.window_manager.process_name}")
                return None

            # Calculate absolute screen position
            abs_x, abs_y = window_info.get_absolute_position(standard_x, standard_y)
            return standard_x, standard_y, abs_x, abs_y

        except Exception as e:
            logger.error(f"Error preparing position: {e}")
            return None

    def click_at_position(self, x: Union[int, Position], y: Optional[int] = None, button: str = 'left', delay:float = None) -> bool:
        """
        Click on a position based on standard coordinates (3580x2014).

        Args:
            x: Either a Position object or x coordinate in standard window size
            y: Y coordinate in standard window size (not needed if x is a Position)
            button (str): Mouse button to click ('left', 'right', 'middle')
            delay (float): Delay in seconds to wait after clicking
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self._prepare_position(x, y)
            if not result:
                return False

            standard_x, standard_y, abs_x, abs_y = result

            # Perform the click
            pyautogui.click(abs_x, abs_y, button=button)
            logger.info(
                f"Clicked at standard position ({standard_x}, {standard_y}) => screen position ({abs_x}, {abs_y})")
            if delay is not None:
                time.sleep(delay)
            else:
                self.delay_manager.sleep()
            return True

        except Exception as e:
            logger.error(f"Error clicking on window: {e}")
            return False

    def move_to_position(self, x: Union[int, Position], y: Optional[int] = None, delay: float = None) -> bool:
        """
        Move mouse pointer to a position based on standard coordinates (3580x2014) without clicking.

        Args:
            x: Either a Position object or x coordinate in standard window size
            y: Y coordinate in standard window size (not needed if x is a Position)
            delay (float): Delay in seconds to wait after moving
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self._prepare_position(x, y)
            if not result:
                return False

            standard_x, standard_y, abs_x, abs_y = result

            # Move the mouse without clicking
            pyautogui.moveTo(abs_x, abs_y)
            logger.info(
                f"Moved to standard position ({standard_x}, {standard_y}) => screen position ({abs_x}, {abs_y})")
            if delay is not None:
                time.sleep(delay)
            else:
                self.delay_manager.sleep()
            return True

        except Exception as e:
            logger.error(f"Error moving mouse to position: {e}")
            return False

    def click_multiple_positions(self, positions: Sequence[Union[Position, Tuple[int, int]]],
                                 button: str = 'left', interval: float = 0.5) -> bool:
        """
        Click on multiple standard positions in sequence.

        Args:
            positions: List of Position objects or (x, y) tuples in standard coordinates
            button (str): Mouse button to click ('left', 'right', 'middle')
            interval (float): Time to wait between clicks in seconds

        Returns:
            bool: True if all clicks successful, False otherwise
        """
        try:
            window_info = self.get_window_info()

            if not window_info:
                logger.error(f"Failed to get window info for: {self.window_manager.process_name}")
                return False

            # Perform each click
            for idx, pos in enumerate(positions):
                # Handle both Position objects and (x, y) tuples
                if isinstance(pos, Position):
                    standard_x, standard_y = pos.x, pos.y
                else:
                    standard_x, standard_y = pos[0], pos[1]

                abs_x, abs_y = window_info.get_absolute_position(standard_x, standard_y)
                pyautogui.click(abs_x, abs_y, button=button)
                logger.info(
                    f"Click {idx + 1}/{len(positions)}: position ({standard_x}, {standard_y}) => screen ({abs_x}, {abs_y})")

                if idx < len(positions) - 1:  # Don't wait after the last click
                    pyautogui.sleep(interval)

            return True

        except Exception as e:
            logger.error(f"Error during multiple clicks: {e}")
            return False

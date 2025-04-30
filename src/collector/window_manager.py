import time
from typing import Dict, Optional, Tuple

import psutil
import win32api
import win32con
import win32gui
import win32process

from .logging_config import get_logger
from .ui_def import STANDARD_WINDOW_HEIGHT, STANDARD_WINDOW_WIDTH
from .window_info import WindowInfo, Region

logger = get_logger(__name__)


class WindowNotFoundException(Exception):
    """Exception raised when a window for a specific process is not found."""

    def __init__(self, process_name):
        self.process_name = process_name
        message = f"Window not found for process: {process_name}"
        super().__init__(message)


class WindowManager:
    def __init__(self, process_name: str,
                 standard_width: Optional[int] = None,
                 standard_height: Optional[int] = None,
                 exact_match: bool = True):
        """
        Initialize the WindowCapture class with mss instance and process name.

        Args:
            process_name (str): Name of the process to capture (e.g., 'nikke.exe')
            exact_match (bool): Whether to require exact process name match
        """
        self.process_name = process_name
        self.standard_width = standard_width
        self.standard_height = standard_height
        if standard_width is None or standard_height is None:
            self.standard_width = STANDARD_WINDOW_WIDTH
            self.standard_height = STANDARD_WINDOW_HEIGHT
        self.exact_match = exact_match
        self._update_window_info()

    def _update_window_info(self):
        hwnd = get_window_handle(self.process_name, self.exact_match)
        if not hwnd:
            raise WindowNotFoundException(self.process_name)
        rect = get_window_rect(hwnd)
        if not rect:
            raise Exception("Failed to get window rect")
        self._window_info = WindowInfo(hwnd, rect, self.standard_width, self.standard_height)
        logger.info(f"Got window info: {self._window_info}")

    def get_window_info(self) -> WindowInfo:
        self._update_window_info()
        return self._window_info

    @property
    def hwnd(self) -> int:
        self._update_window_info()
        return self._window_info.hwnd

    @property
    def rect(self) -> Region:
        self._update_window_info()
        return self._window_info.rect

    @property
    def start_x(self):
        self._update_window_info()
        return self._window_info.left

    @property
    def start_y(self):
        self._update_window_info()
        return self._window_info.top

    @property
    def height(self):
        self._update_window_info()
        return self._window_info.height

    @property
    def width(self):
        self._update_window_info()
        return self._window_info.width

    def resize_to_standard(self, width: int = 1500, position: str = "top-left", margin: int = 10) -> bool:
        """
        Resize the window's client area based on specified width.
        Positions the window in the specified corner with a fixed margin.

        Args:
            width (int): Desired width in pixels for the client area. Default 1500.
            position (str): Position of window - 'top-left', 'top-right', 'bottom-left', 'bottom-right'. Default 'top-left'.
            margin (int): Fixed margin in pixels between window edge and screen edge. Default 10.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find which monitor the window is currently on
            monitor_info = self._get_window_monitor_info(self.hwnd)
            if not monitor_info:
                return False

            # Restore window if maximized
            self._restore_if_maximized(self.hwnd)

            # Get current window dimensions
            current_rect = win32gui.GetWindowRect(self.hwnd)
            client_rect = win32gui.GetClientRect(self.hwnd)
            client_width, client_height = client_rect[2], client_rect[3]

            # Calculate frame dimensions
            frame_width = (current_rect[2] - current_rect[0]) - client_width
            frame_height = (current_rect[3] - current_rect[1]) - client_height

            # Calculate target dimensions based on monitor size
            monitor_rect = monitor_info['monitor']
            monitor_width = monitor_rect[2] - monitor_rect[0]
            monitor_height = monitor_rect[3] - monitor_rect[1]

            # Calculate target size based on specified width
            target_size = self._calculate_target_size_by_width(
                width,
                monitor_width,
                monitor_height
            )

            # Calculate window size including frame
            new_width = target_size['width'] + frame_width
            new_height = target_size['height'] + frame_height

            # Position window based on requested position with fixed margin
            # Position the entire window (including title bar and borders) with the specified margin
            if position == "top-left":
                new_left = monitor_rect[0] + margin
                new_top = monitor_rect[1] + margin
            elif position == "top-right":
                new_left = monitor_rect[2] - new_width - margin
                new_top = monitor_rect[1] + margin
            elif position == "bottom-left":
                new_left = monitor_rect[0] + margin
                new_top = monitor_rect[3] - new_height - margin
            elif position == "bottom-right":
                new_left = monitor_rect[2] - new_width - margin
                new_top = monitor_rect[3] - new_height - margin
            else:
                # Default to top-left if invalid position
                new_left = monitor_rect[0] + margin
                new_top = monitor_rect[1] + margin

            # Resize window
            win32gui.MoveWindow(self.hwnd, new_left, new_top, new_width, new_height, True)

            # Update window info with new rect
            self._window_info = WindowInfo(self.hwnd, get_window_rect(self.hwnd), self.standard_width, self.standard_height)

            return True

        except Exception as e:
            logger.error(f"Error resizing window: {e}")
            return False

    @classmethod
    def _restore_if_maximized(cls, hwnd: int) -> None:
        """
        Restore window if it's maximized

        Args:
            hwnd: Window handle
        """
        window_placement = win32gui.GetWindowPlacement(hwnd)
        is_maximized = window_placement[1] == win32con.SW_SHOWMAXIMIZED
        if is_maximized:
            logger.info("Window is maximized, restoring to normal state")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.6)  # Wait for restore

    def _calculate_target_size_by_width(self, target_width: int, monitor_width: int, monitor_height: int) -> Dict[
        str, int]:
        """
        Calculate target client size based on desired width, maintaining aspect ratio

        Args:
            target_width: Desired width in pixels
            monitor_width: Width of the monitor
            monitor_height: Height of the monitor

        Returns:
            Dictionary with target width and height
        """
        # Ensure width is within screen bounds
        max_width = monitor_width - 50  # Leave a small margin
        target_width = min(target_width, max_width)

        # Calculate height based on standard aspect ratio
        aspect_ratio = self.standard_height / self.standard_width
        target_height = int(target_width * aspect_ratio)

        # If height is too large for screen, scale down
        max_height = monitor_height - 50  # Leave a small margin
        if target_height > max_height:
            target_height = max_height
            target_width = int(target_height / aspect_ratio)

        logger.info(f"Using dimensions: {target_width}x{target_height}")

        return {'width': target_width, 'height': target_height}

    @classmethod
    def _get_window_monitor_info(cls, hwnd: int) -> Optional[Dict]:
        """
        Get information about the monitor where the window is displayed.

        Args:
            hwnd: Window handle

        Returns:
            Dictionary with monitor information or None if failed
        """
        try:
            # Get the monitor that has the largest area of intersection with the window
            window_rect = win32gui.GetWindowRect(hwnd)
            monitor_handle = win32api.MonitorFromRect(window_rect, win32con.MONITOR_DEFAULTTONEAREST)
            monitor_info = win32api.GetMonitorInfo(monitor_handle)

            result = {
                'handle': monitor_handle,
                'work_area': monitor_info['Work'],  # (left, top, right, bottom) excluding taskbar
                'monitor': monitor_info['Monitor'],  # (left, top, right, bottom) entire monitor
                'is_primary': monitor_info['Flags'] & win32con.MONITORINFOF_PRIMARY != 0
            }

            logger.info(f"Window is on monitor: {result['monitor'][0]},{result['monitor'][1]} - "
                        f"{result['monitor'][2]},{result['monitor'][3]}")
            return result

        except Exception as e:
            logger.error(f"Error getting monitor info: {e}")
            return None


def get_process_name_by_pid(pid: int) -> Optional[str]:
    """
    Get process name from process ID using psutil.

    Args:
        pid (int): Process ID

    Returns:
        Optional[str]: Process name if found, None otherwise
    """
    try:
        process = psutil.Process(pid)
        return process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        logger.debug(f"Error getting process name for PID {pid}: {e}")
        return None


def get_window_handle(process_name: str, exact_match: bool = True) -> Optional[int]:
    """
    Get the window handle for a specific process name.

    Args:
        process_name (str): Name of the process to find (e.g., 'nikke.exe')
        exact_match (bool): Whether to require exact process name match

    Returns:
        Optional[int]: Window handle if found, None otherwise
    """

    def callback(hwnd, hwnds):
        if not win32gui.IsWindowVisible(hwnd):
            return True

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc_name = get_process_name_by_pid(pid)

        if proc_name:
            if exact_match and proc_name.lower() == process_name.lower():
                hwnds.append(hwnd)
            elif not exact_match and process_name.lower() in proc_name.lower():
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None


def get_window_rect(hwnd: int) -> Optional[Region]:
    """
    Get the window client area rectangle coordinates.

    Args:
        hwnd (int): Window handle

    Returns:
        Optional[Tuple[int, int, int, int]]: (left, top, right, bottom) coordinates of client area
    """
    try:
        # Get the window client area
        client_rect = win32gui.GetClientRect(hwnd)
        client_left, client_top, client_right, client_bottom = client_rect

        # Convert client coordinates to screen coordinates
        point_left_top = win32gui.ClientToScreen(hwnd, (client_left, client_top))
        point_right_bottom = win32gui.ClientToScreen(hwnd, (client_right, client_bottom))
        return Region(left=point_left_top[0], top=point_left_top[1],
                      right=point_right_bottom[0], bottom=point_right_bottom[1],
                      width=point_right_bottom[0] - point_left_top[0],
                      height=point_right_bottom[1] - point_left_top[1]
                      )


    except Exception as e:
        logger.error(f"Error getting window client rectangle: {e}")
        return None

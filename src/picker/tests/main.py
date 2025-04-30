import os
import sys

from collector.window_capturer import WindowCapturer
from collector.window_manager import WindowManager
from picker.data import get_page_config_path
from picker.picker_page_config import run_config_window

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

if __name__ == "__main__":
    """Run the page configuration window."""
    window_manager = WindowManager("nikke.exe")
    # Create window capturer
    capturer = WindowCapturer(window_manager)
    # Run configuration window
    exit_code = run_config_window(get_page_config_path(), capturer)
    sys.exit(exit_code)

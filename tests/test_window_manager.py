from collector.window_manager import WindowManager


def test_window_manager(manager: WindowManager):
    manager.resize_to_standard(width=1500,position="top-left")
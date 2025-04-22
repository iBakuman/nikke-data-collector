from nikke_arena.window_manager import WindowManager


def test_window_manager(manager: WindowManager):
    manager.resize_to_standard(ratio=0.9,position="top-right")
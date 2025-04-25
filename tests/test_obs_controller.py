from collector.obs_controller import OBSController, OBSInfo
from collector.window_manager import WindowManager


def test_obs_controller(manager: WindowManager):
    obs_controller = OBSController(window_manager=manager, obs_info=OBSInfo(password="jmGWO95LGMjEFDV5"))
    assert obs_controller.connect() is True
    # assert obs_controller.setup_window_capture()
    assert obs_controller.start_recording("testdata/obs", "nikke.mp4") is True
    
    obs_controller.stop_recording()
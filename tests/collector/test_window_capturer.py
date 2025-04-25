from collector.ui_def import Region
from collector.window_capturer import WindowCapturer


def test_window_capture(capturer: WindowCapturer):
    capture_result = capturer.capture_window()
    capture_result.save("testdata/capturer/window.png")
    region = Region(start_x=1344, start_y=955, width=893, height=455)
    region_result = capturer.capture_region(region)
    region_result.save("testdata/capturer/region.png")

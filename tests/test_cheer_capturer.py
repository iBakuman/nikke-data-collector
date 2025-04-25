import os

from collector.cheer_processor import CheerCapturer
from collector.utils import combine_images
from tests.utils import keyboard_terminable


@keyboard_terminable()
def test_cheer_capturer(controller, lineup_processor):
    cheer_capturer = CheerCapturer(lineup_processor, controller)
    cheer_result = cheer_capturer.process()
    images = [cheer_result.left_user.team_image, cheer_result.right_user.team_image]
    final_images = combine_images(60, 80, images)
    save_dir = "testdata/cheer_capturer"
    os.makedirs(save_dir, exist_ok=True)
    final_images.save("testdata/cheer_capturer/combined.png")

import logging
import os

from collector.group_processor import GroupProcessor
from tests.collector.utils import keyboard_terminable

logger = logging.getLogger(__name__)


@keyboard_terminable()
def test_group_processor(group_processor: GroupProcessor):
    group = group_processor.process()
    save_dir = "testdata/group_processor"
    assert group is not None
    group.save_combined_image(os.path.join(save_dir, "combined.png"))
    group.save_result_image(os.path.join(save_dir, "result.png"))
    group.save_as_json(os.path.join(save_dir, "data.json"))
    for user in group.users:
        for _round in user.rounds.values():
            path = os.path.join(save_dir, f"user_{user.user_id}", f"round_{_round.round_index}")
            _round.save_character_images(path)

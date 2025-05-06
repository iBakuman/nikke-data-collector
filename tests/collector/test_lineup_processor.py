import pytest

from collector.lineup_processor import LineupProcessor
from tests.collector.utils import keyboard_terminable


@keyboard_terminable()
def test_lineup_processor(lineup_processor: LineupProcessor):
    user = lineup_processor.process()
    user.save_team_image("testdata/lineup_processor")
    for _round in user.rounds.values():
        print(_round)
        _round.save_character_images(f"testdata/lineup_processor/round_{_round.round_index}")

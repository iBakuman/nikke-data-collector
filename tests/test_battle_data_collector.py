from collector.battle_data_collector import BattleDataCollector
from tests.utils import keyboard_terminable


@keyboard_terminable()
def test_battle_result_collector(battle_data_collector: BattleDataCollector):
    battle_data = battle_data_collector.collect_battle()
    assert battle_data.left_user_id is not None
    assert battle_data.right_user_id is not None
    assert battle_data.result is not None
    battle_data.save_image("testdata/battle_collector/battle_result.png")
    battle_data.save_as_json("testdata/battle_collector/battle_result.json")
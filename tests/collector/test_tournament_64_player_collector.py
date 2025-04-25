from collector.tournament_64_player_collector import Tournament64PlayerCollector


def test_tournament_64_player_collector(player_collector: Tournament64PlayerCollector):
    assert player_collector.collect_group(1) is not None

def test_tournament_64_player_collector_collect_all_groups(player_collector: Tournament64PlayerCollector):
    assert player_collector.collect_all_groups() is not None


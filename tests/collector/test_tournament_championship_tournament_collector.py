from collector.models import TournamentStage
from collector.tournament_championship_collector import ChampionshipTournamentCollector
from tests.collector.utils import keyboard_terminable


@keyboard_terminable()
def test_championship_tournament_collector(championship_collector: ChampionshipTournamentCollector):
    for stage in [TournamentStage.STAGE_8_4, TournamentStage.STAGE_4_2, TournamentStage.STAGE_2_1]:
        championship_collector.collect_stage(stage)


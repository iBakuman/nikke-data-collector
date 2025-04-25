from collector.models import TournamentStage
from collector.tournament_championship_collector import ChampionshipTournamentCollector
from tests.utils import keyboard_terminable


@keyboard_terminable()
def test_championship_tournament_collector(championship_collector: ChampionshipTournamentCollector):
    championship_collector.collect_stage(TournamentStage.STAGE_4_2)


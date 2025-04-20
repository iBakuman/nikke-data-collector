from nikke_arena.models import TournamentStage
from nikke_arena.tournament_championship_collector import ChampionshipTournamentCollector
from tests.utils import keyboard_terminable


# @pytest.mark.gap(200)
@keyboard_terminable()
def test_championship_tournament_collector(championship_collector: ChampionshipTournamentCollector):
    championship_collector.collect_stage(TournamentStage.STAGE_2_1)


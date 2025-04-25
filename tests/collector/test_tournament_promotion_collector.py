from src.collector.models import TournamentStage
from src.collector.tournament_promotion_collector import \
    PromotionDataCollector
from tests.collector.utils import keyboard_terminable


@keyboard_terminable()
def test_promotion_tournament_collector(promotion_collector: PromotionDataCollector):
    promotion_collector.collect_stage(TournamentStage.STAGE_16_8, [1])

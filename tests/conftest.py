import pytest

from nikke_arena.battle_data_collector import BattleDataCollector
from nikke_arena.character_matcher import CharacterMatcher
from nikke_arena.db.character_dao import CharacterDAO
from nikke_arena.delay_manager import DelayManager
from nikke_arena.group_processor import GroupProcessor
from nikke_arena.image_detector import ImageDetector
from nikke_arena.lineup_processor import LineupProcessor
from nikke_arena.mouse_control import MouseController
from nikke_arena.profile_collector import ProfileCollector
from nikke_arena.tournament_64_player_collector import Tournament64PlayerCollector
from nikke_arena.tournament_championship_collector import \
    ChampionshipTournamentCollector
from nikke_arena.tournament_group_collector import GroupDataCollector
from nikke_arena.tournament_promotion_collector import \
    PromotionDataCollector
from nikke_arena.tournament_recorder import TournamentRecorder
from nikke_arena.ui_def import STANDARD_WINDOW_HEIGHT, STANDARD_WINDOW_WIDTH
from nikke_arena.window_capturer import WindowCapturer
from nikke_arena.window_manager import WindowManager
from nikke_arena.window_recorder import Quality, WindowRecorder


@pytest.fixture
def delay_manager() -> DelayManager:
    return DelayManager(1.6, 2.1)


@pytest.fixture
def capturer(manager) -> WindowCapturer:
    capturer = WindowCapturer(manager)
    return capturer


@pytest.fixture
def controller(manager) -> MouseController:
    return MouseController(manager)


@pytest.fixture
def manager(request):
    marker = request.node.get_closest_marker("width")
    width = 3580
    if marker and marker.args:
        width = marker.args[0]
    manager = WindowManager("nikke.exe", STANDARD_WINDOW_WIDTH, STANDARD_WINDOW_HEIGHT)
    manager.resize_to_standard(width=width, position="top-left")
    return manager


@pytest.fixture
def image_detector(capturer, manager) -> ImageDetector:
    return ImageDetector(capturer, manager, debug_path="testdata/detector")


@pytest.fixture
def recorder(manager: WindowManager) -> WindowRecorder:
    return WindowRecorder(manager, quality=Quality.SLOW)


@pytest.fixture
def tournament_recorder(manager: WindowManager, controller: MouseController,
                        image_detector: ImageDetector, recorder: WindowRecorder) -> TournamentRecorder:
    return TournamentRecorder(manager, controller, image_detector, recorder)

@pytest.fixture
def character_dao() -> CharacterDAO:
    return CharacterDAO()


@pytest.fixture
def matcher() -> CharacterMatcher:
    return CharacterMatcher(
        cache_dir="testdata/matcher/cache",
        character_dao=CharacterDAO(),
        cache_size_limit=int(2e9)
    )

@pytest.fixture
def profile_collector(capturer: WindowCapturer, controller: MouseController) -> ProfileCollector:
    return ProfileCollector(controller, capturer)

@pytest.fixture
def lineup_processor(capturer: WindowCapturer, controller: MouseController,
                     matcher: CharacterMatcher, profile_collector: ProfileCollector) -> LineupProcessor:
    return LineupProcessor(controller, capturer, profile_collector, matcher=matcher)


@pytest.fixture
def battle_data_collector(image_detector: ImageDetector, controller: MouseController,
                          capturer: WindowCapturer) -> BattleDataCollector:
    return BattleDataCollector(image_detector, controller, capturer)


@pytest.fixture
def promotion_collector(capturer: WindowCapturer, controller: MouseController,
                        image_detector: ImageDetector) -> PromotionDataCollector:
    return PromotionDataCollector(capturer, controller, image_detector, "testdata/collector")


@pytest.fixture
def championship_collector(capturer: WindowCapturer, controller: MouseController,
                           image_detector: ImageDetector) -> ChampionshipTournamentCollector:
    return ChampionshipTournamentCollector(capturer, controller, image_detector,
                                           "testdata/collector")

@pytest.fixture
def player_collector(controller: MouseController, lineup_processor: LineupProcessor) -> Tournament64PlayerCollector:
    return Tournament64PlayerCollector(controller, lineup_processor,"testdata/collector")

@pytest.fixture
def group_processor(controller: MouseController,capturer: WindowCapturer,lineup_processor: LineupProcessor) -> GroupProcessor:
    return GroupProcessor(controller, capturer, lineup_processor)

@pytest.fixture
def group_collector(capturer: WindowCapturer, controller: MouseController,group_processor: GroupProcessor) -> GroupDataCollector:
    return GroupDataCollector(capturer, controller, group_processor,
                              "testdata/collector/groups")


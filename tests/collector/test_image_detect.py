import logging

from collector.image_detector import ImageDetector
from collector.ui_def import PROMOTION_TOURNAMENT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_detect_image(image_detector: ImageDetector) -> None:
    assert image_detector.detect_image(PROMOTION_TOURNAMENT.CHEER_IMAGE) is not None

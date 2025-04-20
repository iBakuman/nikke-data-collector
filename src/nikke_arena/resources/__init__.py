import sys
from pathlib import Path

from nikke_arena.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    'RESOURCE_DIR',
    'get_detectable_image_path',
    'get_ref_images_dir'
]


# Base directory for resources depends on whether app is frozen (packaged)
def _get_base_dir() -> Path:
    """
    Get the base directory for resources, handling both packaged and development environments

    Returns:
        Path to the base resources directory
    """
    if getattr(sys, 'frozen', False):
        logger.info("App is packaged, detecting resources directory")
        meipass_attr = getattr(sys, '_MEIPASS', None)
        if meipass_attr is not None:  # PyInstaller
            logger.info(f"PyInstaller detected, using resources at: {Path(meipass_attr) / 'src' / 'nikke_arena' / 'resources'}")
            return Path(meipass_attr) / "src" / "nikke_arena" / "resources"
        executable_path = Path(sys.argv[0])
        logger.info(f"executable_path: {executable_path}")
        if executable_path.exists():
            logger.info(f"executable_path detected, using resources at: {executable_path.parent / 'resources'}")
            return executable_path.parent / "resources"
        raise Exception("Resources directory not found in packaged mode")

    logger.info(f"using module's directory: {Path(__file__).parent}")
    return Path(__file__).parent


# Initialize resource directory with proper detection
RESOURCE_DIR = _get_base_dir()
logger.info(f"Resource directory: {RESOURCE_DIR}")
logo_path = RESOURCE_DIR / "logo.ico"
logger.info(f"Logo path: {logo_path}")


# Make resources directory structure visible
def get_detectable_image_path(image_name: str) -> str:
    """
    Get absolute path for an image in the resources/detectable directory

    Args:
        image_name: Image filename

    Returns:
        Absolute path to the image as string
    """
    path = RESOURCE_DIR / "detectable" / image_name
    return str(path)


def get_ref_images_dir() -> str:
    """
    Get the path to the reference images directory.

    Returns:
        The path to the reference images directory as string
    """
    path = RESOURCE_DIR / 'ref'
    return str(path)
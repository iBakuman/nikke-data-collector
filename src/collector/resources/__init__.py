import os
import sys
from pathlib import Path

__all__ = [
    'RESOURCE_DIR',
    'logo_path'
]


# Base directory for resources depends on whether app is frozen (packaged)
def _get_base_dir() -> Path:
    """
    Get the base directory for resources, handling both packaged and development environments

    Returns:
        Path to the base resources directory
    """
    if "NUITKA_ONEFILE_PARENT" in os.environ:
        print("App is packaged, detecting resources directory")
        print(f"sys.executable: {sys.executable}")
        print(f"sys.argv: {sys.argv}")
        print(f"cwd: {os.getcwd()}")
        return Path(sys.executable).parent / "resources"
    else:
        print(f"using module's directory: {Path(__file__).parent}")
        return Path(__file__).parent


# Initialize resource directory with proper detection
RESOURCE_DIR = _get_base_dir()
print(f"Resource directory: {RESOURCE_DIR}")
logo_path = RESOURCE_DIR / "logo.ico"
print(f"Logo path: {logo_path}")

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

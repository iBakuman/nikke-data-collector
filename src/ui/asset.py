from importlib.resources import files
from pathlib import Path


def get_translation_file(language_code: str) -> str:
    """Get the path to a translation file based on language code.
    
    Args:
        language_code: The language code (e.g., 'en_US', 'zh_CN')
        
    Returns:
        Path to the translation file as string
    """
    return str(files("ui.translations").joinpath(f"app_{language_code}.qm"))

def get_translation_path() -> Path:
    """Get the path to the translations directory.
    
    Returns:
        Path object to the translations directory
    """
    return Path(files("ui.translations").joinpath(""))

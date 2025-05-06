"""UI module for the Nikke Data Collector application."""

from importlib.resources import files
from pathlib import Path

from ui.character_extractor_ui import CharacterExtractorApp

# Get the resource directory for UI resources
RESOURCE_DIR = Path(files("ui").joinpath(""))

__all__ = ["CharacterExtractorApp"]

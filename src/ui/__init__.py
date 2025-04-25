from importlib.resources import files
from pathlib import Path

# Get the resource directory for UI resources
RESOURCE_DIR = Path(files("ui").joinpath(""))

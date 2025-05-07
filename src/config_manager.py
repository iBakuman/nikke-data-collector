"""
Configuration Manager

Handles reading and writing configuration files in platform-specific locations
"""

from typing import Any, Dict

from collector.logging_config import get_logger
from config.config_manager import ConfigManager

logger = get_logger(__name__)


class AppConfigManager(ConfigManager):
    """
    Manages application configuration using platform-specific directories.

    Handles reading and writing configuration files to the appropriate
    user config directory for each platform.
    """

    def __init__(self, config_name: str = "settings.json"):
        """
        Initialize the config manager.

        Args:
            config_name: Name of the configuration file
        """
        super().__init__("nikke-data-collector", "iBakuman", config_name)

    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration"""
        return {
            "delay": {
                "min": 1.5,
                "max": 2.0
            },
            "last_save_dir": "",
            "show_time_warning": True,
        }

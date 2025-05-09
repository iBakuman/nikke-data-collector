from typing import Dict, Any

from config import ConfigManager


class AppConfigManager(ConfigManager):
    def __init__(self):
        super().__init__("extractor", "iBakuman")
    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration"""
        return {
            "output_dir": "",
            "version": "1.0.0"
        }
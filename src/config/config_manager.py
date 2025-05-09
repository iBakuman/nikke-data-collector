import json
import os
from abc import abstractmethod
from typing import Dict, Any

import appdirs

import log.config

logger = log.config.get_logger(__name__)

class ConfigManager:
    """
    Manages application configuration using platform-specific directories.

    Handles reading and writing configuration files to the appropriate
    user config directory for each platform.
    """

    def __init__(self, app_name: str, app_author: str, config_name: str = "settings.json"):
        """
        Initialize the config manager.

        Args:
            app_name: Name of the application
            app_author: Author of the application
            config_name: Name of the configuration file
        """
        self.cache_dir = appdirs.user_cache_dir(app_name, app_author)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.log_dir = appdirs.user_log_dir(app_name, app_author)
        os.makedirs(self.log_dir, exist_ok=True)
        self.config_dir = appdirs.user_config_dir(app_name, app_author)
        os.makedirs(self.config_dir, exist_ok=True)

        self.config_path = os.path.join(self.config_dir, config_name)
        self.config = self.get_default_config()
        # Load existing configuration if available
        self.load_config()

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration"""
        ...

    def load_config(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # Update config with loaded values, preserving defaults for missing keys
                self._merge_configs(self.config, loaded_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.info(f"No configuration file found at {self.config_path}, using defaults")
                self.save_config()  # Save the default config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

        return self.config

    def save_config(self) -> bool:
        """
        Save current configuration to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value if key doesn't exist

        Returns:
            The configuration value or default
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        # Navigate to the deepest dict
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def update(self, values: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.

        Args:
            values: Dictionary of values to update
        """
        self._merge_configs(self.config, values)

    @staticmethod
    def _merge_configs(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge source config into target config.

        Args:
            target: Target configuration dict to update
            source: Source configuration dict with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively update nested dicts
                ConfigManager._merge_configs(target[key], value)
            else:
                # Update or add value
                target[key] = value

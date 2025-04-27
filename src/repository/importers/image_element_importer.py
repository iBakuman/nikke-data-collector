"""
ImageElement data importer.

This module provides importers for ImageElement objects from various sources.
"""

import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from domain.image_element import ImageElement
from log.config import get_logger
from .base_importer import DataImporter

logger = get_logger(__name__)


class ImageElementImporter(DataImporter[ImageElement]):
    """Importer for ImageElement data from files and directories."""

    def __init__(self, default_threshold: float = 0.8):
        """Initialize the importer.
        
        Args:
            default_threshold: Default detection threshold if not specified in config
        """
        self.default_threshold = default_threshold

    def import_from_directory(self, directory_path: str) -> List[ImageElement]:
        """Import all image elements from a directory.
        
        Looks for images and an optional config.json file that contains region info.
        
        Args:
            directory_path: Path to directory containing images and config
            
        Returns:
            List of imported ImageElement objects
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory does not exist: {directory_path}")
            return []

        # Try to load config file if it exists
        config_file = directory / "config.json"
        config_data = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse config file: {config_file}")
            except Exception as e:
                logger.error(f"Error reading config file: {e}")

        # Find all image files in the directory
        result = []
        image_files = [f for f in directory.glob("*")
                       if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']]

        for image_file in image_files:
            # Get image-specific config if available
            image_name = image_file.stem
            image_config = config_data.get(image_name, {})

            try:
                # Import the image element
                dto = self._import_image_file(image_file, image_config)
                if dto:
                    result.append(dto)
            except Exception as e:
                logger.error(f"Failed to import image {image_file}: {e}")

        return result

    def import_from_file(self, file_path: str) -> List[ImageElement]:
        """Import a single image element from a file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            List containing a single ImageElement or empty if failed
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File does not exist: {file_path}")
            return []

        # Check if a matching config JSON exists
        config_path = path.with_suffix('.json')
        config_data = {}
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse config file: {config_path}")
            except Exception as e:
                logger.error(f"Error reading config file: {e}")

        try:
            dto = self._import_image_file(path, config_data)
            return [dto] if dto else []
        except Exception as e:
            logger.error(f"Failed to import image {file_path}: {e}")
            return []

    def import_from_json(self, json_path: str) -> List[ImageElement]:
        """Import image elements from a JSON configuration.
        
        The JSON should contain a list of objects with 'image_path' and other properties.
        
        Args:
            json_path: Path to the JSON configuration file
            
        Returns:
            List of imported ImageElement objects
        """
        json_file = Path(json_path)
        if not json_file.exists():
            logger.error(f"JSON file does not exist: {json_path}")
            return []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON file: {json_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            return []

        result = []
        base_dir = json_file.parent

        # Handle both list and dict formats
        if isinstance(config, list):
            items = config
        elif isinstance(config, dict):
            items = [{"name": name, **data} for name, data in config.items()]
        else:
            logger.error(f"Invalid JSON format in {json_path}, expected list or dict")
            return []

        for item in items:
            image_path = item.get('image_path')
            if not image_path:
                logger.warning(f"Missing image_path in item: {item}")
                continue

            # Resolve image path (absolute or relative to JSON file)
            img_path = Path(image_path)
            if not img_path.is_absolute():
                img_path = base_dir / img_path

            if not img_path.exists():
                logger.error(f"Image file does not exist: {img_path}")
                continue

            try:
                dto = self._import_image_file(img_path, item)
                if dto:
                    result.append(dto)
            except Exception as e:
                logger.error(f"Failed to import image {img_path}: {e}")

        return result

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'json']

    def _import_image_file(self, image_path: Path, config: Dict[str, Any]) -> Optional[ImageElement]:
        """Internal helper to import a single image file with config.
        
        Args:
            image_path: Path to the image file
            config: Configuration data for the image
            
        Returns:
            ImageElement instance or None if import failed
        """
        try:
            # Load the image
            with Image.open(image_path) as img:
                # Convert image to binary data
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                image_data = img_byte_arr.getvalue()

                # Get image dimensions
                width, height = img.size

            # Extract region information from config or use defaults
            name = config.get('name', image_path.stem)
            region_x = config.get('region_x', 0)
            region_y = config.get('region_y', 0)
            region_width = config.get('region_width', width)
            region_height = config.get('region_height', height)
            region_total_width = config.get('region_total_width', width)
            region_total_height = config.get('region_total_height', height)
            threshold = config.get('threshold', self.default_threshold)

            # Create the DTO
            return ImageElement(
                name=name,
                region_x=region_x,
                region_y=region_y,
                region_width=region_width,
                region_height=region_height,
                region_total_width=region_total_width,
                region_total_height=region_total_height,
                image_data=image_data,
                threshold=threshold
            )
        except Exception as e:
            logger.error(f"Error importing image {image_path}: {e}")
            return None

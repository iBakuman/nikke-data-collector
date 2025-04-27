"""
Character data importer.

This module provides importers for Character objects from various sources.
"""

import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from domain.character import Character, ChargeValues, WeaponType
from log.config import get_logger
from .base_importer import DataImporter
from .. import CharacterDAO

logger = get_logger(__name__)

class CharacterImporter(DataImporter[Character]):
    def __init__(self, character_dao: CharacterDAO):
        self.character_dao = character_dao

    """Importer for Character data from files and directories."""
    def import_from_directory(self, directory_path: str, pattern=r"^(\d{3})_([^_]+)_[a-z]\.(?:png|jpg|jpeg)$") -> List[Character]:
        for filename in os.listdir(directory_path):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            # Extract ID and name using regex
            match = re.match(pattern, filename)
            if not match:
                # Try alternative pattern without letter suffix
                match = re.match(r"^(\d{3})_([^_]+)\.(?:png|jpg|jpeg)$", filename)
                if not match:
                    logger.warning(f"Skipping file with unrecognized format: {filename}")
                    continue

            char_id = match.group(1)
            char_name = match.group(2)

            # Check if character exists, if not create it
            char = self.character_dao.get_character(char_id)
            if not char:
                self.character_dao.add_character(char_id,chinese_name=char_name)

            # Add the image
            image_path = os.path.join(directory_path, filename)
            success = self.character_dao.add_character_image(char_id, image_path)

            if success:
                count += 1
        logger.info(f"Successfully imported {count} images into the database")
        return count

    def import_from_file(self, file_path: str) -> List[Character]:
        """Import character data from a file.

        Args:
            file_path: Path to the file containing character data

        Returns:
            List of imported Character objects
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File does not exist: {file_path}")
            return []

        # Handle based on file type
        suffix = path.suffix.lower()
        if suffix == '.json':
            return self.import_from_json(file_path)
        elif suffix == '.csv':
            return self._import_from_csv(path)
        else:
            logger.error(f"Unsupported file format for character import: {suffix}")
            return []

    def import_from_json(self, json_path: str) -> List[Character]:
        """Import character data from a JSON file.

        The JSON can be either:
        1. A list of character objects
        2. A dictionary with character IDs as keys

        Args:
            json_path: Path to the JSON file

        Returns:
            List of imported Character objects
        """
        json_file = Path(json_path)
        if not json_file.exists():
            logger.error(f"JSON file does not exist: {json_path}")
            return []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON file: {json_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            return []

        result = []

        # Handle different JSON formats
        if isinstance(data, list):
            # List of character objects
            for item in data:
                try:
                    char = self._create_character_from_dict(item)
                    if char:
                        result.append(char)
                except Exception as e:
                    logger.error(f"Error creating character from JSON item: {e}")
        elif isinstance(data, dict):
            # Dictionary with character IDs as keys
            for char_id, char_data in data.items():
                try:
                    # Ensure ID is in the data
                    if isinstance(char_data, dict):
                        char_data['id'] = char_data.get('id', char_id)
                        char = self._create_character_from_dict(char_data)
                        if char:
                            result.append(char)
                except Exception as e:
                    logger.error(f"Error creating character from JSON item: {e}")
        else:
            logger.error(f"Invalid JSON format in {json_path}, expected list or dict")

        return result

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats.

        Returns:
            List of supported file extensions
        """
        return ['json', 'csv']

    def _import_from_csv(self, csv_path: Path) -> List[Character]:
        """Import character data from a CSV file.

        Args:
            csv_path: Path to the CSV file

        Returns:
            List of imported Character objects
        """
        if not csv_path.exists():
            logger.error(f"CSV file does not exist: {csv_path}")
            return []

        result = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        char = self._create_character_from_dict(row)
                        if char:
                            result.append(char)
                    except Exception as e:
                        logger.error(f"Error creating character from CSV row: {e}")
        except Exception as e:
            logger.error(f"Error reading CSV file {csv_path}: {e}")

        return result

    def _create_character_from_dict(self, data: Dict[str, Any]) -> Optional[Character]:
        """Create a Character object from dictionary data.

        Args:
            data: Dictionary containing character data

        Returns:
            Character object or None if creation failed
        """
        try:
            # Extract required fields
            char_id = data.get('id')
            if not char_id:
                logger.warning("Character data missing required 'id' field")
                return None

            name = data.get('name', char_id)
            position = int(data.get('position', 0))

            # Create the character
            character = Character(
                id=char_id,
                name=name,
                position=position
            )

            # Add optional fields if present
            if 'weapon_type' in data:
                weapon_str = data['weapon_type']
                try:
                    character.weapon_type = WeaponType[weapon_str]
                except KeyError:
                    # Try to match by value
                    for wt in WeaponType:
                        if wt.value == weapon_str:
                            character.weapon_type = wt
                            break

            # Handle charge values if present
            if all(k in data for k in ['extreme_speed', 'high_speed', 'sg5', 'sg7']):
                character.charge_values = ChargeValues(
                    extreme_speed=float(data['extreme_speed']),
                    high_speed=float(data['high_speed']),
                    sg5=float(data['sg5']),
                    sg7=float(data['sg7'])
                )

            # Load image if path provided
            image_path = data.get('image_path')
            if image_path:
                img_path = Path(image_path)
                if img_path.exists():
                    character.image = Image.open(img_path)

            return character
        except Exception as e:
            logger.error(f"Error creating character from data: {e}")
            return None

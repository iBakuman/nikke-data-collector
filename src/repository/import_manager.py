"""
Import Manager for coordinating data import operations.

This module provides a centralized manager for importing data from various
sources into the application's database.
"""

from pathlib import Path
from typing import Any, Dict, List

from log.config import get_logger
from .character_dao import CharacterDAO
from .image_element_dao import ImageElementDAO
from .importers.base_importer import DataImporter
from .importers.character_importer import CharacterImporter
from .importers.image_element_importer import ImageElementImporter

logger = get_logger(__name__)


class ImportManager:
    """Central manager for data import operations.
    
    This class coordinates the import of different data types from various sources
    and handles saving imported data to the database.
    """

    def __init__(self):
        """Initialize the import manager with default importers."""
        # Initialize default importers
        self._importers: Dict[str, DataImporter] = {
            'character': CharacterImporter(),
            'image_element': ImageElementImporter()
        }

        # Initialize repositories
        self._character_repo = CharacterDAO()
        self._image_element_repo = ImageElementDAO()

    def register_importer(self, data_type: str, importer: DataImporter) -> None:
        """Register a new importer for a data type.
        
        Args:
            data_type: Identifier for the data type
            importer: DataImporter instance for this data type
        """
        self._importers[data_type] = importer
        logger.info(f"Registered importer for data type: {data_type}")

    def import_data(self, data_type: str, source_path: str, save_to_db: bool = True) -> List[Any]:
        """Import data from a source and optionally save to database.
        
        Args:
            data_type: Type of data to import (must match a registered importer)
            source_path: Path to the source file or directory
            save_to_db: Whether to save imported data to the database
            
        Returns:
            List of imported data objects
            
        Raises:
            ValueError: If data_type is not supported or source_path is invalid
        """
        if data_type not in self._importers:
            raise ValueError(f"Unsupported data type: {data_type}")

        path = Path(source_path)
        if not path.exists():
            raise ValueError(f"Source path does not exist: {source_path}")

        importer = self._importers[data_type]
        imported_data = []

        # Import based on path type
        if path.is_dir():
            logger.info(f"Importing {data_type} data from directory: {source_path}")
            imported_data = importer.import_from_directory(source_path)
        else:
            # Determine import method based on file extension
            ext = path.suffix.lower()[1:]  # Remove the dot
            if ext == 'json':
                logger.info(f"Importing {data_type} data from JSON: {source_path}")
                imported_data = importer.import_from_json(source_path)
            elif importer.can_handle_file(source_path):
                logger.info(f"Importing {data_type} data from file: {source_path}")
                imported_data = importer.import_from_file(source_path)
            else:
                raise ValueError(f"Unsupported file format: {ext} for data type: {data_type}")

        # Save imported data if requested
        if save_to_db and imported_data:
            saved_count = self._save_to_database(data_type, imported_data)
            logger.info(f"Saved {saved_count} {data_type} items to database")

        return imported_data

    def import_all_from_directory(self, directory_path: str, save_to_db: bool = True) -> Dict[str, List[Any]]:
        """Import all supported data types from a directory structure.
        
        This method scans a directory for subdirectories that match registered data types
        and imports data from each of them.
        
        Args:
            directory_path: Path to the base directory
            save_to_db: Whether to save imported data to the database
            
        Returns:
            Dictionary mapping data types to lists of imported objects
        """
        base_dir = Path(directory_path)
        if not base_dir.exists() or not base_dir.is_dir():
            raise ValueError(f"Base directory does not exist: {directory_path}")

        result = {}

        # First check if importers have dedicated subdirectories
        for data_type in self._importers:
            type_dir = base_dir / data_type
            if type_dir.exists() and type_dir.is_dir():
                logger.info(f"Found dedicated directory for {data_type}: {type_dir}")
                try:
                    imported_data = self.import_data(data_type, str(type_dir), save_to_db)
                    result[data_type] = imported_data
                except Exception as e:
                    logger.error(f"Error importing {data_type} from {type_dir}: {e}")

        # Then look for supported files in the base directory
        for item in base_dir.iterdir():
            if item.is_file():
                ext = item.suffix.lower()[1:]  # Remove the dot
                for data_type, importer in self._importers.items():
                    if ext in importer.get_supported_formats():
                        # Skip if we already processed this data type from a dedicated directory
                        if data_type in result:
                            continue

                        logger.info(f"Found file for {data_type}: {item}")
                        try:
                            imported_data = self.import_data(data_type, str(item), save_to_db)
                            result[data_type] = imported_data
                        except Exception as e:
                            logger.error(f"Error importing {data_type} from {item}: {e}")

        return result

    def _save_to_database(self, data_type: str, items: List[Any]) -> int:
        """Save imported items to the database.
        
        Args:
            data_type: Type of data being saved
            items: List of items to save
            
        Returns:
            Number of items successfully saved
        """
        saved_count = 0

        if data_type == 'character':
            for char in items:
                try:
                    # For character, we need to handle both the character data and image
                    success = self._character_repo.add_character(
                        character_id=char.id,
                        chinese_name="",  # Set appropriate values based on available data
                        english_name=char.name
                    )

                    # If character has an image, save it too
                    if success and char.image:
                        self._character_repo.add_character_image(char.id, char.image)

                    if success:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving character {char.id}: {e}")

        elif data_type == 'image_element':
            for element in items:
                try:
                    saved = self._image_element_repo.save(element)
                    if saved:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving image element {element.name}: {e}")

        else:
            logger.warning(f"No save handler implemented for data type: {data_type}")

        return saved_count

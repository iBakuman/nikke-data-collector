"""
Data Access Object for ImageElement.

This module provides database operations for ImageElement entities.
"""

from typing import List, Optional

from domain.image_element import ImageElementEntity
from log.config import get_logger
from .connection import get_db_connection

logger = get_logger(__name__)

class ImageElementDAO:
    """Data Access Object for ImageElement entities."""

    @staticmethod
    def create_table() -> None:
        """Create the image_elements table if it doesn't exist."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                region_x INTEGER NOT NULL,
                region_y INTEGER NOT NULL,
                region_width INTEGER NOT NULL,
                region_height INTEGER NOT NULL,
                region_total_width INTEGER NOT NULL,
                region_total_height INTEGER NOT NULL,
                image_data BLOB NOT NULL,
                threshold REAL NOT NULL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

    @staticmethod
    def save(element: ImageElementEntity) -> ImageElementEntity:
        """Save an ImageElement to the database.

        Args:
            element: The ImageElement to save

        Returns:
            The saved ImageElement with ID populated
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if element.id is None:
                # Insert new record
                cursor.execute('''
                INSERT INTO image_elements (
                    name, region_x, region_y, region_width, region_height,
                    region_total_width, region_total_height, image_data, threshold
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    element.name, element.region_x, element.region_y, element.region_width,
                    element.region_height, element.region_total_width, element.region_total_height,
                    element.image_data, element.threshold
                ))
                element.id = cursor.lastrowid
            else:
                # Update existing record
                cursor.execute('''
                UPDATE image_elements SET
                    name = ?, region_x = ?, region_y = ?, region_width = ?,
                    region_height = ?, region_total_width = ?, region_total_height = ?,
                    image_data = ?, threshold = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (
                    element.name, element.region_x, element.region_y, element.region_width,
                    element.region_height, element.region_total_width, element.region_total_height,
                    element.image_data, element.threshold, element.id
                ))

            return element

    @staticmethod
    def find_by_id(element_id: int) -> Optional[ImageElementEntity]:
        """Find an ImageElement by its ID.

        Args:
            element_id: The ID of the ImageElement to find

        Returns:
            The ImageElement if found, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, name, region_x, region_y, region_width, region_height,
                region_total_width, region_total_height, image_data, threshold,
                created_at, updated_at
            FROM image_elements
            WHERE id = ?
            ''', (element_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return ImageElementDAO.row_to_element(row)

    @staticmethod
    def find_by_name(name: str) -> Optional[ImageElementEntity]:
        """Find an ImageElement by its name.

        Args:
            name: The name of the ImageElement to find

        Returns:
            The ImageElement if found, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, name, region_x, region_y, region_width, region_height,
                region_total_width, region_total_height, image_data, threshold,
                created_at, updated_at
            FROM image_elements
            WHERE name = ?
            ''', (name,))

            row = cursor.fetchone()
            if not row:
                return None

            return ImageElementDAO.row_to_element(row)

    @staticmethod
    def find_all() -> List[ImageElementEntity]:
        """Find all ImageElements in the database.

        Returns:
            List of all ImageElements
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, name, region_x, region_y, region_width, region_height,
                region_total_width, region_total_height, image_data, threshold,
                created_at, updated_at
            FROM image_elements
            ''')

            rows = cursor.fetchall()
            return [ImageElementDAO.row_to_element(row) for row in rows]

    @staticmethod
    def delete(element_id: int) -> bool:
        """Delete an ImageElement by its ID.

        Args:
            element_id: The ID of the ImageElement to delete

        Returns:
            True if successful, False otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM image_elements WHERE id = ?', (element_id,))
            return cursor.rowcount > 0

    @staticmethod
    def row_to_element(row) -> ImageElementEntity:
        """Convert a database row to an ImageElement.

        Args:
            row: Database row (as a dict-like object)

        Returns:
            ImageElement instance
        """
        return ImageElementEntity(
            id=row['id'],
            name=row['name'],
            region_x=row['region_x'],
            region_y=row['region_y'],
            region_width=row['region_width'],
            region_height=row['region_height'],
            region_total_width=row['region_total_width'],
            region_total_height=row['region_total_height'],
            image_data=row['image_data'],
            threshold=row['threshold'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

"""
Data Access Object for PixelColorElement.

This module provides database operations for PixelColorElement entities.
"""

from typing import List, Optional

from domain.pixel_element import PixelColorElementEntity
from log.config import get_logger
from .connection import get_db_connection

logger = get_logger(__name__)

class PixelColorElementDAO:
    """Data Access Object for PixelColorElement entities."""

    @staticmethod
    def create_table() -> None:
        """Create the pixel_color_elements table if it doesn't exist."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pixel_color_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                points_colors_json TEXT NOT NULL,
                tolerance INTEGER NOT NULL DEFAULT 10,
                match_all BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            conn.commit()

    @staticmethod
    def save(element: PixelColorElementEntity) -> PixelColorElementEntity:
        """Save a PixelColorElement to the database.

        Args:
            element: The PixelColorElement to save

        Returns:
            The saved PixelColorElement with ID populated
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if element.id is None:
                # Insert new record
                cursor.execute('''
                INSERT INTO pixel_color_elements (
                    name, points_colors_json, tolerance, match_all
                ) VALUES (?, ?, ?, ?)
                ''', (
                    element.name, element.points_colors_json, 
                    element.tolerance, element.match_all
                ))
                element.id = cursor.lastrowid
            else:
                # Update existing record
                cursor.execute('''
                UPDATE pixel_color_elements SET
                    name = ?, points_colors_json = ?, tolerance = ?, 
                    match_all = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (
                    element.name, element.points_colors_json,
                    element.tolerance, element.match_all, element.id
                ))

            conn.commit()
            return element

    @staticmethod
    def find_by_id(element_id: int) -> Optional[PixelColorElementEntity]:
        """Find a PixelColorElement by its ID.

        Args:
            element_id: The ID of the PixelColorElement to find

        Returns:
            The PixelColorElement if found, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, name, points_colors_json, tolerance, match_all,
                created_at, updated_at
            FROM pixel_color_elements
            WHERE id = ?
            ''', (element_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return PixelColorElementDAO.row_to_element(row)

    @staticmethod
    def find_by_name(name: str) -> Optional[PixelColorElementEntity]:
        """Find a PixelColorElement by its name.

        Args:
            name: The name of the PixelColorElement to find

        Returns:
            The PixelColorElement if found, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, name, points_colors_json, tolerance, match_all,
                created_at, updated_at
            FROM pixel_color_elements
            WHERE name = ?
            ''', (name,))

            row = cursor.fetchone()
            if not row:
                return None

            return PixelColorElementDAO.row_to_element(row)

    @staticmethod
    def find_all() -> List[PixelColorElementEntity]:
        """Find all PixelColorElements in the database.

        Returns:
            List of all PixelColorElements
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, name, points_colors_json, tolerance, match_all,
                created_at, updated_at
            FROM pixel_color_elements
            ''')

            rows = cursor.fetchall()
            return [PixelColorElementDAO.row_to_element(row) for row in rows]

    @staticmethod
    def delete(element_id: int) -> bool:
        """Delete a PixelColorElement by its ID.

        Args:
            element_id: The ID of the PixelColorElement to delete

        Returns:
            True if successful, False otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('DELETE FROM pixel_color_elements WHERE id = ?', (element_id,))
            conn.commit()

            return cursor.rowcount > 0

    @staticmethod
    def row_to_element(row) -> PixelColorElementEntity:
        """Convert a database row to a PixelColorElement.

        Args:
            row: Database row (as a dict-like object)

        Returns:
            PixelColorElement instance
        """
        return PixelColorElementEntity(
            id=row['id'],
            name=row['name'],
            points_colors_json=row['points_colors_json'],
            tolerance=row['tolerance'],
            match_all=bool(row['match_all']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) 

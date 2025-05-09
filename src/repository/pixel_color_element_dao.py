"""
Data Access Object for PixelColorElement.

This module provides database operations for PixelColorElement entities.
"""

from typing import List, Optional

from domain.pixel_element import PixelColorElementEntity, PixelColorPointEntity
from log.config import get_logger
from repository.base_dao import BaseDAO
from repository.decorator import db_operation

logger = get_logger(__name__)

class PixelColorElementDAO(BaseDAO):
    """Data Access Object for PixelColorElement entities."""

    @db_operation()
    def create_table(self) -> None:
        """Create the pixel_color_elements and pixel_color_points tables if they don't exist."""
        def create_tables(conn):
            cursor = conn.cursor()

            # Create main element table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pixel_color_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tolerance INTEGER NOT NULL DEFAULT 10,
                match_all BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Create points table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pixel_color_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_id INTEGER NOT NULL,
                point_x INTEGER NOT NULL,
                point_y INTEGER NOT NULL,
                total_width INTEGER NOT NULL,
                total_height INTEGER NOT NULL,
                color_r INTEGER NOT NULL,
                color_g INTEGER NOT NULL,
                color_b INTEGER NOT NULL,
                FOREIGN KEY (element_id) REFERENCES pixel_color_elements (id) ON DELETE CASCADE
            )
            ''')

        return self.with_connection(create_tables)

    @db_operation()
    def save(self, element: PixelColorElementEntity) -> PixelColorElementEntity:
        """Save a PixelColorElement to the database.

        Args:
            element: The PixelColorElement to save

        Returns:
            The saved PixelColorElement with ID populated
        """
        def save_element(conn):
            cursor = conn.cursor()
            if element.id is None:
                # Insert new record
                cursor.execute('''
                INSERT INTO pixel_color_elements (
                    name, tolerance, match_all
                ) VALUES (?, ?, ?)
                ''', (
                    element.name, element.tolerance, element.match_all
                ))
                element.id = cursor.lastrowid
            else:
                # Update existing record
                cursor.execute('''
                UPDATE pixel_color_elements SET
                    name = ?, tolerance = ?, match_all = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (
                    element.name, element.tolerance, element.match_all, element.id
                ))

                # Delete existing points to replace them
                cursor.execute('DELETE FROM pixel_color_points WHERE element_id = ?', (element.id,))

            # Save all points
            for point_entity in element.points:
                point_entity.element_id = element.id
                cursor.execute('''
                INSERT INTO pixel_color_points (
                    element_id, point_x, point_y, total_width, total_height,
                    color_r, color_g, color_b
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    point_entity.element_id, point_entity.point_x, point_entity.point_y,
                    point_entity.total_width, point_entity.total_height,
                    point_entity.color_r, point_entity.color_g, point_entity.color_b
                ))

            return element

        return self.with_connection(save_element)

    @db_operation(default_return_value=None)
    def find_by_id(self, element_id: int) -> Optional[PixelColorElementEntity]:
        """Find a PixelColorElement by its ID.

        Args:
            element_id: The ID of the PixelColorElement to find

        Returns:
            The PixelColorElement if found, None otherwise
        """
        def find_element(conn):
            cursor = conn.cursor()

            # Get main element data
            cursor.execute('''
            SELECT id, name, tolerance, match_all, created_at, updated_at
            FROM pixel_color_elements
            WHERE id = ?
            ''', (element_id,))

            element_row = cursor.fetchone()
            if not element_row:
                return None

            element = self._row_to_element(element_row)

            # Get all points for this element
            cursor.execute('''
            SELECT id, element_id, point_x, point_y, total_width, total_height,
                   color_r, color_g, color_b
            FROM pixel_color_points
            WHERE element_id = ?
            ''', (element_id,))

            point_rows = cursor.fetchall()
            for point_row in point_rows:
                element.points.append(self._row_to_point(point_row))

            return element

        return self.with_connection(find_element)

    @db_operation(default_return_value=None)
    def find_by_name(self, name: str) -> Optional[PixelColorElementEntity]:
        """Find a PixelColorElement by its name.

        Args:
            name: The name of the PixelColorElement to find

        Returns:
            The PixelColorElement if found, None otherwise
        """
        def find_by_name_op(conn):
            cursor = conn.cursor()

            # Get main element data
            cursor.execute('''
            SELECT id, name, tolerance, match_all, created_at, updated_at
            FROM pixel_color_elements
            WHERE name = ?
            ''', (name,))

            element_row = cursor.fetchone()
            if not element_row:
                return None

            element = self._row_to_element(element_row)

            # Get all points for this element
            cursor.execute('''
            SELECT id, element_id, point_x, point_y, total_width, total_height,
                   color_r, color_g, color_b
            FROM pixel_color_points
            WHERE element_id = ?
            ''', (element.id,))

            point_rows = cursor.fetchall()
            for point_row in point_rows:
                element.points.append(self._row_to_point(point_row))

            return element

        return self.with_connection(find_by_name_op)

    @db_operation(default_return_value=[])
    def find_all(self) -> List[PixelColorElementEntity]:
        """Find all PixelColorElements in the database.

        Returns:
            List of all PixelColorElements
        """
        def find_all_op(conn):
            cursor = conn.cursor()

            # Get all elements
            cursor.execute('''
            SELECT id, name, tolerance, match_all, created_at, updated_at
            FROM pixel_color_elements
            ''')

            element_rows = cursor.fetchall()
            elements = [self._row_to_element(row) for row in element_rows]

            # If no elements, return empty list
            if not elements:
                return []

            # Get all points for all elements in one query
            element_ids = [element.id for element in elements]
            placeholders = ','.join(['?'] * len(element_ids))

            cursor.execute(f'''
            SELECT id, element_id, point_x, point_y, total_width, total_height,
                   color_r, color_g, color_b
            FROM pixel_color_points
            WHERE element_id IN ({placeholders})
            ''', element_ids)

            point_rows = cursor.fetchall()

            # Create a map from element_id to element for quick lookup
            element_map = {element.id: element for element in elements}

            # Add points to their respective elements
            for point_row in point_rows:
                point = self._row_to_point(point_row)
                if point.element_id in element_map:
                    element_map[point.element_id].points.append(point)

            return elements

        return self.with_connection(find_all_op)

    @db_operation(default_return_value=False)
    def delete(self, element_id: int) -> bool:
        """Delete a PixelColorElement by its ID.

        Args:
            element_id: The ID of the PixelColorElement to delete

        Returns:
            True if successful, False otherwise
        """
        def delete_op(conn):
            cursor = conn.cursor()
            # Delete element (points will be cascade deleted by foreign key constraint)
            cursor.execute('DELETE FROM pixel_color_elements WHERE id = ?', (element_id,))
            return cursor.rowcount > 0

        return self.with_connection(delete_op)

    def _row_to_element(self, row) -> PixelColorElementEntity:
        """Convert a database row to a PixelColorElement.

        Args:
            row: Database row (as a dict-like object)

        Returns:
            PixelColorElement instance
        """
        return PixelColorElementEntity(
            id=row['id'],
            name=row['name'],
            tolerance=row['tolerance'],
            match_all=bool(row['match_all']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_point(self, row) -> PixelColorPointEntity:
        """Convert a database row to a PixelColorPointEntity.

        Args:
            row: Database row (as a dict-like object)

        Returns:
            PixelColorPointEntity instance
        """
        return PixelColorPointEntity(
            id=row['id'],
            element_id=row['element_id'],
            point_x=row['point_x'],
            point_y=row['point_y'],
            total_width=row['total_width'],
            total_height=row['total_height'],
            color_r=row['color_r'],
            color_g=row['color_g'],
            color_b=row['color_b']
        )

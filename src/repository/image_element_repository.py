"""
Repository for ImageElement data access operations.

This module provides database access methods for ImageElement objects,
handling serialization, deserialization, and CRUD operations.
"""

import io
import logging
from pathlib import Path
from typing import List, Optional

from PIL import Image

from log.config import get_logger

from .conn import get_connection
from .image_element_dto import ImageElementDTO

logger = get_logger(__name__)


class ImageElementRepository:
    """Repository for database operations on ImageElement entities."""

    @staticmethod
    def create_table() -> None:
        """Create the image_elements table if it doesn't exist."""
        conn = get_connection()
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

        conn.commit()

    @staticmethod
    def save(dto: ImageElementDTO) -> ImageElementDTO:
        """Save an ImageElementDTO to the database.

        Args:
            dto: The ImageElementDTO to save

        Returns:
            The saved ImageElementDTO with ID populated
        """
        conn = get_connection()
        cursor = conn.cursor()

        if dto.id is None:
            # Insert new record
            cursor.execute('''
            INSERT INTO image_elements (
                name, region_x, region_y, region_width, region_height,
                region_total_width, region_total_height, image_data, threshold
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dto.name, dto.region_x, dto.region_y, dto.region_width,
                dto.region_height, dto.region_total_width, dto.region_total_height,
                dto.image_data, dto.threshold
            ))
            dto.id = cursor.lastrowid
        else:
            # Update existing record
            cursor.execute('''
            UPDATE image_elements SET
                name = ?, region_x = ?, region_y = ?, region_width = ?,
                region_height = ?, region_total_width = ?, region_total_height = ?,
                image_data = ?, threshold = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (
                dto.name, dto.region_x, dto.region_y, dto.region_width,
                dto.region_height, dto.region_total_width, dto.region_total_height,
                dto.image_data, dto.threshold, dto.id
            ))

        conn.commit()
        return dto

    @staticmethod
    def find_by_id(element_id: int) -> Optional[ImageElementDTO]:
        """Find an ImageElementDTO by its ID.

        Args:
            element_id: The ID of the ImageElement to find

        Returns:
            The ImageElementDTO if found, None otherwise
        """
        conn = get_connection()
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

        return ImageElementDTO(
            id=row[0],
            name=row[1],
            region_x=row[2],
            region_y=row[3],
            region_width=row[4],
            region_height=row[5],
            region_total_width=row[6],
            region_total_height=row[7],
            image_data=row[8],
            threshold=row[9],
            created_at=row[10],
            updated_at=row[11],
        )

    @staticmethod
    def find_by_name(name: str) -> Optional[ImageElementDTO]:
        """Find an ImageElementDTO by its name.

        Args:
            name: The name of the ImageElement to find

        Returns:
            The ImageElementDTO if found, None otherwise
        """
        conn = get_connection()
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

        return ImageElementDTO(
            id=row[0],
            name=row[1],
            region_x=row[2],
            region_y=row[3],
            region_width=row[4],
            region_height=row[5],
            region_total_width=row[6],
            region_total_height=row[7],
            image_data=row[8],
            threshold=row[9],
            created_at=row[10],
            updated_at=row[11],
        )

    @staticmethod
    def find_all() -> List[ImageElementDTO]:
        """Find all ImageElementDTOs in the database.

        Returns:
            List of all ImageElementDTOs
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT id, name, region_x, region_y, region_width, region_height,
               region_total_width, region_total_height, image_data, threshold,
               created_at, updated_at
        FROM image_elements
        ''')

        rows = cursor.fetchall()
        return [
            ImageElementDTO(
                id=row[0],
                name=row[1],
                region_x=row[2],
                region_y=row[3],
                region_width=row[4],
                region_height=row[5],
                region_total_width=row[6],
                region_total_height=row[7],
                image_data=row[8],
                threshold=row[9],
                created_at=row[10],
                updated_at=row[11],
            )
            for row in rows
        ]

    @staticmethod
    def delete(element_id: int) -> bool:
        """Delete an ImageElement by its ID.

        Args:
            element_id: The ID of the ImageElement to delete

        Returns:
            True if successful, False otherwise
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM image_elements WHERE id = ?', (element_id,))
        conn.commit()

        return cursor.rowcount > 0

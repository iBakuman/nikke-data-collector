import io
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from domain.character import Character
from log.config import get_logger
from repository.base_dao import BaseDAO
from repository.decorator import db_operation

logger = get_logger(__name__)

class CharacterDAO(BaseDAO):
    """
    Data Access Object for character data in SQLite database.
    Handles CRUD operations for characters and their images.
    """

    @db_operation(default_return_value=False)
    def add_character(self, character_id: str, chinese_name: str,
                      japanese_name: Optional[str] = None,
                      english_name: Optional[str] = None) -> bool:
        """
        Add a new character to the database

        Args:
            character_id: Unique ID for the character
            chinese_name: Chinese name of the character (optional)
            japanese_name: Japanese name of the character (optional)
            english_name: English name of the character

        Returns:
            True if successful, False otherwise
        """
        return self.with_connection(lambda conn:
                                    conn.execute(
                                        '''
                                        INSERT INTO characters (id, english_name, japanese_name, chinese_name)
                                        VALUES (?, ?, ?, ?)
                                        ''',
                                        (character_id, english_name, japanese_name, chinese_name)
                                    ) or True  # Return True when execute succeeds
                                    )

    @db_operation(default_return_value=False)
    def update_character(self, character_id: str, english_name: Optional[str] = None,
                         japanese_name: Optional[str] = None,
                         chinese_name: Optional[str] = None) -> bool:
        """
        Update an existing character in the database

        Args:
            character_id: ID of the character to update
            english_name: New English name (optional)
            japanese_name: New Japanese name (optional)
            chinese_name: New Chinese name (optional)

        Returns:
            True if successful, False if character not found
        """
        # Build update query dynamically based on provided values
        updates = []
        params = []

        if english_name is not None:
            updates.append("english_name = ?")
            params.append(english_name)

        if japanese_name is not None:
            updates.append("japanese_name = ?")
            params.append(japanese_name)

        if chinese_name is not None:
            updates.append("chinese_name = ?")
            params.append(chinese_name)

        if not updates:
            # Nothing to update
            return False

        # Add character_id to params
        params.append(character_id)

        return self.with_connection(lambda conn:
                                    conn.execute(
                                        f'''
                UPDATE characters
                SET {", ".join(updates)}
                WHERE id = ?
                ''',
                                        params
                                    ).rowcount > 0
                                    )

    @db_operation(default_return_value=False)
    def delete_character(self, character_id: str) -> bool:
        """
        Delete a character from the database

        Args:
            character_id: ID of the character to delete

        Returns:
            True if successful, False if character not found
        """

        def delete_op(conn):
            # Delete related images first (foreign key constraint)
            conn.execute(
                "DELETE FROM character_images WHERE character_id = ?",
                (character_id,)
            )
            # Delete the character
            cursor = conn.execute(
                "DELETE FROM characters WHERE id = ?",
                (character_id,)
            )
            return cursor.rowcount > 0

        return self.with_connection(delete_op)

    @db_operation(default_return_value=None)
    def get_character(self, character_id: str) -> Optional[Character]:
        """
        Get a character by ID

        Args:
            character_id: ID of the character to retrieve

        Returns:
            Character object or None if not found
        """

        def get_char_op(conn):
            cursor = conn.execute(
                "SELECT * FROM characters WHERE id = ?",
                (character_id,)
            )
            row = cursor.fetchone()
            if row:
                data = dict(row)
                # Get preferred name based on available language versions
                name = data.get('english_name', '')
                if not name:  # If english_name is None or empty string
                    name = data.get('japanese_name', '')
                if not name:  # If japanese_name is also None or empty string
                    name = data.get('chinese_name', '')
                return Character(
                    position=0,  # Default position
                    id=data['id'],
                    name=name
                )
            return None

        return self.with_connection(get_char_op)

    @db_operation(default_return_value=None)
    def get_character_raw(self, character_id: str) -> Optional[Dict]:
        """
        Get raw character data by ID

        Args:
            character_id: ID of the character to retrieve

        Returns:
            Character data as a dictionary, or None if not found
        """

        def get_raw_op(conn):
            cursor = conn.execute(
                "SELECT * FROM characters WHERE id = ?",
                (character_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        return self.with_connection(get_raw_op)

    @db_operation(default_return_value=None)
    def get_all_characters(self) -> Optional[List[Character]]:
        """
        Get all characters in the database

        Returns:
            List of Character objects
        """

        def get_all_op(conn):
            cursor = conn.execute("SELECT * FROM characters ORDER BY id")
            result = []
            for row in cursor.fetchall():
                data = dict(row)
                # Get preferred name based on available language versions
                name = data.get('english_name', '')
                if not name:  # If english_name is None or empty string
                    name = data.get('japanese_name', '')
                if not name:  # If japanese_name is also None or empty string
                    name = data.get('chinese_name', '')
                result.append(Character(
                    id=data['id'],
                    name=name
                ))
            return result

        return self.with_connection(get_all_op)

    @db_operation(default_return_value=[])
    def get_all_characters_raw(self) -> List[Dict]:
        """
        Get raw data for all characters in the database

        Returns:
            List of character data dictionaries
        """
        return self.with_connection(lambda conn:
                                    [dict(row) for row in
                                     conn.execute("SELECT * FROM characters ORDER BY id").fetchall()]
                                    )

    @db_operation(default_return_value=False)
    def add_character_image(self, character_id: str, image: Union[str, np.ndarray, Image.Image]) -> bool:
        """
        Add an image for a character

        Args:
            character_id: ID of the character
            image: Image to add (file path, numpy array, or PIL Image)
        Returns:
            True if successful, False otherwise
        """
        # Convert image to binary data
        if isinstance(image, str):
            # Load from file path
            with open(image, 'rb') as f:
                image_data = f.read()
        elif isinstance(image, np.ndarray):
            # Convert OpenCV image to binary
            is_success, buffer = cv2.imencode('.png', image)
            if not is_success:
                return False
            image_data = buffer.tobytes()
        elif isinstance(image, Image.Image):
            # Convert PIL image to binary
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_data = buffer.getvalue()

        return self.with_connection(lambda conn:
                                    conn.execute(
                                        '''
                                        INSERT INTO character_images (character_id, image_data)
                                        VALUES (?, ?)
                                        ''',
                                        (character_id, image_data)
                                    ) or True  # Return True when execute succeeds
                                    )

    @db_operation(default_return_value=[])
    def get_character_images(self, character_id: str) -> List[Tuple[int, bytes]]:
        """
        Get all images for a character

        Args:
            character_id: ID of the character

        Returns:
            List of tuples (image_id, image_data, image_hash)
        """
        return self.with_connection(lambda conn:
                                    [(row['id'], row['image_data']) for row in conn.execute(
                                        "SELECT id, image_data FROM character_images WHERE character_id = ?",
                                        (character_id,)
                                    ).fetchall()]
                                    )

    @db_operation(default_return_value=None)
    def get_character_image(self, image_id: int) -> Optional[bytes]:
        """
        Get a specific character image by ID

        Args:
            image_id: ID of the image

        Returns:
            Tuple of (image_data) or None if not found
        """

        def get_image_op(conn):
            cursor = conn.execute(
                "SELECT image_data FROM character_images WHERE id = ?",
                (image_id,)
            )
            row = cursor.fetchone()
            if row:
                return row['image_data']
            return None

        return self.with_connection(get_image_op)

    @db_operation(default_return_value=False)
    def delete_character_image(self, image_id: int) -> bool:
        """
        Delete a character image by ID

        Args:
            image_id: ID of the image to delete

        Returns:
            True if successful, False if image not found
        """
        return self.with_connection(lambda conn:
                                    conn.execute(
                                        "DELETE FROM character_images WHERE id = ?",
                                        (image_id,)
                                    ).rowcount > 0
                                    )

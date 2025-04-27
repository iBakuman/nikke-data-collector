import io
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from .character_dto import Character
from .conn import get_db_connection, get_db_path


class CharacterDTORepository:
    """
    Data Access Object for character data in SQLite database.
    Handles CRUD operations for characters and their images.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the character DAO

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path if db_path is not None else get_db_path()

    def add_character(self, character_id: str, chinese_name: str,
                     japanese_name: Optional[str] = None,
                     english_name: Optional[str] = None) -> Optional[bool]:
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
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    '''
                    INSERT INTO characters (id, english_name, japanese_name, chinese_name)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (character_id, english_name, japanese_name, chinese_name)
                )
            return True
        except sqlite3.IntegrityError:
            # Character with this ID already exists
            return False
        finally:
            conn.close()

    def update_character(self, character_id: str, english_name: Optional[str] = None,
                        japanese_name: Optional[str] = None,
                        chinese_name: Optional[str] = None) -> Optional[bool]:
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
        conn = get_db_connection(self.db_path)

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
            conn.close()
            return False

        # Add character_id to params
        params.append(character_id)

        try:
            with conn:
                cursor = conn.execute(
                    f'''
                    UPDATE characters
                    SET {", ".join(updates)}
                    WHERE id = ?
                    ''',
                    params
                )

            success = cursor.rowcount > 0
            return success
        finally:
            conn.close()

    def delete_character(self, character_id: str) -> Optional[bool]:
        """
        Delete a character from the database

        Args:
            character_id: ID of the character to delete

        Returns:
            True if successful, False if character not found
        """
        conn = get_db_connection(self.db_path)

        try:
            with conn:
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

            success = cursor.rowcount > 0
            return success
        finally:
            conn.close()

    def get_character(self, character_id: str) -> Optional[Character]:
        """
        Get a character by ID

        Args:
            character_id: ID of the character to retrieve

        Returns:
            Character object or None if not found
        """
        conn = get_db_connection(self.db_path)

        try:
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
        finally:
            conn.close()

    def get_character_raw(self, character_id: str) -> Optional[Dict]:
        """
        Get raw character data by ID

        Args:
            character_id: ID of the character to retrieve

        Returns:
            Character data as a dictionary, or None if not found
        """
        conn = get_db_connection(self.db_path)

        try:
            cursor = conn.execute(
                "SELECT * FROM characters WHERE id = ?",
                (character_id,)
            )

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_all_characters(self) -> Optional[List[Character]]:
        """
        Get all characters in the database

        Returns:
            List of Character objects
        """
        conn = get_db_connection(self.db_path)

        try:
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
        finally:
            conn.close()

    def get_all_characters_raw(self) -> List[Dict]:
        """
        Get raw data for all characters in the database

        Returns:
            List of character data dictionaries
        """
        conn = get_db_connection(self.db_path)

        try:
            cursor = conn.execute("SELECT * FROM characters ORDER BY id")

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_character_image(self, character_id: str, image: Union[str, np.ndarray, Image.Image],
                           image_hash: Optional[str] = None) -> bool:
        """
        Add an image for a character

        Args:
            character_id: ID of the character
            image: Image to add (file path, numpy array, or PIL Image)
            image_hash: Optional hash for the image (computed if not provided)

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
        else:
            raise TypeError(f"Unsupported image type: {type(image)}. Must be str, np.ndarray, or PIL.Image.Image")

        # Compute hash if not provided
        if image_hash is None:
            if isinstance(image, str):
                # Load and compute hash
                img = Image.open(image)
                image_hash = self._compute_image_hash(img)
            elif isinstance(image, np.ndarray):
                # Convert and compute hash
                img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                image_hash = self._compute_image_hash(img)
            elif isinstance(image, Image.Image):
                # Compute hash directly
                image_hash = self._compute_image_hash(image)

        conn = get_db_connection(self.db_path)

        try:
            with conn:
                conn.execute(
                    '''
                    INSERT INTO character_images (character_id, image_data, image_hash)
                    VALUES (?, ?, ?)
                    ''',
                    (character_id, image_data, image_hash)
                )
            return True
        except sqlite3.IntegrityError:
            # Character ID doesn't exist or hash collision
            return False
        finally:
            conn.close()

    def get_character_images(self, character_id: str) -> List[Tuple[int, bytes, str]]:
        """
        Get all images for a character

        Args:
            character_id: ID of the character

        Returns:
            List of tuples (image_id, image_data, image_hash)
        """
        conn = get_db_connection(self.db_path)

        try:
            cursor = conn.execute(
                "SELECT id, image_data, image_hash FROM character_images WHERE character_id = ?",
                (character_id,)
            )

            return [(row['id'], row['image_data'], row['image_hash']) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_character_image(self, image_id: int) -> Optional[Tuple[bytes, str]]:
        """
        Get a specific character image by ID

        Args:
            image_id: ID of the image

        Returns:
            Tuple of (image_data, image_hash) or None if not found
        """
        conn = get_db_connection(self.db_path)

        try:
            cursor = conn.execute(
                "SELECT image_data, image_hash FROM character_images WHERE id = ?",
                (image_id,)
            )

            row = cursor.fetchone()
            if row:
                return (row['image_data'], row['image_hash'])
            return None
        finally:
            conn.close()

    def delete_character_image(self, image_id: int) -> bool:
        """
        Delete a character image by ID

        Args:
            image_id: ID of the image to delete

        Returns:
            True if successful, False if image not found
        """
        conn = get_db_connection(self.db_path)

        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM character_images WHERE id = ?",
                    (image_id,)
                )

            success = cursor.rowcount > 0
            return success
        finally:
            conn.close()

    def get_all_character_image_hashes(self) -> Dict[str, List[str]]:
        """
        Get all character image hashes

        Returns:
            Dictionary mapping character IDs to lists of image hashes
        """
        conn = get_db_connection(self.db_path)

        try:
            cursor = conn.execute(
                "SELECT character_id, image_hash FROM character_images"
            )

            result = {}
            for row in cursor.fetchall():
                char_id = row['character_id']
                image_hash = row['image_hash']

                if char_id not in result:
                    result[char_id] = []

                result[char_id].append(image_hash)

            return result
        finally:
            conn.close()

    def get_image_by_hash(self, image_hash: str) -> Optional[Tuple[str, bytes]]:
        """
        Get an image by its hash

        Args:
            image_hash: Hash of the image

        Returns:
            Tuple of (character_id, image_data) or None if not found
        """
        conn = get_db_connection(self.db_path)

        try:
            cursor = conn.execute(
                '''
                SELECT character_images.character_id, character_images.image_data
                FROM character_images
                WHERE image_hash = ?
                ''',
                (image_hash,)
            )

            row = cursor.fetchone()
            if row:
                return (row['character_id'], row['image_data'])
            return None
        finally:
            conn.close()

    @staticmethod
    def _compute_image_hash(image: Image.Image) -> str:
        """
        Compute a perceptual hash for an image.
        Uses PIL's built-in image hashing.

        Args:
            image: PIL Image object

        Returns:
            String hash representing the image
        """
        import imagehash

        # Compute perceptual hash (more robust to minor variations)
        phash = str(imagehash.phash(image))
        return phash

    @staticmethod
    def convert_blob_to_cv_image(blob_data: bytes) -> np.ndarray:
        """
        Convert binary blob data to OpenCV image format

        Args:
            blob_data: Binary image data

        Returns:
            OpenCV image (numpy array)
        """
        # Convert binary data to numpy array
        nparr = np.frombuffer(blob_data, np.uint8)

        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    @staticmethod
    def convert_blob_to_pil_image(blob_data: bytes) -> Image.Image:
        """
        Convert binary blob data to PIL image format

        Args:
            blob_data: Binary image data

        Returns:
            PIL Image object
        """
        # Create BytesIO object from blob data
        buffer = io.BytesIO(blob_data)

        # Open as PIL image
        img = Image.open(buffer)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        return img



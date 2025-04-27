import importlib.resources
import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from importlib.abc import Traversable
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

from .character_dao import CharacterDAO
from .connection import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Database migration information"""
    version: str
    description: str
    sql: str
    timestamp: datetime = None


def get_applied_migrations(conn: sqlite3.Connection) -> Set[str]:
    """
    Get the set of migration versions that have been applied to the database.

    Args:
        conn: SQLite connection

    Returns:
        Set of applied migration version strings
    """
    try:
        cursor = conn.execute("SELECT version FROM migrations ORDER BY timestamp")
        return {row[0] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        # Migrations table doesn't exist yet
        return set()


def init_migrations_table(conn: sqlite3.Connection) -> None:
    """
    Initialize the migrations tracking table if it doesn't exist.

    Args:
        conn: SQLite connection
    """
    with conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        ''')


def load_migrations_from_directory(migrations_dir: Union[Path, Traversable]) -> List[Migration]:
    """
    Load migration files from a directory.
    Migration files should be named like: 001_initial_schema.sql

    Args:
        migrations_dir: Directory containing migration files (Path or Traversable from importlib.resources)

    Returns:
        List of Migration objects sorted by version
    """
    migrations = []

    # Match files like: 001_description.sql
    migration_pattern = re.compile(r'^(\d+)_([a-z0-9_]+)\.sql$')

    try:
        # For MultiplexedPath/Traversable use iterdir instead of glob
        for file_path in migrations_dir.iterdir():
            # Process only .sql files
            if not str(file_path).endswith('.sql'):
                continue

            file_name = os.path.basename(str(file_path))
            match = migration_pattern.match(file_name)

            if match:
                version = match.group(1)
                description = match.group(2).replace('_', ' ')

                # Read file using Traversable's open method
                with file_path.open("r") as f:
                    sql = f.read()

                migrations.append(Migration(
                    version=version,
                    description=description,
                    sql=sql
                ))
    except Exception as e:
        logger.error(f"Error loading migrations: {e}")

    # Sort by version number
    migrations.sort(key=lambda m: m.version)
    return migrations


def apply_migration(conn: sqlite3.Connection, migration: Migration) -> bool:
    """
    Apply a single migration to the database.

    Args:
        conn: SQLite connection
        migration: Migration to apply

    Returns:
        True if successful, False otherwise
    """
    try:
        with conn:
            # Split by semicolons and execute each statement
            statements = migration.sql.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(statement)

            # Record the migration
            now = datetime.utcnow().isoformat()
            conn.execute(
                "INSERT INTO migrations (version, description, timestamp) VALUES (?, ?, ?)",
                (migration.version, migration.description, now)
            )

        logger.info(f"Applied migration {migration.version}: {migration.description}")
        return True

    except Exception as e:
        logger.error(f"Failed to apply migration {migration.version}: {e}")
        return False


def migrate_database(db_path: Optional[Path] = None):
    """
    Apply all pending migrations to the database.

    Args:
        db_path: Path to the database file

    Returns:
        Tuple of (number of successful migrations, number of failed migrations)
    """
    # Open the database connection
    with get_db_connection(db_path) as conn:
        # Ensure migrations table exists
        init_migrations_table(conn)

        # Get already applied migrations
        applied = get_applied_migrations(conn)
        migrations_dir = importlib.resources.files('repository.data.migrations')
        migrations = load_migrations_from_directory(migrations_dir)
        # Apply pending migrations
        success_count = 0
        fail_count = 0
        for migration in migrations:
            if migration.version not in applied:
                if apply_migration(conn, migration):
                    success_count += 1
                else:
                    fail_count += 1

        logger.info(f"Database migration complete: {success_count} applied, {fail_count} failed")
        return success_count, fail_count


def create_migration(description: str, sql: str, output_dir: Optional[Path] = None) -> Path:
    """
    Create a new migration file.

    Args:
        description: Brief description of the migration
        sql: SQL statements for the migration
        output_dir: Directory to save the migration file

    Returns:
        Path to the created migration file
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / 'data' / 'migrations'

    os.makedirs(output_dir, exist_ok=True)

    # Find the next version number
    existing_versions = [
        int(f.stem.split('_')[0])
        for f in output_dir.glob('*.sql')
        if f.stem.split('_')[0].isdigit()
    ]

    next_version = 1
    if existing_versions:
        next_version = max(existing_versions) + 1

    # Format the version with leading zeros
    version_str = f"{next_version:03d}"

    # Convert description to snake_case
    desc_slug = description.lower().replace(' ', '_')
    desc_slug = re.sub(r'[^a-z0-9_]', '', desc_slug)

    # Create the migration file
    file_name = f"{version_str}_{desc_slug}.sql"
    file_path = output_dir / file_name

    with open(file_path, 'w') as f:
        f.write(sql)

    logger.info(f"Created migration file: {file_path}")
    return file_path

class DatabaseMigrationHelper:
    """
    Helper class to migrate character data from the old file-based system
    to the new SQLite database.
    """

    DEFAULT_PATTERNS = [
        # Standard pattern with letter suffix
        r"^(\d{3})_([^_]+)_[a-z]\.(?:png|jpg|jpeg)$",
        # Pattern without letter suffix
        r"^(\d{3})_([^_]+)\.(?:png|jpg|jpeg)$"
    ]

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the migration helper

        Args:
            db_path: Path to the SQLite database file (optional)
        """
        self.character_dao = CharacterDAO(db_path)

    def migrate_from_directory(self, directory_path: Optional[str] = None,
                              patterns: Optional[List[str]] = None) -> Tuple[int, int]:
        """
        Migrate character data from a directory of images to the database

        Args:
            directory_path: Path to directory containing character images
                           (defaults to resources directory if None)
            patterns: List of regex patterns to extract character ID and name from filenames
                      (defaults to DEFAULT_PATTERNS if None)

        Returns:
            Tuple of (images_processed, images_imported)
        """
        if directory_path is None:
            try:
                # Try to get from package resources
                directory_path = str(importlib.resources.files('collector.resources').joinpath('ref'))
            except (ModuleNotFoundError, ImportError, ValueError):
                # Fallback to default location
                directory_path = Path(__file__).parent.parent / 'resources' / 'ref'

        if patterns is None:
            patterns = self.DEFAULT_PATTERNS

        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return 0, 0

        logger.info(f"Migrating character data from directory: {directory_path}")

        processed = 0
        imported = 0

        for filename in os.listdir(directory_path):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            processed += 1

            # Try each pattern until one matches
            match = None
            for pattern in patterns:
                match = re.match(pattern, filename)
                if match:
                    break

            if not match:
                logger.warning(f"Skipping file with unrecognized format: {filename}")
                continue

            char_id = match.group(1)
            char_name = match.group(2).replace('_', ' ')

            # Check if character exists, if not create it
            char = self.character_dao.get_character(char_id)
            if not char:
                logger.info(f"Creating new character: {char_id} - {char_name}")
                self.character_dao.add_character(char_id, char_name)

            # Add the image
            image_path = os.path.join(directory_path, filename)
            success = self.character_dao.add_character_image(char_id, image_path)

            if success:
                imported += 1
                logger.info(f"Imported image: {filename}")
            else:
                logger.warning(f"Failed to import image: {filename}")

        logger.info(f"Migration complete. Processed {processed} images, imported {imported} images.")
        return processed, imported

    def verify_migration(self, directory_path: Optional[str] = None) -> Tuple[int, int, List[str]]:
        """
        Verify that all characters and images were successfully migrated

        Args:
            directory_path: Path to directory containing character images for verification
                           (defaults to resources directory if None)

        Returns:
            Tuple of (files_in_directory, characters_in_db, missing_files)
        """
        if directory_path is None:
            try:
                # Try to get from package resources
                directory_path = str(importlib.resources.files('collector.resources').joinpath('ref'))
            except (ModuleNotFoundError, ImportError, ValueError):
                # Fallback to default location
                directory_path = Path(__file__).parent.parent / 'resources' / 'ref'

        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return 0, 0, []

        # Get all image files in directory
        files = [f for f in os.listdir(directory_path)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        # Get all characters in database
        characters = self.character_dao.get_all_characters()

        # Check for missing files
        missing = []
        for filename in files:
            # Try to extract character ID
            for pattern in self.DEFAULT_PATTERNS:
                match = re.match(pattern, filename)
                if match:
                    char_id = match.group(1)

                    # Check if character exists in database
                    char = self.character_dao.get_character(char_id)
                    if not char:
                        missing.append(f"Character {char_id} from file {filename} not found in database")
                    else:
                        # Check if character has images
                        images = self.character_dao.get_character_images(char_id)
                        if not images:
                            missing.append(f"Character {char_id} has no images in database")

                    break
            else:
                logger.warning(f"Could not extract character ID from filename: {filename}")

        return len(files), len(characters), missing

    def export_statistics(self) -> dict:
        """
        Export statistics about the database

        Returns:
            Dictionary with database statistics
        """
        # Get all characters
        characters = self.character_dao.get_all_characters()

        total_images = 0
        characters_without_images = []

        # Get image count for each character
        character_image_counts = {}
        for char in characters:
            images = self.character_dao.get_character_images(char.id)
            count = len(images)
            character_image_counts[char.id] = count
            total_images += count

            if count == 0:
                characters_without_images.append(char.id)

        return {
            'total_characters': len(characters),
            'total_images': total_images,
            'average_images_per_character': total_images / len(characters) if characters else 0,
            'characters_without_images': characters_without_images,
            'character_image_counts': character_image_counts
        }


def run_migration(db_path: Optional[Path] = None, ref_dir: Optional[str] = None) -> Tuple[int, int]:
    """
    Convenience function to run the database migration

    Args:
        db_path: Path to the SQLite database
        ref_dir: Path to the reference images directory

    Returns:
        Tuple of (images_processed, images_imported)
    """
    # Migrate data
    migrator = DatabaseMigrationHelper(db_path)
    return migrator.migrate_from_directory(ref_dir)
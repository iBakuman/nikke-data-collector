# Default database name
import os
import sqlite3
from importlib.resources import files, as_file
from pathlib import Path
from typing import Optional

from log.config import get_logger

logger = get_logger(__name__)

DEFAULT_DB_NAME = 'nikke.db'


def get_db_path(db_name: Optional[str] = None) -> Path:
    """
    Get the path to the SQLite database file

    Args:
        db_name: Name of the database file

    Returns:
        Path object representing the database file path
    """
    if db_name is None:
        db_name = DEFAULT_DB_NAME

    try:
        # Try to get the path from the package resources (for installed package)
        return as_file(files('collector.repository.data') / db_name)
    except (ModuleNotFoundError, ImportError, ValueError):
        # Fallback to a local path for development
        data_dir = Path(__file__).parent / 'data'
        os.makedirs(data_dir, exist_ok=True)
        return data_dir / db_name


class DBConnection:
    """Database connection manager with context manager support.

    This class wraps a SQLite connection and provides context manager
    functionality to ensure connections are properly closed.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the connection manager.

        Args:
            db_path: Path to the database file, or None to use default
        """
        self.db_path = db_path if db_path is not None else get_db_path()
        self.conn = None

    def __enter__(self) -> sqlite3.Connection:
        """Open the database connection when entering context.

        Returns:
            The SQLite connection object
        """
        # Enable foreign key constraints
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Configure connection to return rows as dictionaries
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the connection when exiting context.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.conn:
            if exc_type is not None:
                # An exception occurred, rollback any pending transaction
                try:
                    self.conn.rollback()
                except sqlite3.Error as e:
                    logger.error(f"Error rolling back transaction: {e}")

            try:
                self.conn.close()
            except sqlite3.Error as e:
                logger.error(f"Error closing connection: {e}")

            self.conn = None


def get_db_connection(db_path: Optional[Path] = None) -> DBConnection:
    """
    Get a database connection manager that supports context management.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")

    Args:
        db_path: Path to the database file, or None to use default

    Returns:
        DBConnection context manager
    """
    return DBConnection(db_path)

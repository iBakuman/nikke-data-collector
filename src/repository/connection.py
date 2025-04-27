# Default database name
import sqlite3
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any, Generator, Optional

from log.config import get_logger

logger = get_logger(__name__)


@contextmanager
def get_db_connection(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, Any, None]:
    """
    Get a database connection with context management.

    Automatically configures the connection with proper settings and handles
    transaction management. The connection will be closed when the context exits.

    If no exception occurs, you still need to commit explicitly if needed.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            conn.commit()  # Don't forget to commit if needed

    Args:
        db_path: Path to the database file, or None to use default

    Returns:
        SQLite connection object
    """
    conn = None
    try:
        if db_path is None:
            with as_file(files('repository.data') / 'nikke.db') as p:
                conn = sqlite3.connect(str(p))
        else:
            conn = sqlite3.connect(str(db_path))

        conn.execute("PRAGMA foreign_keys = ON")
        # Configure connection to return rows as dictionaries
        conn.row_factory = sqlite3.Row

        yield conn

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except sqlite3.Error as rollback_error:
                logger.error(f"Error rolling back transaction: {rollback_error}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except sqlite3.Error as close_error:
                logger.error(f"Error closing connection: {close_error}")

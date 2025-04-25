# Default database name
import os
import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import Optional

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
        return files('nikke_arena.db.data').joinpath(db_name)
    except (ModuleNotFoundError, ImportError, ValueError):
        # Fallback to a local path for development
        data_dir = Path(__file__).parent / 'data'
        os.makedirs(data_dir, exist_ok=True)
        return data_dir / db_name


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get a connection to the SQLite database

    Args:
        db_path: Path to the database file

    Returns:
        SQLite connection object
    """
    if db_path is None:
        db_path = get_db_path()
    # Enable foreign key constraints
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    # Configure connection to return rows as dictionaries
    conn.row_factory = sqlite3.Row
    return conn
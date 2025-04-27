import os
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from repository.connection import get_db_connection


def test_successful_transaction():
    """Test that successful operations are committed when no exceptions occur."""
    # Create temporary database file
    temp_db = NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        db_path = Path(temp_db.name)

        # First connection: create a table and insert data
        with get_db_connection(db_path) as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test_table (name) VALUES (?)", ("test_value",))
            conn.commit()

        # Second connection: verify data persisted
        with get_db_connection(db_path) as conn:
            result = conn.execute("SELECT name FROM test_table WHERE id = 1").fetchone()
            assert result is not None
            assert result["name"] == "test_value"

    finally:
        # Clean up temporary file
        os.unlink(temp_db.name)


def test_transaction_rollback_on_error():
    """Test that transactions are rolled back when an exception occurs."""
    # Create temporary database file
    temp_db = NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        db_path = Path(temp_db.name)

        # First connection: create a table
        with get_db_connection(db_path) as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            conn.commit()

        # Second connection: attempt operation that will fail
        try:
            with get_db_connection(db_path) as conn:
                # This should succeed
                conn.execute("INSERT INTO test_table (name) VALUES (?)", ("valid_value",))

                # This should fail due to NOT NULL constraint
                conn.execute("INSERT INTO test_table (name) VALUES (?)", (None,))

                # We should never reach this point
                conn.commit()

                pytest.fail("Expected sqlite3.IntegrityError was not raised")
        except sqlite3.IntegrityError:
            # Expected exception, continue with test
            pass

        # Third connection: verify the first insert was rolled back
        with get_db_connection(db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()[0]
            assert count == 0, "Transaction was not rolled back correctly"

    finally:
        # Clean up temporary file
        os.unlink(temp_db.name)

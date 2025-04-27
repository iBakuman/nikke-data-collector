import os
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from repository.connection import get_db_connection


def test_auto_commit():
    """Test that transactions are automatically committed when no exceptions occur."""
    # Create temporary database file
    temp_db = NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        db_path = Path(temp_db.name)

        # First connection: create a table and insert data
        with get_db_connection(db_path) as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test_table (name) VALUES (?)", ("test_value",))
            # No explicit commit needed

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
            # No explicit commit needed

        # Second connection: attempt operation that will fail
        try:
            with get_db_connection(db_path) as conn:
                # This should succeed
                conn.execute("INSERT INTO test_table (name) VALUES (?)", ("valid_value",))

                # This should fail due to NOT NULL constraint
                conn.execute("INSERT INTO test_table (name) VALUES (?)", (None,))

                # We should never reach this point
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


def test_explicit_commit_still_works():
    """Test that explicit commits still work as expected."""
    # Create temporary database file
    temp_db = NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        db_path = Path(temp_db.name)

        # Create table and insert first record with explicit commit
        with get_db_connection(db_path) as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test_table (name) VALUES (?)", ("record1",))
            conn.commit()  # Explicit commit

            # Add another record that should be auto-committed
            conn.execute("INSERT INTO test_table (name) VALUES (?)", ("record2",))

        # Verify both records persisted
        with get_db_connection(db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()[0]
            assert count == 2, "Both records should be saved (one from explicit commit, one from auto-commit)"

    finally:
        # Clean up temporary file
        os.unlink(temp_db.name)

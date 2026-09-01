import os
import tempfile
import sqlite3
import pytest

from backend.department_nodes.common.database import get_connection, initialize_database

def test_database_initialization():
    """Verify that tables are created and seed data is populated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_cse.db")
        initialize_database(db_path, "CSE")

        conn = get_connection(db_path)
        cursor = conn.cursor()

        # Check resources table
        cursor.execute("SELECT COUNT(*) as count FROM resources;")
        res_count = cursor.fetchone()["count"]
        assert res_count > 0, "Seed resources should be inserted on initial creation"

        # Check bookings table exists
        cursor.execute("SELECT COUNT(*) as count FROM bookings;")
        bk_count = cursor.fetchone()["count"]
        assert bk_count == 0, "Bookings table should initially be empty"

        conn.close()

def test_idempotent_initialization():
    """Verify that re-initializing database does not duplicate data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_it.db")
        initialize_database(db_path, "IT")

        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM resources;")
        initial_count = cursor.fetchone()["count"]
        conn.close()

        # Re-initialize
        initialize_database(db_path, "IT")

        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM resources;")
        new_count = cursor.fetchone()["count"]
        conn.close()

        assert initial_count == new_count, "Database re-initialization should be idempotent"

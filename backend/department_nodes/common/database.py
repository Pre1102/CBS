import os
import sqlite3
import sys

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.department_nodes.common.seed_data import SEED_RESOURCES
except ImportError:
    from department_nodes.common.seed_data import SEED_RESOURCES

def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Establish and return a SQLite database connection.
    Enables sqlite3.Row for dictionary-style attribute access.
    """
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database(db_path: str, department_code: str) -> None:
    """
    Creates resources and bookings tables if they do not exist,
    and populates seed resources if the database is newly initialized.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Create resources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            location TEXT NOT NULL,
            department TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            is_available INTEGER DEFAULT 1,
            UNIQUE(name, department)
        );
    """)

    # Create bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER NOT NULL,
            booked_by TEXT NOT NULL,
            department TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            purpose TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CONFIRMED',
            created_at TEXT NOT NULL,
            FOREIGN KEY (resource_id) REFERENCES resources (id)
        );
    """)

    conn.commit()

    # Populate sample data if resources table is empty
    cursor.execute("SELECT COUNT(*) as count FROM resources;")
    row = cursor.fetchone()
    if row and row["count"] == 0:
        dept_clean = department_code.upper().replace("&", "")
        # Find matching key in seed dictionary
        target_key = "ENTC" if ("ENTC" in dept_clean or "ETC" in dept_clean) else department_code.upper()
        seed_list = SEED_RESOURCES.get(target_key, SEED_RESOURCES.get(department_code.upper(), []))

        for res in seed_list:
            cursor.execute("""
                INSERT OR IGNORE INTO resources (name, resource_type, location, department, capacity, is_available)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (
                res["name"],
                res["resource_type"],
                res["location"],
                res["department"],
                res["capacity"],
                res["is_available"]
            ))
        conn.commit()


    conn.close()

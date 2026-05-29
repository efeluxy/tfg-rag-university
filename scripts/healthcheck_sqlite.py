"""Block 3.4: SQLite healthcheck."""
import os
import sys
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("SQLITE_DB_PATH", "data/database/students.db")

def test_sqlite():
    conn = sqlite3.connect(DB_PATH)
    try:
        n = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        print(f"SQLITE: {n} alumnos en BD")
        if n == 50:
            print("SQLITE_COUNT: PASS (50 alumnos)")
        else:
            print(f"SQLITE_COUNT: WARNING (expected 50, got {n})")
        return True
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        test_sqlite()
        print("SQLITE: OK")
        sys.exit(0)
    except Exception as e:
        print(f"SQLITE ERROR: {e}")
        sys.exit(1)

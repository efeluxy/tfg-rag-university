"""Migracion: anade tabla student_subject_attempts."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "database" / "students.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS student_subject_attempts (
    student_id TEXT NOT NULL,
    subject_code TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    attempts_used INTEGER NOT NULL DEFAULT 0,
    attempts_max INTEGER NOT NULL DEFAULT 4,
    last_attempt_year INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
        -- 'passed' | 'failed_last' | 'pending'
    PRIMARY KEY (student_id, subject_code),
    FOREIGN KEY (student_id) REFERENCES students(id)
);
"""

INDEX = """
CREATE INDEX IF NOT EXISTS idx_attempts_student
  ON student_subject_attempts(student_id);
"""


def run():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.executescript(SCHEMA + INDEX)
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) FROM student_subject_attempts"
        ).fetchone()[0]
        print(f"OK - Tabla creada/verificada. Filas actuales: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    run()

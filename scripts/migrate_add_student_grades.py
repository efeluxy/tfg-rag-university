"""Migracion: tabla student_grades con historico de notas por convocatoria."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "database" / "students.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS student_grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject_code TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    grade REAL NOT NULL CHECK (grade >= 0 AND grade <= 10),
    passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE (student_id, subject_code, attempt_number)
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_grades_student
  ON student_grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_subject
  ON student_grades(student_id, subject_code);
"""


def run():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.executescript(SCHEMA + INDEXES)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM student_grades").fetchone()[0]
        print(f"OK - Tabla student_grades creada. Filas: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    run()

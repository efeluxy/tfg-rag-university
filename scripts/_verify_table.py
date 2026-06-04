"""Verifica que la tabla student_subject_attempts existe."""
import sqlite3
from pathlib import Path
DB = Path(__file__).parent.parent / "data" / "database" / "students.db"
conn = sqlite3.connect(str(DB))
r = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='student_subject_attempts'").fetchone()
print(r[0] if r else "NO EXISTE")
conn.close()

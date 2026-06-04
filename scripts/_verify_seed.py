"""Verifica datos del seed."""
import sqlite3
from pathlib import Path
DB = Path(__file__).parent.parent / "data" / "database" / "students.db"
conn = sqlite3.connect(str(DB))
total = conn.execute("SELECT COUNT(*) FROM student_subject_attempts").fetchone()[0]
sergio = conn.execute("SELECT COUNT(*) FROM student_subject_attempts WHERE student_id='ALU015'").fetchone()[0]
print(f"Total filas: {total}, ALU015: {sergio}")
conn.close()

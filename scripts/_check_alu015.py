"""Check ALU015 INF201 in new seed."""
import sqlite3
from pathlib import Path
DB = Path(__file__).parent.parent / "data" / "database" / "students.db"
conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
r = conn.execute(
    "SELECT * FROM student_subject_attempts WHERE student_id='ALU015' AND subject_code='INF201'"
).fetchone()
print(dict(r) if r else "NOT FOUND")
g = conn.execute(
    "SELECT * FROM student_grades WHERE student_id='ALU015' AND subject_code='INF201'"
).fetchall()
for row in g:
    print(dict(row))
conn.close()

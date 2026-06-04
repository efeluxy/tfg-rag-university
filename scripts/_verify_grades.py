"""Verifica coherencia de los datos de notas."""
import sqlite3
from pathlib import Path
DB = Path(__file__).parent.parent / "data" / "database" / "students.db"
conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row

a = conn.execute("SELECT COUNT(*) FROM student_subject_attempts").fetchone()[0]
g = conn.execute("SELECT COUNT(*) FROM student_grades").fetchone()[0]
print(f"attempts: {a}, grades: {g}")
assert a >= 600, f"Esperado >= 600 attempts, got {a}"
assert g >= 800, f"Esperado >= 800 grades, got {g}"

# ALU001 (excellent): mayoria passed con notas altas
r1 = conn.execute(
    "SELECT passed, AVG(grade) as avg_g, COUNT(*) as cnt FROM student_grades "
    "WHERE student_id='ALU001' GROUP BY passed"
).fetchall()
for r in r1:
    print(f"ALU001 passed={r['passed']}: avg={r['avg_g']:.1f}, count={r['cnt']}")

# ALU015 (at_risk): varias notas bajas
r2 = conn.execute(
    "SELECT passed, AVG(grade) as avg_g, COUNT(*) as cnt FROM student_grades "
    "WHERE student_id='ALU015' GROUP BY passed"
).fetchall()
for r in r2:
    print(f"ALU015 passed={r['passed']}: avg={r['avg_g']:.1f}, count={r['cnt']}")

conn.close()
print("OK - coherencia verificada")

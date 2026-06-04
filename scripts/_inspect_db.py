"""Script temporal para inspeccionar el schema de la BD."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "database" / "students.db"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row

tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("=== TABLAS ===")
for t in tables:
    print(" -", t["name"])

print()
print("=== SCHEMA TABLA students ===")
schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='students'").fetchone()
print(schema["sql"] if schema else "NO EXISTE")

print()
print("=== OTRAS TABLAS (schema) ===")
for t in tables:
    if t["name"] != "students":
        s = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t["name"],)
        ).fetchone()
        print(f"\n-- {t['name']} --")
        print(s["sql"] if s else "NO SCHEMA")

print()
print("=== FILAS ALU001, ALU015, ALU030 ===")
for aid in ["ALU001", "ALU015", "ALU030"]:
    row = conn.execute("SELECT * FROM students WHERE id=?", (aid,)).fetchone()
    if row:
        print(dict(row))
    else:
        print(f"{aid}: NO EXISTE")

conn.close()

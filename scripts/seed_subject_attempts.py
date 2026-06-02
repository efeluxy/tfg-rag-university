"""Pobla la tabla student_subject_attempts con datos sinteticos coherentes.

Script idempotente: usa INSERT OR REPLACE para evitar duplicados.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "database" / "students.db"

# Formato: (student_id, subject_code, subject_name, attempts_used, attempts_max, last_attempt_year, status)
DATA = [
    # ── ALU001 — Carlos Vega Cruz (Informatica, 4 anyo, GPA 9.10, excellent) ──
    ("ALU001", "INF101", "Algoritmica",              1, 4, 2023, "passed"),
    ("ALU001", "INF103", "Programacion I",            1, 4, 2023, "passed"),
    ("ALU001", "INF201", "Estructuras de Datos",      1, 4, 2024, "passed"),
    ("ALU001", "INF203", "Bases de Datos",            1, 4, 2024, "passed"),
    ("ALU001", "INF301", "Ingenieria del Software",   1, 4, 2025, "passed"),
    ("ALU001", "INF302", "Inteligencia Artificial",   1, 4, 2025, "passed"),
    ("ALU001", "INF308", "Aprendizaje Automatico",    2, 4, 2025, "passed"),
    ("ALU001", "INF401", "TFG",                       0, 4, None, "pending"),

    # ── ALU015 — Sergio Delgado Pena (Informatica, 2 anyo, GPA 4.20, at_risk) ──
    ("ALU015", "INF101", "Algoritmica",              3, 4, 2024, "passed"),
    ("ALU015", "INF102", "Calculo",                  3, 4, 2025, "failed_last"),
    ("ALU015", "INF103", "Programacion I",            2, 4, 2024, "passed"),
    ("ALU015", "INF104", "Logica",                   2, 4, 2024, "passed"),
    ("ALU015", "INF201", "Estructuras de Datos",      2, 4, 2025, "failed_last"),
    ("ALU015", "INF202", "Sistemas Operativos",       2, 4, 2026, "failed_last"),
    ("ALU015", "INF203", "Bases de Datos",            0, 4, None, "pending"),
    ("ALU015", "INF204", "Redes",                     0, 4, None, "pending"),

    # ── ALU030 — Isabel Blanco Perez (grado mixto, beca MEC) ──
    ("ALU030", "INF101", "Algoritmica",              1, 4, 2024, "passed"),
    ("ALU030", "INF103", "Programacion I",            2, 4, 2024, "passed"),
    ("ALU030", "INF201", "Estructuras de Datos",      1, 4, 2025, "passed"),
    ("ALU030", "INF203", "Bases de Datos",            1, 4, 2026, "pending"),
    ("ALU030", "INF301", "Ingenieria del Software",   0, 4, None, "pending"),

    # ── ALU002 — variedad para demos ──
    ("ALU002", "INF101", "Algoritmica",              1, 4, 2023, "passed"),
    ("ALU002", "INF201", "Estructuras de Datos",      2, 4, 2024, "passed"),
    ("ALU002", "INF301", "Ingenieria del Software",   1, 4, 2025, "passed"),

    # ── ALU025 — alumno medio, GPA ~6.5 ──
    ("ALU025", "INF101", "Algoritmica",              2, 4, 2024, "passed"),
    ("ALU025", "INF201", "Estructuras de Datos",      2, 4, 2025, "passed"),
    ("ALU025", "INF301", "Ingenieria del Software",   1, 4, 2026, "pending"),

    # ── ALU045 — ultimo anyo, casi terminando ──
    ("ALU045", "INF301", "Ingenieria del Software",   1, 4, 2025, "passed"),
    ("ALU045", "INF401", "TFG",                       1, 4, 2026, "pending"),
    ("ALU045", "INF4E01", "Deep Learning",            1, 4, 2026, "passed"),
]


def run():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.executemany(
            """INSERT OR REPLACE INTO student_subject_attempts
               (student_id, subject_code, subject_name, attempts_used,
                attempts_max, last_attempt_year, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            DATA,
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM student_subject_attempts").fetchone()[0]
        for aid in ["ALU001", "ALU015", "ALU030"]:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM student_subject_attempts WHERE student_id=?", (aid,)
            ).fetchone()[0]
            print(f"  {aid}: {cnt} registros")
        print(f"OK - Total filas insertadas: {total}")
    finally:
        conn.close()


if __name__ == "__main__":
    run()

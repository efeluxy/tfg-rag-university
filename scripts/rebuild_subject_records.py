"""Reconstruye subject_records desde la verdad academica (fix incoherencia F3).

PROBLEMA (documentado en logs/diag_pendientes_incoherencia_20260805.txt):
subject_records se poblaba con generate_students.py usando un catalogo de
asignaturas (codigos -> nombres, y numero de asignaturas por curso) DISTINTO al de
student_grades / student_subject_attempts (que genera seed_full_academic_profile.py
y que es la fuente que muestra la sidebar). Consecuencia: el chat marcaba como
pendientes asignaturas ya aprobadas y con nombres cambiados por codigo, y una misma
respuesta de admin se contradecia a si misma.

SOLUCION (opcion 2): derivar subject_records 1:1 desde student_subject_attempts
(estado y catalogo correctos) + student_grades (nota final de la ultima
convocatoria), de modo que subject_records quede totalmente coherente con la
sidebar (fuente de verdad). Las asignaturas "futuras"/"matriculadas" que solo
existian en el catalogo antiguo desaparecen: la verdad solo modela asignaturas
efectivamente cursadas (con estado passed / failed_last / pending).

Ejecutar DESPUES de seed_full_academic_profile.py. Idempotente y determinista.

Mapeo de estado (student_subject_attempts -> subject_records):
    passed       -> passed
    failed_last  -> failed     (get_pending_subjects filtra IN ('pending','failed'))
    pending      -> pending

Uso:
    python scripts/rebuild_subject_records.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "database" / "students.db"

# Estado de la tabla "verdad" -> estado en subject_records
STATUS_MAP = {
    "passed": "passed",
    "failed_last": "failed",
    "pending": "pending",
}

CREDITS_DEFAULT = 6  # todas las asignaturas del plan son de 6 creditos


def _last_grade(conn: sqlite3.Connection, student_id: str, subject_code: str):
    """Devuelve la nota de la ultima convocatoria registrada (o None)."""
    row = conn.execute(
        """SELECT grade FROM student_grades
           WHERE student_id = ? AND subject_code = ?
           ORDER BY attempt_number DESC, id DESC
           LIMIT 1""",
        (student_id, subject_code),
    ).fetchone()
    return row[0] if row else None


def run() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        attempts = conn.execute(
            """SELECT student_id, subject_code, subject_name, status, last_attempt_year
               FROM student_subject_attempts
               ORDER BY student_id, subject_code"""
        ).fetchall()

        nuevos = []
        for a in attempts:
            status = STATUS_MAP.get(a["status"], a["status"])
            grade = _last_grade(conn, a["student_id"], a["subject_code"])
            semester = f"{a['last_attempt_year']}-1" if a["last_attempt_year"] else None
            nuevos.append({
                "student_id": a["student_id"],
                "subject_code": a["subject_code"],
                "subject_name": a["subject_name"],
                "credits": CREDITS_DEFAULT,
                "grade": grade,
                "semester": semester,
                "status": status,
            })

        # Transaccion: vaciar y reinsertar
        conn.execute("BEGIN")
        conn.execute("DELETE FROM subject_records")
        conn.executemany(
            """INSERT INTO subject_records
               (student_id, subject_code, subject_name, credits, grade, semester, status)
               VALUES (:student_id, :subject_code, :subject_name, :credits, :grade, :semester, :status)""",
            nuevos,
        )
        conn.commit()

        # ── Verificacion post-rebuild ────────────────────────────────────────
        n = conn.execute("SELECT COUNT(*) FROM subject_records").fetchone()[0]
        from collections import Counter
        vocab = Counter(r[0] for r in conn.execute("SELECT status FROM subject_records"))

        # name mismatch en codigos compartidos con student_grades (debe ser 0)
        name_mismatch = conn.execute(
            """SELECT COUNT(*) FROM (
                 SELECT DISTINCT sr.student_id, sr.subject_code
                 FROM subject_records sr
                 JOIN student_grades sg
                   ON sg.student_id = sr.student_id AND sg.subject_code = sr.subject_code
                 WHERE sr.subject_name <> sg.subject_name
               )"""
        ).fetchone()[0]

        # status conflict: subject_records failed/pending pero attempts passed (debe ser 0)
        status_conflict = conn.execute(
            """SELECT COUNT(*) FROM subject_records sr
               JOIN student_subject_attempts a
                 ON a.student_id = sr.student_id AND a.subject_code = sr.subject_code
               WHERE sr.status IN ('failed','pending') AND a.status = 'passed'"""
        ).fetchone()[0]

        print(f"OK - subject_records reconstruida: {n} filas")
        print(f"     status vocab: {dict(vocab)}")
        print(f"     name_mismatch (vs student_grades): {name_mismatch} (esperado 0)")
        print(f"     status_conflict (vs attempts): {status_conflict} (esperado 0)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()

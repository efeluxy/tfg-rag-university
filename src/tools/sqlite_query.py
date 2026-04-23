"""Funciones predefinidas de consulta SQLite para el Agente Student Data.

El LLM nunca escribe SQL directamente. Este módulo expone un conjunto fijo
de funciones con queries seguras y resultados predecibles.
"""

import logging
import os
import sqlite3
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/database/students.db")


def _get_db_path() -> str:
    """Resuelve la ruta absoluta de la base de datos."""
    path = os.getenv("SQLITE_DB_PATH", "data/database/students.db")
    if not os.path.isabs(path):
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, path)
    return path


def get_student_profile(student_id: str) -> dict:
    """Devuelve el perfil básico del alumno: nombre, grado, curso, media, estado.

    Args:
        student_id: Identificador del alumno (ej. 'ALU001').

    Returns:
        Dict con campos name, degree, year, gpa, status, email, credits_completed,
        credits_total, enrolled_year. Si no existe, devuelve {'error': '...'}.
    """
    logger.debug("get_student_profile(%s)", student_id)
    try:
        with sqlite3.connect(_get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """SELECT id, name, email, degree, year, gpa,
                          credits_completed, credits_total, status, enrolled_year
                   FROM students WHERE id = ?""",
                (student_id,),
            ).fetchone()
            if row is None:
                return {"error": f"Alumno '{student_id}' no encontrado en la base de datos."}
            return dict(row)
    except sqlite3.Error as exc:
        logger.error("Error en get_student_profile(%s): %s", student_id, exc)
        return {"error": f"Error de base de datos: {exc}"}


def get_subject_records(student_id: str) -> list[dict]:
    """Devuelve todas las asignaturas del alumno con nota y estado.

    Args:
        student_id: Identificador del alumno.

    Returns:
        Lista de dicts con subject_code, subject_name, credits, grade, semester, status.
        Lista vacía (con clave 'error') si el alumno no existe.
    """
    logger.debug("get_subject_records(%s)", student_id)
    try:
        with sqlite3.connect(_get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT subject_code, subject_name, credits, grade, semester, status
                   FROM subject_records WHERE student_id = ?
                   ORDER BY semester, subject_code""",
                (student_id,),
            ).fetchall()
            if not rows:
                return [{"error": f"No se encontraron asignaturas para '{student_id}'."}]
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("Error en get_subject_records(%s): %s", student_id, exc)
        return [{"error": f"Error de base de datos: {exc}"}]


def get_pending_subjects(student_id: str) -> list[dict]:
    """Devuelve asignaturas con status='pending' o 'failed'.

    Args:
        student_id: Identificador del alumno.

    Returns:
        Lista de dicts con subject_code, subject_name, credits, grade, status.
        Lista vacía si no hay asignaturas pendientes o fallidas.
    """
    logger.debug("get_pending_subjects(%s)", student_id)
    try:
        with sqlite3.connect(_get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT subject_code, subject_name, credits, grade, status, semester
                   FROM subject_records
                   WHERE student_id = ? AND status IN ('pending', 'failed')
                   ORDER BY status, subject_code""",
                (student_id,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("Error en get_pending_subjects(%s): %s", student_id, exc)
        return [{"error": f"Error de base de datos: {exc}"}]


def get_passed_subjects(student_id: str) -> list[dict]:
    """Devuelve asignaturas con status='passed' con su nota.

    Args:
        student_id: Identificador del alumno.

    Returns:
        Lista de dicts con subject_code, subject_name, credits, grade, semester.
    """
    logger.debug("get_passed_subjects(%s)", student_id)
    try:
        with sqlite3.connect(_get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT subject_code, subject_name, credits, grade, semester
                   FROM subject_records
                   WHERE student_id = ? AND status = 'passed'
                   ORDER BY semester, subject_code""",
                (student_id,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("Error en get_passed_subjects(%s): %s", student_id, exc)
        return [{"error": f"Error de base de datos: {exc}"}]


def get_current_enrollments(student_id: str) -> list[dict]:
    """Devuelve asignaturas en las que el alumno está matriculado este semestre.

    Args:
        student_id: Identificador del alumno.

    Returns:
        Lista de dicts con subject_code, subject_name, credits, semester.
    """
    logger.debug("get_current_enrollments(%s)", student_id)
    try:
        with sqlite3.connect(_get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT subject_code, subject_name, credits, semester
                   FROM subject_records
                   WHERE student_id = ? AND status = 'enrolled'
                   ORDER BY subject_code""",
                (student_id,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("Error en get_current_enrollments(%s): %s", student_id, exc)
        return [{"error": f"Error de base de datos: {exc}"}]


def get_scholarships(student_id: str) -> list[dict]:
    """Devuelve becas activas o pendientes del alumno.

    Args:
        student_id: Identificador del alumno.

    Returns:
        Lista de dicts con type, amount, year, status. Lista vacía si no hay becas.
    """
    logger.debug("get_scholarships(%s)", student_id)
    try:
        with sqlite3.connect(_get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT type, amount, year, status
                   FROM scholarships
                   WHERE student_id = ? AND status IN ('active', 'pending')
                   ORDER BY year DESC""",
                (student_id,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("Error en get_scholarships(%s): %s", student_id, exc)
        return [{"error": f"Error de base de datos: {exc}"}]


def get_academic_standing(student_id: str) -> dict:
    """Calcula y devuelve el estado académico completo del alumno.

    Calcula: créditos completados, créditos totales, porcentaje de avance,
    media global de asignaturas superadas y si el alumno está en riesgo académico.

    Args:
        student_id: Identificador del alumno.

    Returns:
        Dict con credits_completed, credits_total, progress_pct, gpa,
        at_risk (bool), status. Si no existe, devuelve {'error': '...'}.
    """
    logger.debug("get_academic_standing(%s)", student_id)
    try:
        with sqlite3.connect(_get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            student = conn.execute(
                "SELECT credits_completed, credits_total, gpa, status FROM students WHERE id = ?",
                (student_id,),
            ).fetchone()
            if student is None:
                return {"error": f"Alumno '{student_id}' no encontrado."}

            credits_completed = student["credits_completed"]
            credits_total = student["credits_total"]
            gpa = student["gpa"]
            status = student["status"]

            progress_pct = round((credits_completed / credits_total) * 100, 1) if credits_total > 0 else 0.0

            # Contar asignaturas suspensas para complementar el riesgo
            failed_count = conn.execute(
                "SELECT COUNT(*) FROM subject_records WHERE student_id = ? AND status = 'failed'",
                (student_id,),
            ).fetchone()[0]

            total_evaluated = conn.execute(
                """SELECT COUNT(*) FROM subject_records
                   WHERE student_id = ? AND status IN ('passed', 'failed')""",
                (student_id,),
            ).fetchone()[0]

            fail_rate = (failed_count / total_evaluated) if total_evaluated > 0 else 0.0

            at_risk = status == "at_risk" or gpa < 5.0 or fail_rate > 0.30

            return {
                "credits_completed": credits_completed,
                "credits_total": credits_total,
                "progress_pct": progress_pct,
                "gpa": gpa,
                "status": status,
                "at_risk": at_risk,
                "failed_subjects_count": failed_count,
                "fail_rate": round(fail_rate, 2),
            }
    except sqlite3.Error as exc:
        logger.error("Error en get_academic_standing(%s): %s", student_id, exc)
        return {"error": f"Error de base de datos: {exc}"}


def get_full_student_record(student_id: str) -> dict:
    """Consolida toda la información del alumno en un único dict estructurado.

    Este es el único método que llama el Agente Student Data al State.

    Args:
        student_id: Identificador del alumno (ej. 'ALU001').

    Returns:
        Dict con claves: profile, academic_standing, passed_subjects,
        pending_subjects, current_enrollments, scholarships.
        Si el alumno no existe, devuelve {'error': '...'}.
    """
    logger.debug("get_full_student_record(%s)", student_id)

    profile = get_student_profile(student_id)
    if "error" in profile:
        return {"error": profile["error"]}

    academic_standing = get_academic_standing(student_id)
    passed_subjects = get_passed_subjects(student_id)
    pending_subjects = get_pending_subjects(student_id)
    current_enrollments = get_current_enrollments(student_id)
    scholarships = get_scholarships(student_id)

    return {
        "profile": {
            "name": profile.get("name"),
            "degree": profile.get("degree"),
            "year": profile.get("year"),
            "gpa": profile.get("gpa"),
            "status": profile.get("status"),
            "email": profile.get("email"),
        },
        "academic_standing": {
            "credits_completed": academic_standing.get("credits_completed", 0),
            "credits_total": academic_standing.get("credits_total", 240),
            "progress_pct": academic_standing.get("progress_pct", 0.0),
            "at_risk": academic_standing.get("at_risk", False),
            "failed_subjects_count": academic_standing.get("failed_subjects_count", 0),
        },
        "passed_subjects": [
            {"code": s["subject_code"], "name": s["subject_name"], "grade": s["grade"]}
            for s in passed_subjects
            if "error" not in s
        ],
        "pending_subjects": [
            {"code": s["subject_code"], "name": s["subject_name"], "status": s["status"]}
            for s in pending_subjects
            if "error" not in s
        ],
        "current_enrollments": [
            {"code": s["subject_code"], "name": s["subject_name"], "semester": s["semester"]}
            for s in current_enrollments
            if "error" not in s
        ],
        "scholarships": [
            {"type": s["type"], "status": s["status"], "amount": s["amount"]}
            for s in scholarships
            if "error" not in s
        ],
    }

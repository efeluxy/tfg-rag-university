"""Agente Student Data: recupera el expediente del alumno desde SQLite.

Implementa tres capas de seguridad:
1. Capa SQL: filtro de permisos antes de consultar la BD.
2. Capa state: flags access_violation_attempted y student_grades.
3. Capa Generator: mensaje de rechazo amable (en generator.py).
"""

import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.graph.state import UniversityAssistantState
from src.tools.sqlite_query import (
    get_full_student_record,
    get_student_grades,
    get_subject_attempts,
)

logger = logging.getLogger(__name__)

_SUBJECT_CODE_RE = re.compile(r"\b[A-Z]{2,4}\d{3,4}[A-Z]?\d*\b")
_ALU_ID_PATTERN = re.compile(r"^ALU\d+$", re.IGNORECASE)
_ATTEMPTS_KEYWORDS = re.compile(
    r"convocatori|intento|veces que he hecho|cuantas veces|me quedan|he gastado",
    re.IGNORECASE,
)
_GRADES_KEYWORDS = re.compile(
    r"nota|calificacion|calificación|puntuacion|puntuación|saque|saco|"
    r"expediente|media|promedio|que tal voy|como voy",
    re.IGNORECASE,
)
_FULL_RECORD_KEYWORDS = re.compile(
    r"expediente|todo|completo|historial completo",
    re.IGNORECASE,
)
_ALU_ID_REGEX = re.compile(r"\bALU\d{3,}\b", re.IGNORECASE)


def _extract_mentioned_student_id(message: str) -> Optional[str]:
    """Detecta si el mensaje menciona explicitamente un ALUxxx."""
    if not message:
        return None
    match = _ALU_ID_REGEX.search(message)
    return match.group(0).upper() if match else None


def _check_access_permission(
    role: str,
    authenticated_user_id: Optional[str],
    target_user_id: Optional[str],
) -> Tuple[bool, str]:
    """Decide si esta sesion puede acceder al expediente de target_user_id.

    Args:
        role: Rol del usuario ("admin" | "student" | "guest").
        authenticated_user_id: ID real del alumno autenticado.
        target_user_id: ID del alumno cuyo expediente se solicita.

    Returns:
        Tuple (allowed: bool, reason: str).
    """
    if role == "admin":
        return True, "admin_access"
    if role == "student":
        if target_user_id == authenticated_user_id:
            return True, "own_record"
        return False, "student_requesting_other"
    if role == "guest":
        if target_user_id is None:
            return True, "guest_no_target"
        return False, "guest_requesting_student"
    return False, "unknown_role"


def run_student_data(state: UniversityAssistantState) -> Dict[str, Any]:
    """Consulta el expediente academico del alumno si es necesario.

    Aplica control de acceso por rol antes de consultar la BD.
    Si se detecta violacion de privacidad, activa el flag
    access_violation_attempted y devuelve datos vacios.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con student_record, subject_attempts, student_grades y
        access_violation_attempted.
    """
    requires = state.get("requires_student_data", False)
    requires_detail = state.get("requires_subject_detail", False)
    user_message = state.get("user_message", "")
    user_id = state.get("user_id") or ""

    # Campos de control de acceso
    role = state.get("role", "guest")
    auth_uid = state.get("authenticated_user_id")

    # Siempre detectar si el mensaje menciona un ALU explicitamente
    mentioned_uid = _extract_mentioned_student_id(user_message)

    logger.info(
        "StudentData: role=%s auth_uid=%s selected_uid=%s "
        "mentioned_uid=%s message='%s'",
        role, auth_uid,
        state.get("user_id"), mentioned_uid,
        user_message[:80],
    )

    # Si el mensaje menciona otro alumno, comprobar permisos SIEMPRE
    # (independientemente de los flags requires_*)
    if mentioned_uid:
        allowed, reason = _check_access_permission(role, auth_uid, mentioned_uid)
        if not allowed:
            logger.warning(
                "ACCESS_VIOLATION: role=%s auth_uid=%s target=%s reason=%s message='%s'",
                role, auth_uid, mentioned_uid, reason, user_message[:100],
            )
            return {
                "student_record": None,
                "subject_attempts": [],
                "student_grades": [],
                "access_violation_attempted": True,
            }

    if not requires and not requires_detail:
        logger.info("Student Data: no se requiere expediente ni detalle")
        return {
            "student_record": None,
            "subject_attempts": None,
            "student_grades": None,
            "access_violation_attempted": False,
        }

    # Determinar el target real (mencionado en mensaje o seleccionado por sesion)
    target_uid = mentioned_uid if mentioned_uid else (user_id or None)

    # Comprobar permisos para el target
    allowed, reason = _check_access_permission(role, auth_uid, target_uid)

    logger.info(
        "StudentData: allowed=%s reason=%s target_uid=%s",
        allowed, reason, target_uid,
    )

    if not allowed:
        logger.warning(
            "ACCESS_VIOLATION: role=%s auth_uid=%s target=%s reason=%s message='%s'",
            role, auth_uid, target_uid, reason, user_message[:100],
        )
        return {
            "student_record": None,
            "subject_attempts": [],
            "student_grades": [],
            "access_violation_attempted": True,
        }

    # Acceso permitido
    if not target_uid:
        logger.info("Student Data: target_uid vacio — omitiendo consulta a BD")
        return {
            "student_record": None,
            "subject_attempts": None,
            "student_grades": None,
            "access_violation_attempted": False,
        }

    record = get_full_student_record(target_uid)
    if "error" in record:
        logger.warning(
            "Student Data: error al obtener expediente de '%s' — %s",
            target_uid, record["error"],
        )
        return {
            "student_record": None,
            "subject_attempts": None,
            "student_grades": None,
            "access_violation_attempted": False,
        }

    logger.info(
        "Student Data: expediente cargado para '%s' — status=%s, gpa=%s",
        target_uid,
        record.get("profile", {}).get("status"),
        record.get("profile", {}).get("gpa"),
    )

    # Detectar si se requieren convocatorias
    subject_attempts = None
    upper_msg = user_message.upper()
    # Filter out ALU student IDs that the regex falsely matches as subject codes
    codes_found = [
        c for c in _SUBJECT_CODE_RE.findall(upper_msg)
        if not _ALU_ID_PATTERN.match(c)
    ]
    has_attempts_kw = bool(_ATTEMPTS_KEYWORDS.search(user_message))
    wants_full_record = bool(_FULL_RECORD_KEYWORDS.search(user_message))

    if codes_found:
        code = codes_found[0]
        subject_attempts = get_subject_attempts(target_uid, code)
    elif has_attempts_kw or requires_detail or wants_full_record:
        subject_attempts = get_subject_attempts(target_uid)

    # Detectar si se piden notas
    student_grades = None
    pide_notas = bool(_GRADES_KEYWORDS.search(user_message))
    if pide_notas:
        subject_code = codes_found[0] if codes_found else None
        student_grades = get_student_grades(target_uid, subject_code=subject_code)
        logger.info(
            "Student Data: notas cargadas para '%s' — %d filas",
            target_uid, len(student_grades),
        )

    logger.info(
        "StudentData: returning record=%s attempts=%d grades=%d violation=%s",
        "yes" if record else "no",
        len(subject_attempts or []),
        len(student_grades or []),
        False,
    )

    return {
        "student_record": record,
        "subject_attempts": subject_attempts,
        "student_grades": student_grades,
        "access_violation_attempted": False,
    }

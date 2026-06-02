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
from typing import Any, Dict, List, Optional, Tuple

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

# ── Patrones de detección ─────────────────────────────────────────────────────

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

# Detección de IDs múltiples y rangos
ALU_ID_REGEX = re.compile(r"\bALU\d{3,}\b", re.IGNORECASE)
ALU_RANGE_REGEX = re.compile(
    r"\b(?:ALU)?0*(\d{1,4})\b"           # primer número
    r"\s*(?:al|a|hasta|-)\s*"            # separador
    r"\b(?:ALU)?0*(\d{1,4})\b",          # segundo número
    re.IGNORECASE,
)

MAX_BATCH_SIZE = 20


# ── Funciones auxiliares ──────────────────────────────────────────────────────

def _extract_mentioned_student_ids(message: str) -> Tuple[List[str], bool]:
    """Devuelve (ids, truncated).

    ids: lista de IDs de alumno detectados en el mensaje, sin duplicados
         y en orden de aparición.
    truncated: True si se aplicó el límite MAX_BATCH_SIZE.
    """
    if not message:
        return [], False

    # 1. Rango numérico primero: "del 1 al 5", "ALU005 a ALU001", "1-5", etc.
    # Tiene prioridad sobre IDs explícitos cuando aparece un separador de rango.
    range_match = ALU_RANGE_REGEX.search(message)
    if range_match:
        try:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
        except ValueError:
            return [], False

        # Normalizar orden si vienen invertidos
        if start > end:
            start, end = end, start

        # Filtros de sanidad
        if start < 1 or end < 1:
            return [], False
        if end > 999:
            end = 999

        total = end - start + 1
        truncated = total > MAX_BATCH_SIZE
        if truncated:
            end = start + MAX_BATCH_SIZE - 1

        ids = [f"ALU{n:03d}" for n in range(start, end + 1)]
        return ids, truncated

    # 2. IDs explícitos (cuando no hay rango)
    explicit_matches = ALU_ID_REGEX.findall(message)
    if explicit_matches:
        seen = set()
        ids = []
        for m in explicit_matches:
            uid = m.upper()
            if uid not in seen:
                seen.add(uid)
                ids.append(uid)
        if len(ids) > MAX_BATCH_SIZE:
            return ids[:MAX_BATCH_SIZE], True
        return ids, False

    return [], False


def _extract_mentioned_student_id(message: str) -> Optional[str]:
    """Alias retrocompatible: devuelve el primer ID detectado."""
    ids, _ = _extract_mentioned_student_ids(message)
    return ids[0] if ids else None


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


def _build_multi_record(uid: str) -> Optional[dict]:
    """Carga y aplana el expediente de un alumno para uso en multi_student_records."""
    full_rec = get_full_student_record(uid)
    if "error" in full_rec:
        logger.warning("StudentData: no se encontro expediente para '%s'", uid)
        return None
    profile = full_rec.get("profile", {})
    standing = full_rec.get("academic_standing", {})
    attempts = get_subject_attempts(uid)
    return {
        "id": uid,
        "name": profile.get("name"),
        "degree": profile.get("degree"),
        "year": profile.get("year"),
        "gpa": profile.get("gpa"),
        "status": profile.get("status"),
        "credits_completed": standing.get("credits_completed", 0),
        "credits_total": standing.get("credits_total", 240),
        "_attempts_summary": {
            "total": len(attempts),
            "passed": sum(1 for a in attempts if a.get("status") == "passed"),
            "failed_last": sum(1 for a in attempts if a.get("status") == "failed_last"),
            "pending": sum(1 for a in attempts if a.get("status") == "pending"),
        },
        "_full_record": full_rec,
    }


# ── Nodo principal ────────────────────────────────────────────────────────────

def run_student_data(state: UniversityAssistantState) -> Dict[str, Any]:
    """Consulta el expediente academico del alumno si es necesario.

    Soporta consultas de uno o varios alumnos (solo admin para múltiples).
    Aplica control de acceso por rol antes de consultar la BD.
    Si se detecta violacion de privacidad, activa access_violation_attempted.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con student_record, subject_attempts, student_grades,
        multi_student_records y access_violation_attempted.
    """
    requires = state.get("requires_student_data", False)
    requires_detail = state.get("requires_subject_detail", False)
    user_message = state.get("user_message", "")
    user_id = state.get("user_id") or ""
    role = state.get("role", "guest")
    auth_uid = state.get("authenticated_user_id")

    # Extraer todos los IDs mencionados (IDs explícitos o rango)
    mentioned_ids, truncated = _extract_mentioned_student_ids(user_message)

    logger.info(
        "StudentData: role=%s auth_uid=%s selected_uid=%s "
        "mentioned_ids=%s truncated=%s message='%s'",
        role, auth_uid, user_id, mentioned_ids, truncated, user_message[:80],
    )

    # ── CASO A: múltiples IDs mencionados ────────────────────────────────────
    if len(mentioned_ids) > 1:
        if role != "admin":
            # Student o guest pidiendo múltiples alumnos → violación
            logger.warning(
                "ACCESS_VIOLATION_MULTI: role=%s auth=%s targets=%s msg='%s'",
                role, auth_uid, mentioned_ids, user_message[:100],
            )
            return {
                "student_record": None,
                "subject_attempts": [],
                "student_grades": [],
                "multi_student_records": None,
                "multi_student_truncated": False,
                "multi_student_limit": 0,
                "access_violation_attempted": True,
            }

        # Admin: cargar todos los expedientes
        multi_records = []
        for uid in mentioned_ids:
            rec = _build_multi_record(uid)
            if rec:
                multi_records.append(rec)

        logger.info(
            "StudentData: %d/%d expedientes cargados (truncated=%s)",
            len(multi_records), len(mentioned_ids), truncated,
        )

        return {
            "student_record": multi_records[0].get("_full_record") if multi_records else None,
            "subject_attempts": None,
            "student_grades": None,
            "multi_student_records": multi_records,
            "multi_student_truncated": truncated,
            "multi_student_limit": MAX_BATCH_SIZE if truncated else 0,
            "access_violation_attempted": False,
        }

    # ── CASO B: un solo ID o ninguno ─────────────────────────────────────────
    mentioned_uid = mentioned_ids[0] if mentioned_ids else None

    # Si el mensaje menciona un ID explícito, comprobar permisos SIEMPRE
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
                "multi_student_records": None,
                "multi_student_truncated": False,
                "multi_student_limit": 0,
                "access_violation_attempted": True,
            }

    if not requires and not requires_detail:
        logger.info("Student Data: no se requiere expediente ni detalle")
        return {
            "student_record": None,
            "subject_attempts": None,
            "student_grades": None,
            "multi_student_records": None,
            "multi_student_truncated": False,
            "multi_student_limit": 0,
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
            "multi_student_records": None,
            "multi_student_truncated": False,
            "multi_student_limit": 0,
            "access_violation_attempted": True,
        }

    # Acceso permitido
    if not target_uid:
        logger.info("Student Data: target_uid vacio — omitiendo consulta a BD")
        return {
            "student_record": None,
            "subject_attempts": None,
            "student_grades": None,
            "multi_student_records": None,
            "multi_student_truncated": False,
            "multi_student_limit": 0,
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
            "multi_student_records": None,
            "multi_student_truncated": False,
            "multi_student_limit": 0,
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
    # Filtrar IDs de alumno que el regex confunde con códigos de asignatura
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
        "multi_student_records": None,
        "multi_student_truncated": False,
        "multi_student_limit": 0,
        "access_violation_attempted": False,
    }

"""Agente Student Data: recupera el expediente del alumno desde SQLite."""

import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.graph.state import UniversityAssistantState
from src.tools.sqlite_query import get_full_student_record, get_subject_attempts

logger = logging.getLogger(__name__)

_SUBJECT_CODE_RE = re.compile(r"\b[A-Z]{2,4}\d{3,4}[A-Z]?\d*\b")
_ATTEMPTS_KEYWORDS = re.compile(
    r"convocatori|intento|veces que he hecho|cuantas veces|me quedan|he gastado",
    re.IGNORECASE,
)


def run_student_data(state: UniversityAssistantState) -> Dict[str, Any]:
    """Consulta el expediente academico del alumno si es necesario.

    Ademas, detecta si el mensaje menciona codigos de asignatura o
    palabras clave de convocatorias y carga el detalle de intentos.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con student_record (dict completo o None) y
        subject_attempts (lista de dicts o None).
    """
    requires = state.get("requires_student_data", False)
    requires_detail = state.get("requires_subject_detail", False)
    user_message = state.get("user_message", "")
    user_id = state.get("user_id") or ""

    if not requires and not requires_detail:
        logger.info("Student Data: no se requiere expediente ni detalle")
        return {"student_record": None, "subject_attempts": None}

    if not user_id:
        logger.info("Student Data: user_id vacio — omitiendo consulta a BD")
        return {"student_record": None, "subject_attempts": None}

    record = get_full_student_record(user_id)
    if "error" in record:
        logger.warning(
            "Student Data: error al obtener expediente de '%s' — %s",
            user_id, record["error"],
        )
        return {"student_record": None, "subject_attempts": None}

    logger.info(
        "Student Data: expediente cargado para '%s' — status=%s, gpa=%s",
        user_id,
        record.get("profile", {}).get("status"),
        record.get("profile", {}).get("gpa"),
    )

    # Detectar si se requieren convocatorias
    subject_attempts = None
    upper_msg = user_message.upper()
    codes_found = _SUBJECT_CODE_RE.findall(upper_msg)
    has_attempts_kw = bool(_ATTEMPTS_KEYWORDS.search(user_message))

    if codes_found:
        code = codes_found[0]
        subject_attempts = get_subject_attempts(user_id, code)
        logger.info(
            "Student Data: convocatorias cargadas para '%s' / '%s' — %d filas",
            user_id, code, len(subject_attempts),
        )
    elif has_attempts_kw or requires_detail:
        subject_attempts = get_subject_attempts(user_id)
        logger.info(
            "Student Data: todas las convocatorias cargadas para '%s' — %d filas",
            user_id, len(subject_attempts),
        )

    return {"student_record": record, "subject_attempts": subject_attempts}

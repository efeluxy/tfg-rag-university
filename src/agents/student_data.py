"""Agente Student Data: recupera el expediente del alumno desde SQLite."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.graph.state import UniversityAssistantState
from src.tools.sqlite_query import get_full_student_record

logger = logging.getLogger(__name__)


def run_student_data(state: UniversityAssistantState) -> Dict[str, Any]:
    """Consulta el expediente académico del alumno si es necesario.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con student_record (dict completo o None).
    """
    requires = state.get("requires_student_data", False)
    user_id = state.get("user_id") or ""

    if not requires:
        logger.info("Student Data: no se requiere expediente (requires_student_data=False)")
        return {"student_record": None}

    if not user_id:
        logger.info("Student Data: user_id vacío o None — omitiendo consulta a BD")
        return {"student_record": None}

    record = get_full_student_record(user_id)

    if "error" in record:
        logger.warning("Student Data: error al obtener expediente de '%s' — %s", user_id, record["error"])
        return {"student_record": None}

    logger.info(
        "Student Data: expediente cargado para '%s' — status=%s, gpa=%s",
        user_id,
        record.get("profile", {}).get("status"),
        record.get("profile", {}).get("gpa"),
    )
    return {"student_record": record}

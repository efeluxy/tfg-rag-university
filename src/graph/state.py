"""TypedDict del State compartido por todos los nodos del grafo LangGraph."""

import operator
from typing import Annotated, List, Optional, TypedDict

VALID_INTENTS = [
    "ACADEMIC_ORIENTATION",
    "ADMINISTRATIVE",
    "COURSE_INFO",
    "REGULATIONS",
    "PROSPECTIVE_STUDENT",
    "SCHOLARSHIPS",
    "EMOTIONAL_SUPPORT",
    "OUT_OF_SCOPE",
    "GREETING",
]


class UniversityAssistantState(TypedDict):
    # ── Entrada del usuario ──────────────────────────────────────────
    user_message:            str
    user_id:                 Optional[str]
    session_id:              str

    # ── Clasificación del Router ─────────────────────────────────────
    intent:                  Optional[str]
    key_points:              List[str]
    requires_student_data:   bool
    router_reasoning:        Optional[str]

    # ── Resultado del Guardrail ──────────────────────────────────────
    guardrail_triggered:     bool
    guardrail_reason:        Optional[str]   # "out_of_scope" | "emotional_crisis"
                                             # | "inappropriate" | None
    # ── Contexto recuperado ─────────────────────────────────────────
    retrieved_docs:          List[dict]      # lista de dicts con content,
                                             # title, section, source_file,
                                             # page_number, relevance_score, citation
    search_queries:          List[str]

    # ── Expediente del alumno ────────────────────────────────────────
    student_record:          Optional[dict]  # salida de get_full_student_record()

    # ── Respuesta final ──────────────────────────────────────────────
    final_response:          Optional[str]
    sources:                 List[str]
    confidence:              float

    # ── Historial de conversación ────────────────────────────────────
    message_history:         Annotated[List[dict], operator.add]


def get_initial_state(
    user_message: str,
    session_id: str,
    user_id: Optional[str] = None,
) -> UniversityAssistantState:
    """Crea un State inicial limpio para una nueva consulta."""
    return UniversityAssistantState(
        user_message=user_message,
        user_id=user_id,
        session_id=session_id,
        intent=None,
        key_points=[],
        requires_student_data=False,
        router_reasoning=None,
        guardrail_triggered=False,
        guardrail_reason=None,
        retrieved_docs=[],
        search_queries=[],
        student_record=None,
        final_response=None,
        sources=[],
        confidence=0.0,
        message_history=[],
    )

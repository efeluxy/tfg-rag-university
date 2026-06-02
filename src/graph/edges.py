"""Funciones de decisión condicional del grafo LangGraph.

Cada función recibe el State completo y devuelve el nombre del siguiente nodo.
Ninguna función modifica el State.
"""

import re

from src.graph.state import UniversityAssistantState

_ALU_ID_RE = re.compile(r"\bALU\d{3,}\b", re.IGNORECASE)


def route_after_router(state: UniversityAssistantState) -> str:
    """Decide si después del Router se activa el Guardrail.

    Siempre pasa por el Guardrail — es obligatorio para toda consulta.

    Returns:
        "guardrail" siempre.
    """
    return "guardrail"


def route_after_guardrail(state: UniversityAssistantState) -> str:
    """Decide el flujo despues del Guardrail.

    - Tier 3 (crisis_grave): bypass directo a generator con respuesta predefinida.
    - out_of_scope / inapropiado (guardrail_triggered + safe_response ya en state):
      bypass a generator.
    - Tier 1 / 2: pasar por retriever para enriquecer con recursos del corpus.
    - Resto (tier 0, flujo normal): retriever.

    Returns:
        "generator" | "retriever"
    """
    emotional_tier = state.get("emotional_tier", 0)
    guardrail_triggered = state.get("guardrail_triggered", False)
    guardrail_reason = state.get("guardrail_reason", "")

    if emotional_tier == 3:
        return "generator"
    if guardrail_triggered and guardrail_reason == "out_of_scope":
        return "generator"
    if guardrail_triggered and guardrail_reason == "inappropriate":
        return "generator"
    return "retriever"


def route_after_retriever(state: UniversityAssistantState) -> str:
    """Decide si después del Retriever se consulta el expediente del alumno.

    Routea a student_data si:
    - requires_student_data=True o requires_subject_detail=True y hay user_id, O
    - El mensaje menciona explicitamente un ALU ID (para control de acceso).

    Returns:
        "student_data" | "generator"
    """
    requires = state.get("requires_student_data", False)
    requires_detail = state.get("requires_subject_detail", False)
    user_id = state.get("user_id")
    user_message = state.get("user_message", "")

    if (requires or requires_detail) and user_id and str(user_id).strip():
        return "student_data"

    # Siempre pasar por student_data si el mensaje menciona un ALU ID
    # (para aplicar control de acceso aunque requires sea False)
    if _ALU_ID_RE.search(user_message):
        return "student_data"

    return "generator"

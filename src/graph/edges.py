"""Funciones de decisión condicional del grafo LangGraph.

Cada función recibe el State completo y devuelve el nombre del siguiente nodo.
Ninguna función modifica el State.
"""

from src.graph.state import UniversityAssistantState


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

    - Si requires_student_data=True Y user_id no es None ni vacío:
      ir a "student_data".
    - En cualquier otro caso: ir directamente a "generator".

    Returns:
        "student_data" | "generator"
    """
    requires = state.get("requires_student_data", False)
    user_id = state.get("user_id")
    if requires and user_id and str(user_id).strip():
        return "student_data"
    return "generator"

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
    """Decide el flujo después del Guardrail.

    - Si guardrail_triggered=True: ir directamente a "generator"
      (el Guardrail ya puso safe_response en final_response).
    - Si guardrail_triggered=False: ir a "retriever" para buscar
      información en Azure AI Search.

    Returns:
        "generator" | "retriever"
    """
    if state.get("guardrail_triggered", False):
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

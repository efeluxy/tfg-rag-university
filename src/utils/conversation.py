"""Utilidades para gestion del historial conversacional."""

MAX_HISTORY_TURNS = 6  # 3 intercambios = 3 user + 3 assistant


def get_recent_history(
    messages: list[dict],
    max_turns: int = MAX_HISTORY_TURNS,
) -> list[dict]:
    """Devuelve los ultimos N mensajes (excluyendo el actual).

    Solo conserva role + content, descarta sources, confidence, etc.

    Args:
        messages: Lista de mensajes del historial completo.
        max_turns: Numero maximo de turnos a conservar.

    Returns:
        Lista de dicts con role y content.
    """
    if not messages:
        return []
    history = messages[-(max_turns + 1):-1] if len(messages) > 1 else []
    return [
        {"role": m.get("role"), "content": m.get("content", "")[:1000]}
        for m in history
        if m.get("role") in ("user", "assistant")
    ]


def format_history_for_llm(history: list[dict]) -> str:
    """Convierte historial a un string legible para inyectar en prompts.

    Args:
        history: Lista de dicts con role y content.

    Returns:
        String con el historial formateado, o string vacio si no hay historial.
    """
    if not history:
        return ""
    lines = ["── HISTORIAL DE LA CONVERSACION ──"]
    for m in history:
        role = "Usuario" if m.get("role") == "user" else "Asistente"
        lines.append(f"{role}: {m.get('content', '')}")
    lines.append("── FIN DEL HISTORIAL ──")
    return "\n".join(lines)

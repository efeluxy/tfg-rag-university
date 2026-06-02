"""Utilidades para gestion del historial conversacional."""

MAX_HISTORY_TURNS = 6  # 3 intercambios = 3 user + 3 assistant

# Patrones que indican respuesta de "sin datos" o error.
# Si una respuesta del asistente coincide, se EXCLUYE del historial.
NO_DATA_PATTERNS = (
    "no tengo informacion",
    "no tengo información",
    "no dispongo de informacion",
    "no dispongo de información",
    "no dispongo de info",
    "no dispongo de datos",
    "no dispongo",
    "no puedo acceder",
    "no tengo acceso",
    "no esta en mi base",
    "no está en mi base",
    "informacion no disponible",
    "información no disponible",
    "no esta disponible",
    "no está disponible",
    "no encuentro",
    "no consta",
    "no tengo registros",
)


def is_no_data_response(content: str) -> bool:
    """True si la respuesta del asistente es de tipo 'sin datos'."""
    if not content:
        return False
    c = content.lower()
    return any(p in c for p in NO_DATA_PATTERNS)


def get_recent_history(
    messages: list[dict],
    max_turns: int = MAX_HISTORY_TURNS,
) -> list[dict]:
    """Devuelve los ultimos N mensajes filtrando respuestas de error.

    Cuando una respuesta del asistente es de tipo 'sin datos',
    se elimina junto con el mensaje del usuario que la precede,
    para mantener coherencia conversacional.

    Args:
        messages: Lista de mensajes del historial completo.
        max_turns: Numero maximo de turnos a conservar.

    Returns:
        Lista de dicts con role y content (sin respuestas de error).
    """
    if not messages:
        return []

    # Excluir el último (es el mensaje actual del usuario)
    raw = messages[-(max_turns + 1):-1] if len(messages) > 1 else []

    # Filtrar pares user+assistant donde el asistente dice "no tengo datos"
    filtered = []
    i = 0
    while i < len(raw):
        m = raw[i]
        role = m.get("role")
        content = m.get("content", "")
        # Caso: user seguido de assistant "sin datos" → saltar ambos
        if (
            role == "user"
            and i + 1 < len(raw)
            and raw[i + 1].get("role") == "assistant"
            and is_no_data_response(raw[i + 1].get("content", ""))
        ):
            i += 2
            continue
        # Caso normal: añadir y truncar contenido
        filtered.append({
            "role": role,
            "content": content[:1000],
        })
        i += 1
    return filtered


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

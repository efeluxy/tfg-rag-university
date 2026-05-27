"""Helper para generar HTML de fuentes citadas."""


def format_sources_html(sources: list) -> str:
    """Genera HTML con una línea por fuente. Devuelve string vacío si la lista está vacía."""
    if not sources:
        return ""
    lines = [f"<p style='margin:4px 0;'>📄 {s}</p>" for s in sources]
    return "\n".join(lines)

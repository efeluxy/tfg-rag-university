"""Normalizacion de LaTeX para el render del chat en Streamlit.

Streamlit (``st.markdown``) solo renderiza matematicas cuando las expresiones
van delimitadas por ``$...$`` (en linea) o ``$$...$$`` (en bloque). El modelo,
en cambio, a veces devuelve las formulas como ``\\[ ... \\]``, ``\\( ... \\)`` o
directamente comandos sueltos (``\\frac{a}{b}``, ``x_{i}``, ``\\sqrt{x}``...)
sin ningun delimitador de dolar. Este modulo convierte esa presentacion a la
sintaxis que Streamlit entiende, SIN alterar el contenido real del mensaje.

Es un cambio de PRESENTACION: no depende de Azure ni del grafo y no usa
dependencias externas (solo ``re`` de la libreria estandar).
"""

from __future__ import annotations

import re

# --- Bloques de construccion de expresiones ------------------------------------

# Un grupo entre llaves, admitiendo un nivel de anidamiento ({a}, {\bar{x}}...).
_BRACE = r"\{(?:[^{}]|\{[^{}]*\})*\}"

# Una "unidad" matematica: un comando LaTeX, un grupo de llaves, un
# subindice/superindice, un caracter alfanumerico o un operador simple.
_ATOM = r"(?:\\[A-Za-z]+|" + _BRACE + r"|[_^]|[A-Za-z0-9]|[+\-*/=().,])"

# Un tramo candidato a formula: una secuencia CONTIGUA de unidades (sin espacios
# de nivel superior; los espacios internos van siempre dentro de las llaves).
_RUN = re.compile(_ATOM + r"+")

# Un tramo solo se envuelve si contiene un "disparador" real de matematicas:
# un comando LaTeX (\algo) o un subindice/superindice (_ o ^). Asi el texto
# normal (palabras, "7+8/2", etc.) NO se envuelve. Conservador a proposito.
_TRIGGER = re.compile(r"\\[A-Za-z]|[_^]")

# Delimitadores estilo LaTeX a convertir a dolar.
_BRACKET_DISPLAY = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)   # \[ ... \] -> $$ ... $$
_BRACKET_INLINE = re.compile(r"\\\((.*?)\\\)", re.DOTALL)    # \( ... \) -> $ ... $

# Spans de matematicas ya delimitadas, para protegerlas (evita duplicar y
# garantiza idempotencia). $$...$$ primero (mas largo), luego $...$.
_MATH_BLOCK = re.compile(r"\$\$.+?\$\$", re.DOTALL)
_MATH_INLINE = re.compile(r"(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)", re.DOTALL)

# Puntuacion final de frase que no forma parte de la formula.
_TRAILING_PUNCT = ".,;:!?"


def _wrap_runs(segment: str) -> str:
    """Envuelve en ``$...$`` los tramos de ``segment`` que sean formula suelta."""

    def _replace(match: re.Match) -> str:
        run = match.group(0)
        if not _TRIGGER.search(run):
            # No es formula (no hay comando ni sub/superindice): dejar intacto.
            return run
        # Mover la puntuacion final de frase fuera del $...$ (salvo decimales).
        trailing = ""
        while (
            len(run) >= 2
            and run[-1] in _TRAILING_PUNCT
            and not (run[-1] == "." and run[-2].isdigit())
        ):
            trailing = run[-1] + trailing
            run = run[:-1]
        if not run:
            return match.group(0)
        return f"${run}$" + trailing

    return _RUN.sub(_replace, segment)


def normalize_latex(text: str) -> str:
    """Normaliza la presentacion LaTeX de ``text`` para Streamlit.

    Transforma:
      * ``\\[ ... \\]``  ->  ``$$ ... $$``  (bloque)
      * ``\\( ... \\)``  ->  ``$ ... $``    (en linea)
      * comandos sueltos (``\\frac{a}{b}``, ``x_{i}``, ``\\sqrt{x}``, ``\\bar{x}``,
        ``\\times``, ``\\cdot``, ``\\leq``, ``x^{2}``...) sin delimitar  ->  ``$...$``

    Es conservadora (ante la duda NO envuelve; el texto sin matematicas se
    devuelve intacto) e idempotente (aplicarla dos veces no rompe el resultado:
    lo que ya iba en ``$...$`` o ``$$...$$`` se respeta y no se re-envuelve).

    Args:
        text: El contenido del mensaje del asistente tal cual lo produjo el modelo.

    Returns:
        El mismo texto con las formulas delimitadas de forma que Streamlit las
        renderice. No se modifica ninguna otra parte del texto.
    """
    if not text or "\\" not in text and "$" not in text and "_" not in text and "^" not in text:
        # Sin ningun indicio de matematicas: devolver intacto (rapido y seguro).
        return text or ""

    # 1) Convertir delimitadores estilo LaTeX a dolar.
    text = _BRACKET_DISPLAY.sub(lambda m: "$$" + m.group(1) + "$$", text)
    text = _BRACKET_INLINE.sub(lambda m: "$" + m.group(1) + "$", text)

    # 2) Proteger las matematicas ya delimitadas (idempotencia / no duplicar).
    protected: list[str] = []

    def _protect(match: re.Match) -> str:
        protected.append(match.group(0))
        return f"\x00{len(protected) - 1}\x00"

    text = _MATH_BLOCK.sub(_protect, text)
    text = _MATH_INLINE.sub(_protect, text)

    # 3) Envolver los tramos de formula suelta en el texto restante.
    text = _wrap_runs(text)

    # 4) Restaurar las matematicas protegidas.
    def _restore(match: re.Match) -> str:
        return protected[int(match.group(1))]

    text = re.sub(r"\x00(\d+)\x00", _restore, text)

    return text

"""Tests offline de la normalizacion LaTeX para el render del chat.

No dependen de Azure ni del grafo: solo ejercitan ``normalize_latex``, que es
una funcion pura de presentacion. Cubren los 5 casos del prompt de fix LaTeX.
"""

import sys
from pathlib import Path

# Permitir importar el paquete app/ al ejecutar pytest desde la raiz del repo.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.latex import normalize_latex


def test_caso1_frac_suelto_se_envuelve():
    """Un \\frac{a}{b} sin delimitar queda envuelto en $...$."""
    out = normalize_latex("La media es \\frac{a}{b} al final.")
    assert "$\\frac{a}{b}$" in out


def test_caso2_display_bracket_a_doble_dolar():
    """\\[ x = 1 \\] se convierte en $$ x = 1 $$."""
    assert normalize_latex("\\[ x = 1 \\]") == "$$ x = 1 $$"


def test_caso3_inline_bracket_a_dolar():
    """\\( y = 2 \\) se convierte en $ y = 2 $."""
    assert normalize_latex("\\( y = 2 \\)") == "$ y = 2 $"


def test_caso4_idempotencia_no_duplica_delimitadores():
    """Una formula ya en $...$ no se re-envuelve (idempotente)."""
    entrada = "$\\frac{a}{b}$"
    una_vez = normalize_latex(entrada)
    dos_veces = normalize_latex(una_vez)
    assert una_vez == entrada
    assert dos_veces == entrada
    assert "$$" not in una_vez  # no se han duplicado los delimitadores


def test_caso5_texto_normal_intacto():
    """El texto sin matematicas se devuelve exactamente igual."""
    texto = "La nota media del alumno es notable y va bien."
    assert normalize_latex(texto) == texto


def test_idempotencia_general_en_todos_los_casos():
    """Aplicar la normalizacion dos veces nunca cambia el resultado."""
    ejemplos = [
        "La media es \\frac{a}{b} al final.",
        "\\[ x = 1 \\]",
        "\\( y = 2 \\)",
        "$\\frac{a}{b}$",
        "La nota media del alumno es notable.",
        "x_{i} y x^{2} son variables",
        "a \\times b = c",
    ]
    for texto in ejemplos:
        una = normalize_latex(texto)
        assert una == normalize_latex(una), f"No idempotente: {texto!r}"


# --- Tests para identificadores snake_case (fix at_risk) ----------------------


def test_snake_case_at_risk_intacto():
    """'at_risk' se devuelve literal, sin $...$ y sin subindice."""
    out = normalize_latex("estado at_risk")
    assert "at_risk" in out
    assert "$" not in out


def test_snake_case_student_id_intacto():
    """'student_id' se devuelve intacto como texto plano."""
    out = normalize_latex("campo student_id del expediente")
    assert "student_id" in out
    assert "$" not in out


def test_subindice_con_llaves_se_envuelve():
    """x_{i} (con llaves) se sigue tratando como subindice correctamente."""
    out = normalize_latex("x_{i}")
    assert "$x_{i}$" == out


def test_frac_suelto_se_sigue_envolviendo():
    """\\frac{a}{b} suelto se sigue envolviendo en $...$."""
    out = normalize_latex("\\frac{a}{b}")
    assert out == "$\\frac{a}{b}$"


def test_idempotencia_mezcla_snake_case_y_formula():
    """Idempotencia sobre texto que mezcla at_risk y \\frac{a}{b}."""
    texto = "estado at_risk con \\frac{a}{b}"
    una = normalize_latex(texto)
    dos = normalize_latex(una)
    assert una == dos
    assert "at_risk" in una
    assert "$" not in una.split("at_risk")[0].split()[-1] if una.split("at_risk")[0] else True
    assert "$\\frac{a}{b}$" in una

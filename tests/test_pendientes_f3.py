"""Tests offline del fix F3 (asignaturas pendientes).

No dependen de Azure ni del grafo: ejercitan solo el detector de keywords
(_GRADES_KEYWORDS) y el formateo de contexto (format_student_context) con un
student_record simulado. Cubren deteccion, formateo completo y no-regresion.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.student_data import _GRADES_KEYWORDS
from src.prompts.generator_prompt import format_student_context


def _detecta(texto: str) -> bool:
    """True si el detector decide cargar el detalle de asignaturas."""
    return bool(_GRADES_KEYWORDS.search(texto))


# --- Test A: deteccion de consultas de pendientes ------------------------------

def test_a_deteccion_pendientes():
    assert _detecta("Que asignaturas tengo pendientes?")
    assert _detecta("cuales me quedan pendientes?")
    assert _detecta("que asignaturas tengo suspensas?")


# --- Test B: formateo completo con codigo y creditos ---------------------------

def test_b_formateo_incluye_todas_con_codigo_y_creditos():
    record = {
        "profile": {"name": "Test Alumno", "degree": "Informatica", "year": 2,
                    "gpa": 4.2, "status": "at_risk"},
        "academic_standing": {"credits_completed": 60, "credits_total": 240,
                              "progress_pct": 25.0},
        "pending_subjects": [
            {"code": "INF101", "name": "Programacion I", "credits": 6, "status": "failed"},
            {"code": "INF102", "name": "Matematicas I", "credits": 6, "status": "failed"},
            {"code": "INF206", "name": "Ingenieria del Software I", "credits": 6, "status": "pending"},
            {"code": "INF210", "name": "Programacion Orientada a Objetos", "credits": 6, "status": "pending"},
        ],
        "scholarships": [],
    }
    ctx = format_student_context(record)

    # Las 4 asignaturas aparecen (no solo 3): comprobar codigos.
    for code in ("INF101", "INF102", "INF206", "INF210"):
        assert code in ctx, f"Falta {code} en el contexto"

    # Incluye nombre y creditos de cada una.
    assert "Programacion I" in ctx
    assert "(6 creditos)" in ctx

    # Se listan las 4 lineas de detalle (una por asignatura).
    assert ctx.count("(6 creditos)") == 4

    # NO se trunca a 3: la 4a asignatura esta presente.
    assert "INF210" in ctx


# --- Test C: no-regresion (el detector sigue siendo selectivo) -----------------

def test_c_no_regresion_texto_no_relacionado():
    assert not _detecta("Cuentame sobre las actividades extraescolares del campus.")
    assert not _detecta("Donde esta la cafeteria de la facultad?")


# --- Extra: idempotencia/robustez sin creditos ---------------------------------

def test_d_pendientes_sin_creditos_no_rompe():
    record = {
        "profile": {"name": "X", "degree": "-", "year": 1, "gpa": 5.0, "status": "ok"},
        "academic_standing": {"credits_completed": 0, "credits_total": 240, "progress_pct": 0.0},
        "pending_subjects": [{"code": "AAA111", "name": "Sin creditos", "status": "pending"}],
        "scholarships": [],
    }
    ctx = format_student_context(record)
    assert "AAA111" in ctx and "Sin creditos" in ctx

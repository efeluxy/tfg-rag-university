"""Fixtures compartidas para los tests de la Fase 5.

Proporciona:
  - graph: grafo compilado (scope=module, se crea una sola vez)
  - initial_state_factory: funcion get_initial_state
  - test_cases: lista de casos de tests/test_cases.json
  - db_path: ruta a students.db
"""

import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Silenciar logs ruidosos durante tests
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("azure").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)


def pytest_configure(config):
    """Registrar marcadores personalizados."""
    config.addinivalue_line(
        "markers",
        "integration: tests que requieren conectividad con Azure (pueden saltarse con -m 'not integration')"
    )


@pytest.fixture(scope="session")
def graph():
    """Grafo compilado. Se crea una sola vez por sesion de tests."""
    try:
        from src.graph.graph import build_graph
        return build_graph()
    except Exception as exc:
        pytest.skip(f"No se pudo compilar el grafo: {exc}")


@pytest.fixture(scope="session")
def initial_state_factory():
    """Devuelve la funcion get_initial_state del sistema."""
    from src.graph.state import get_initial_state
    return get_initial_state


@pytest.fixture(scope="session")
def test_cases():
    """Lista de casos de tests/test_cases.json."""
    cases_path = ROOT / "tests" / "test_cases.json"
    with open(cases_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def db_path():
    """Ruta absoluta a la base de datos de alumnos."""
    from src.config.settings import SQLITE_DB_PATH
    path = SQLITE_DB_PATH
    if not Path(path).is_absolute():
        path = str(ROOT / path)
    return path


@pytest.fixture(scope="session")
def sqlite_functions():
    """Devuelve todas las funciones de consulta SQLite del sistema."""
    from src.tools.sqlite_query import (
        get_student_profile,
        get_subject_records,
        get_pending_subjects,
        get_passed_subjects,
        get_current_enrollments,
        get_scholarships,
        get_academic_standing,
        get_full_student_record,
    )
    return {
        "get_student_profile": get_student_profile,
        "get_subject_records": get_subject_records,
        "get_pending_subjects": get_pending_subjects,
        "get_passed_subjects": get_passed_subjects,
        "get_current_enrollments": get_current_enrollments,
        "get_scholarships": get_scholarships,
        "get_academic_standing": get_academic_standing,
        "get_full_student_record": get_full_student_record,
    }

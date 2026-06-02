# -*- coding: utf-8 -*-
"""Tests de la tabla student_grades y consultas de notas."""

import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.sqlite_query import get_student_grades
from src.graph.graph import get_graph
from src.graph.state import get_initial_state

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_grades_{date.today():%Y%m%d}.txt"
)


def _invoke(graph, message, user_id=None, role="student", auth_uid=None):
    sid = str(uuid.uuid4())
    s = get_initial_state(
        message, sid, user_id=user_id,
        role=role, authenticated_user_id=auth_uid or user_id,
    )
    return graph.invoke(s, config={"configurable": {"thread_id": sid}})


def test_g01_sergio_nota_inf101():
    """Sergio pregunta 'Que nota saque en INF101' -> menciona nota real."""
    graph = get_graph()
    r = _invoke(graph, "Que nota saque en INF101?", user_id="ALU015")
    resp = r.get("final_response", "")
    resp_lower = resp.lower()
    assert (
        "inf101" in resp_lower or "algoritmica" in resp_lower or "algoritm" in resp_lower
    ), f"No menciona INF101: {resp[:300]}"
    # Debe haber un numero (nota)
    import re
    has_number = bool(re.search(r"\d+[.,]\d+|\b\d{1,2}\b", resp))
    assert has_number, f"No menciona nota numerica: {resp[:300]}"
    return True


def test_g02_carlos_todas_notas():
    """Carlos pregunta sus notas -> lista con varias asignaturas."""
    graph = get_graph()
    r = _invoke(graph, "Cuales son mis notas?", user_id="ALU001")
    resp = r.get("final_response", "")
    assert len(resp) > 150, f"Respuesta demasiado corta: {len(resp)}"
    # Debe mencionar al menos una asignatura de informatica
    resp_lower = resp.lower()
    assert (
        "inf" in resp_lower or "algoritm" in resp_lower or "programacion" in resp_lower
        or "estructuras" in resp_lower or "bases" in resp_lower
    ), f"No menciona asignaturas INF: {resp[:300]}"
    return True


def test_g03_tabla_tiene_suficientes_filas():
    """student_grades tiene >= 800 filas."""
    from src.tools.sqlite_query import _get_db_path
    import sqlite3
    with sqlite3.connect(_get_db_path()) as conn:
        count = conn.execute("SELECT COUNT(*) FROM student_grades").fetchone()[0]
    assert count >= 800, f"Solo hay {count} filas en student_grades"
    return True


def test_g04_get_grades_alu001():
    """get_student_grades('ALU001') devuelve lista no vacia."""
    grades = get_student_grades("ALU001")
    assert len(grades) > 0, "ALU001 no tiene notas"
    return True


def test_g05_max_4_intentos_por_asignatura():
    """get_student_grades('ALU001', 'INF101') devuelve <= 4 filas."""
    grades = get_student_grades("ALU001", "INF101")
    assert len(grades) <= 4, f"Mas de 4 intentos para INF101: {len(grades)}"
    return True


def test_g06_alu001_notas_altas():
    """ALU001 (excellent) tiene mayoria de notas >= 7."""
    grades = get_student_grades("ALU001")
    if not grades:
        return False
    passed = [g for g in grades if g.get("passed")]
    if not passed:
        return False
    avg = sum(g["grade"] for g in passed) / len(passed)
    assert avg >= 7.0, f"Media de ALU001 en aprobadas: {avg:.1f}"
    return True


CASOS = [
    ("G01", "Sergio nota INF101 -> menciona codigo y numero", test_g01_sergio_nota_inf101),
    ("G02", "Carlos todas notas -> lista con asignaturas", test_g02_carlos_todas_notas),
    ("G03", "student_grades >= 800 filas", test_g03_tabla_tiene_suficientes_filas),
    ("G04", "get_student_grades(ALU001) no vacio", test_g04_get_grades_alu001),
    ("G05", "INF101 <= 4 convocatorias", test_g05_max_4_intentos_por_asignatura),
    ("G06", "ALU001 excellent: media >= 7 en aprobadas", test_g06_alu001_notas_altas),
]


def run():
    lines = ["=== TEST GRADES ==="]
    resultados = []
    for cid, desc, fn in CASOS:
        try:
            ok = fn()
        except AssertionError as e:
            lines.append(f"  [{cid}] {desc:<50} FAIL: {e}")
            resultados.append(False)
            continue
        except Exception as e:
            lines.append(f"  [{cid}] {desc:<50} ERROR: {e}")
            resultados.append(False)
            continue
        estado = "PASS" if ok else "FAIL"
        lines.append(f"  [{cid}] {desc:<50} {estado}")
        resultados.append(bool(ok))
    total = sum(resultados)
    lines.append(f"TOTAL: {total}/{len(CASOS)} PASS")
    output = "\n".join(lines)
    print(output)
    LOG_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.write_text(output + "\n", encoding="utf-8")
    return total


if __name__ == "__main__":
    run()

# -*- coding: utf-8 -*-
"""Tests del modulo de sinonimos y su integracion en el Retriever."""

import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.synonyms import expand_query_with_synonyms
from src.graph.graph import get_graph
from src.graph.state import get_initial_state

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_synonyms_{date.today():%Y%m%d}.txt"
)


def _invoke(graph, message, user_id=None, role="student", auth_uid=None):
    sid = str(uuid.uuid4())
    s = get_initial_state(
        message, sid, user_id=user_id,
        role=role, authenticated_user_id=auth_uid or user_id,
    )
    return graph.invoke(s, config={"configurable": {"thread_id": sid}})


def test_y01_carrera_expande_grado():
    """'carrera' en query -> salida contiene 'grado'."""
    result = expand_query_with_synonyms("que carrera estoy cursando")
    assert "grado" in result, f"'grado' no en: {result}"
    return True


def test_y02_notas_expande_calificacion():
    """'notas' en query -> salida contiene 'calificacion'."""
    result = expand_query_with_synonyms("cuales son mis notas")
    assert "calificacion" in result, f"'calificacion' no en: {result}"
    return True


def test_y03_hola_no_cambia():
    """Consulta sin sinonimos -> sin cambios."""
    result = expand_query_with_synonyms("hola")
    assert result == "hola", f"'hola' no deberia cambiar: {result}"
    return True


def test_y04_carrera_consulta_grado_informatica():
    """'que carrera estoy cursando' como ALU001 -> respuesta sobre Informatica."""
    graph = get_graph()
    r = _invoke(graph, "Que carrera estoy cursando?", user_id="ALU001")
    resp = r.get("final_response", "").lower()
    assert (
        "informatica" in resp or "inform" in resp
        or "grado" in resp or "carrera" in resp
    ), f"No menciona grado/carrera: {resp[:300]}"
    return True


def test_y05_titulacion_consulta_grado():
    """'mi titulacion' como ALU001 -> respuesta sobre su grado."""
    graph = get_graph()
    r = _invoke(graph, "Cual es mi titulacion?", user_id="ALU001")
    resp = r.get("final_response", "").lower()
    assert (
        "informatica" in resp or "grado" in resp
        or "titulacion" in resp or "carrera" in resp
        or "estudios" in resp
    ), f"No menciona titulacion: {resp[:300]}"
    return True


CASOS = [
    ("Y01", "carrera -> expande con grado", test_y01_carrera_expande_grado),
    ("Y02", "notas -> expande con calificacion", test_y02_notas_expande_calificacion),
    ("Y03", "hola no cambia", test_y03_hola_no_cambia),
    ("Y04", "carrera como ALU001 -> Informatica", test_y04_carrera_consulta_grado_informatica),
    ("Y05", "titulacion como ALU001 -> su grado", test_y05_titulacion_consulta_grado),
]


def run():
    lines = ["=== TEST SYNONYMS ==="]
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

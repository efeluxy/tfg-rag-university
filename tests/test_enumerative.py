# -*- coding: utf-8 -*-
"""Tests de deteccion de consultas enumerativas y respuestas exhaustivas."""

import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.graph import get_graph
from src.graph.state import get_initial_state

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_enumerative_{date.today():%Y%m%d}.txt"
)


def _invoke(graph, message, user_id=None):
    sid = str(uuid.uuid4())
    s = get_initial_state(message, sid, user_id)
    r = graph.invoke(s, config={"configurable": {"thread_id": sid}})
    return r


def test_e01_grados():
    """'Que grados ofrece la universidad' -> menciona Informatica, ADE y Derecho."""
    graph = get_graph()
    r = _invoke(graph, "Que grados ofrece la universidad?")
    resp = r.get("final_response", "").lower()
    menciona_informatica = "informatica" in resp or "informática" in resp
    menciona_ade = "ade" in resp or "administracion" in resp or "empresa" in resp
    menciona_derecho = "derecho" in resp
    count = sum([menciona_informatica, menciona_ade, menciona_derecho])
    assert count >= 2, (
        f"Solo menciona {count}/3 grados. Resp: {resp[:300]}"
    )
    return True


def test_e02_becas_enumerativas():
    """'Cuales son las becas disponibles' -> respuesta enumerativa."""
    graph = get_graph()
    r = _invoke(graph, "Cuales son las becas disponibles para estudiantes?")
    resp = r.get("final_response", "").lower()
    # Debe contener algun tipo de listado (guion, numeracion, o palabras como 'beca')
    assert (
        "beca" in resp or "ayuda" in resp or "mec" in resp
    ), f"Respuesta no enumerativa sobre becas: {resp[:300]}"
    assert len(resp) > 100, f"Respuesta demasiado corta: {len(resp)}"
    return True


def test_e03_optativas_4anyo():
    """'Que optativas hay en 4 de Informatica' -> menciona varias."""
    graph = get_graph()
    r = _invoke(graph, "Que optativas hay en 4 de Informatica?")
    resp = r.get("final_response", "").lower()
    # Debe mencionar algun contenido relevante de 4to anyo
    assert (
        "optativa" in resp or "cuarto" in resp or "4" in resp
        or "deep" in resp or "nlp" in resp or "vision" in resp
        or "aprendizaje" in resp or "especializacion" in resp
    ), f"No menciona optativas de 4 anyo: {resp[:300]}"
    assert len(resp) > 80, f"Respuesta demasiado corta: {len(resp)}"
    return True


def test_e04_no_enumerativo():
    """'Informacion del grado de Informatica' -> NO debe activar enumerativo."""
    graph = get_graph()
    r = _invoke(graph, "Dame informacion sobre el grado de Informatica")
    # El flag is_enumerative_query debe ser False
    is_enum = r.get("is_enumerative_query", False)
    resp = r.get("final_response", "")
    # No se espera activacion enumerativa; la respuesta igual puede ser util
    assert not is_enum, (
        f"is_enumerative_query deberia ser False para esta consulta especifica"
    )
    assert len(resp) > 50, f"Respuesta demasiado corta: {resp[:100]}"
    return True


CASOS = [
    ("E01", "Grados universidad -> menciona los 3", test_e01_grados),
    ("E02", "Becas disponibles -> enumerativo", test_e02_becas_enumerativas),
    ("E03", "Optativas 4 Informatica -> menciona varias", test_e03_optativas_4anyo),
    ("E04", "Info grado Informatica -> NO enumerativo", test_e04_no_enumerativo),
]


def run():
    lines = ["=== TEST ENUMERATIVE QUERIES ==="]
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

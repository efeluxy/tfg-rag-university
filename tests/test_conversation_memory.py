# -*- coding: utf-8 -*-
"""Tests de memoria conversacional."""

import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.graph import get_graph
from src.graph.state import get_initial_state

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_conversation_memory_{date.today():%Y%m%d}.txt"
)


def _invoke(graph, message, user_id=None, history=None):
    """Helper: invoca el grafo con historial opcional."""
    sid = str(uuid.uuid4())
    s = get_initial_state(message, sid, user_id, conversation_history=history or [])
    r = graph.invoke(s, config={"configurable": {"thread_id": sid}})
    return r.get("final_response", "")


def test_m01_followup_ia():
    """Turno 1: optativas IA. Turno 2: 'Si' -> debe hablar de optativas/IA."""
    graph = get_graph()
    resp1 = _invoke(graph, "Que optativas hay para especializarme en IA?", "ALU001")
    # Turno 2 con historial
    history = [
        {"role": "user", "content": "Que optativas hay para especializarme en IA?"},
        {"role": "assistant", "content": resp1},
    ]
    resp2 = _invoke(graph, "Si, cuentame mas", "ALU001", history=history)
    resp2_lower = resp2.lower()
    assert (
        "optativa" in resp2_lower or "ia" in resp2_lower
        or "inteligencia" in resp2_lower or "aprendizaje" in resp2_lower
    ), f"Turno 2 no relacionado con IA/optativas: {resp2[:300]}"
    return True


def test_m02_beca_plazos():
    """Turno 1: beca MEC. Turno 2: 'Y los plazos?' -> debe hablar de plazos de beca."""
    graph = get_graph()
    resp1 = _invoke(graph, "Informacion sobre la beca MEC")
    history = [
        {"role": "user", "content": "Informacion sobre la beca MEC"},
        {"role": "assistant", "content": resp1},
    ]
    resp2 = _invoke(graph, "Y los plazos?", history=history)
    resp2_lower = resp2.lower()
    assert (
        "plazo" in resp2_lower or "fecha" in resp2_lower
        or "beca" in resp2_lower or "mec" in resp2_lower
        or "solicitud" in resp2_lower
    ), f"Turno 2 no relacionado con plazos/beca: {resp2[:300]}"
    return True


def test_m03_sin_historial_si():
    """Sin historial, 'Si' -> debe pedir clarificacion o dar respuesta neutral."""
    graph = get_graph()
    resp = _invoke(graph, "Si")
    # No debe ser una respuesta con informacion especifica sin contexto
    # Debe pedir clarificacion o dar bienvenida
    assert len(resp) > 10, "Respuesta vacia"
    # Verificamos que no inventa contenido especifico sin haber preguntado nada
    resp_lower = resp.lower()
    # Una respuesta razonable contiene alguna de estas palabras
    assert (
        "clarif" in resp_lower or "?" in resp or "contexto" in resp_lower
        or "hola" in resp_lower or "ayud" in resp_lower or "encant" in resp_lower
        or "pregunta" in resp_lower or "podria" in resp_lower or "necesit" in resp_lower
    ), f"Respuesta inesperada sin historial: {resp[:300]}"
    return True


def test_m04_grados_tras_saludo():
    """Turno 1: saludo. Turno 2: grados -> respuesta sobre grados (no confunde)."""
    graph = get_graph()
    resp1 = _invoke(graph, "Hola, buenos dias")
    history = [
        {"role": "user", "content": "Hola, buenos dias"},
        {"role": "assistant", "content": resp1},
    ]
    resp2 = _invoke(graph, "Cuantos grados ofrece la universidad?", history=history)
    resp2_lower = resp2.lower()
    assert (
        "grado" in resp2_lower or "informatica" in resp2_lower
        or "ade" in resp2_lower or "derecho" in resp2_lower
    ), f"Turno 2 no menciona grados: {resp2[:300]}"
    return True


CASOS = [
    ("M01", "Follow-up: optativas IA -> 'Si' mantiene contexto", test_m01_followup_ia),
    ("M02", "Follow-up: beca MEC -> 'Y los plazos?' coherente", test_m02_beca_plazos),
    ("M03", "Sin historial: 'Si' pide clarificacion", test_m03_sin_historial_si),
    ("M04", "Saludo + pregunta grados: no se confunde", test_m04_grados_tras_saludo),
]


def run():
    lines = ["=== TEST CONVERSATION MEMORY ==="]
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

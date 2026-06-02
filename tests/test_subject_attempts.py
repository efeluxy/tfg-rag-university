# -*- coding: utf-8 -*-
"""Tests de la nueva tabla y consulta de convocatorias."""

import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.sqlite_query import get_subject_attempts
from src.graph.graph import get_graph
from src.graph.state import get_initial_state

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_subject_attempts_{date.today():%Y%m%d}.txt"
)


def test_db_direct():
    """ALU015 / INF201 debe existir con al menos 1 intento registrado."""
    r = get_subject_attempts("ALU015", "INF201")
    assert len(r) == 1, f"ALU015/INF201 no encontrado (filas={len(r)})"
    assert r[0]["attempts_used"] >= 1, f"attempts_used={r[0]['attempts_used']}"
    assert r[0]["status"] in ("failed_last", "passed", "pending"), f"status={r[0]['status']}"
    return True


def test_db_all_subjects():
    """ALU015 debe tener varias asignaturas."""
    r = get_subject_attempts("ALU015")
    assert len(r) >= 5, f"ALU015 tiene solo {len(r)} asignaturas"
    return True


def test_graph_sergio_inf201():
    """Pregunta directa a Sergio sobre INF201 (con rol student)."""
    import re as _re
    graph = get_graph()
    sid = str(uuid.uuid4())
    s = get_initial_state(
        "Cuantas convocatorias me quedan para INF201?", sid, "ALU015",
        role="student", authenticated_user_id="ALU015",
    )
    r = graph.invoke(s, config={"configurable": {"thread_id": sid}})
    resp = r.get("final_response", "")
    assert "INF201" in resp or "Estructuras" in resp or "estructuras" in resp.lower(), \
        f"No menciona INF201: {resp[:200]}"
    assert _re.search(r"\d", resp), f"No menciona numero de convocatorias: {resp[:200]}"
    return True


def test_graph_carlos_general():
    """Pregunta general a Carlos sobre sus convocatorias (con rol student)."""
    graph = get_graph()
    sid = str(uuid.uuid4())
    s = get_initial_state(
        "Cuantas convocatorias he gastado en total?", sid, "ALU001",
        role="student", authenticated_user_id="ALU001",
    )
    r = graph.invoke(s, config={"configurable": {"thread_id": sid}})
    resp = r.get("final_response", "")
    assert len(resp) > 100, f"Respuesta demasiado corta: {len(resp)} chars"
    return True


def test_invitado_sin_convocatorias():
    """Un invitado pregunta sobre INF201 — no debe revelar datos personales."""
    graph = get_graph()
    sid = str(uuid.uuid4())
    s = get_initial_state(
        "Cuantas convocatorias tengo para INF201?", sid, None
    )
    r = graph.invoke(s, config={"configurable": {"thread_id": sid}})
    resp = r.get("final_response", "")
    assert "ALU0" not in resp, f"Filtra IDs de alumnos: {resp[:200]}"
    return True


CASOS = [
    ("S01", "BD directa: ALU015/INF201", test_db_direct),
    ("S02", "BD directa: todas asignaturas ALU015", test_db_all_subjects),
    ("S03", "Grafo: Sergio pregunta INF201", test_graph_sergio_inf201),
    ("S04", "Grafo: Carlos pregunta general", test_graph_carlos_general),
    ("S05", "Grafo: Invitado no ve datos personales", test_invitado_sin_convocatorias),
]


def run():
    lines = ["=== TEST SUBJECT ATTEMPTS ==="]
    resultados = []
    for cid, desc, fn in CASOS:
        try:
            ok = fn()
        except AssertionError as e:
            lines.append(f"  [{cid}] {desc:<45} FAIL: {e}")
            resultados.append(False)
            continue
        except Exception as e:
            lines.append(f"  [{cid}] {desc:<45} ERROR: {e}")
            resultados.append(False)
            continue
        estado = "PASS" if ok else "FAIL"
        lines.append(f"  [{cid}] {desc:<45} {estado}")
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

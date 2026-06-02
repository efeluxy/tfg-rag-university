"""Test de los bugs de flujo reportados por Felix."""

import re
import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph.graph import get_graph
from src.graph.state import get_initial_state

LOG_PATH = (Path(__file__).parent.parent / "logs"
            / f"test_flow_debug_{date.today():%Y%m%d}.txt")


def _invoke(graph, msg, role, auth_uid, selected_uid):
    sid = str(uuid.uuid4())
    s = get_initial_state(
        user_message=msg, session_id=sid, user_id=selected_uid,
        role=role, authenticated_user_id=auth_uid,
    )
    return graph.invoke(s, config={"configurable": {"thread_id": sid}})


def t_admin_alu017():
    g = get_graph()
    r = _invoke(g, "Quien es ALU017?", "admin", None, None)
    assert r.get("intent") != "OUT_OF_SCOPE", "Router clasifico mal"
    assert not r.get("access_violation_attempted"), "Admin bloqueado!"
    resp = (r.get("final_response") or "").lower()
    assert "no tengo" not in resp or "alu017" in resp, "No usa datos"
    return True


def t_student_own_grade():
    g = get_graph()
    r = _invoke(g, "Que nota saque en INF101?",
                "student", "ALU015", "ALU015")
    grades = r.get("student_grades") or []
    assert len(grades) >= 1, f"No cargo grades (cargo {len(grades)})"
    resp = r.get("final_response") or ""
    assert re.search(r"\b\d+(?:[.,]\d+)?\b", resp), "Sin numero en respuesta"
    return True


def t_student_own_career():
    g = get_graph()
    r = _invoke(g, "Que carrera estoy cursando?",
                "student", "ALU015", "ALU015")
    rec = r.get("student_record")
    assert rec is not None, "No cargo expediente"
    resp = (r.get("final_response") or "").lower()
    assert "informatica" in resp or "inform" in resp, \
        "No menciona informatica"
    return True


def t_enumerative_plan():
    g = get_graph()
    r = _invoke(g, "Plan de estudios completo de informatica",
                "guest", None, None)
    assert r.get("is_enumerative_query"), \
        "No detecto enumerativo"
    resp = r.get("final_response") or ""
    mentions = sum(1 for c in ["primer", "segundo", "tercero", "cuarto"]
                   if c in resp.lower())
    assert mentions >= 3, f"Solo menciona {mentions} cursos"
    return True


def t_student_blocked_other():
    g = get_graph()
    r = _invoke(g, "Quien es ALU017?", "student", "ALU001", "ALU001")
    assert r.get("access_violation_attempted"), \
        "No detecto violacion"
    resp = (r.get("final_response") or "").lower()
    assert ("no tengo acceso" in resp or "no puedo" in resp
            or "proteccion de datos" in resp or "privacidad" in resp), \
        "Respuesta no es de rechazo"
    return True


def t_admin_full_record():
    g = get_graph()
    r = _invoke(g, "Dame el expediente completo de ALU030",
                "admin", None, "ALU030")
    assert not r.get("access_violation_attempted"), "Admin bloqueado"
    attempts = r.get("subject_attempts") or []
    assert len(attempts) >= 3, f"Solo {len(attempts)} attempts"
    return True


CASOS = [
    ("F1", "Admin pregunta por ALU017", t_admin_alu017),
    ("F2", "Sergio pregunta su nota INF101", t_student_own_grade),
    ("F3", "Sergio pregunta su carrera", t_student_own_career),
    ("F4", "Plan estudios completo (enum)", t_enumerative_plan),
    ("F5", "Alumno bloqueado para ver otro", t_student_blocked_other),
    ("F6", "Admin pide expediente ALU030", t_admin_full_record),
]


def run():
    lines = ["=== TEST FLOW DEBUG ==="]
    ok_count = 0
    for cid, desc, fn in CASOS:
        try:
            fn()
            lines.append(f"  [{cid}] {desc:<45} PASS")
            ok_count += 1
        except AssertionError as e:
            lines.append(f"  [{cid}] {desc:<45} FAIL: {e}")
        except Exception as e:
            lines.append(f"  [{cid}] {desc:<45} ERROR: {e}")
    lines.append(f"TOTAL: {ok_count}/{len(CASOS)} PASS")
    out = "\n".join(lines)
    print(out)
    LOG_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.write_text(out + "\n", encoding="utf-8")
    return ok_count


if __name__ == "__main__":
    run()

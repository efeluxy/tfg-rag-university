"""Tests de consultas multiples de alumnos (solo admin)."""

import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph.graph import get_graph
from src.graph.state import get_initial_state
from src.agents.student_data import _extract_mentioned_student_ids

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_multi_student_{date.today():%Y%m%d}.txt"
)


def _invoke(graph, msg, role, auth_uid=None, selected=None):
    sid = str(uuid.uuid4())
    s = get_initial_state(
        user_message=msg, session_id=sid, user_id=selected,
        role=role, authenticated_user_id=auth_uid,
    )
    return graph.invoke(s, config={"configurable": {"thread_id": sid}})


# ── Tests unitarios de la funcion extractora ──────────────────────────────────

def t_extract_range():
    ids, trunc = _extract_mentioned_student_ids("del 1 al 5")
    assert ids == ["ALU001", "ALU002", "ALU003", "ALU004", "ALU005"], \
        f"Esperaba 5 IDs, obtuve {ids}"
    assert not trunc
    return True


def t_extract_explicit_multi():
    ids, _ = _extract_mentioned_student_ids("ALU001, ALU017 y ALU030")
    assert set(ids) == {"ALU001", "ALU017", "ALU030"}, f"IDs: {ids}"
    return True


def t_extract_truncation():
    ids, trunc = _extract_mentioned_student_ids("del 1 al 100")
    assert trunc is True, "Debia truncar"
    assert len(ids) == 20, f"Esperaba 20, obtuve {len(ids)}"
    return True


# ── Tests del grafo end-to-end ────────────────────────────────────────────────

def t_admin_range():
    g = get_graph()
    r = _invoke(g, "Dame info del 1 al 5", "admin")
    multi = r.get("multi_student_records") or []
    assert len(multi) == 5, f"Esperaba 5, obtuve {len(multi)}"
    resp = (r.get("final_response") or "").upper()
    mentions = sum(1 for n in range(1, 6) if f"ALU00{n}" in resp)
    assert mentions >= 3, f"Solo menciona {mentions} IDs en la respuesta"
    return True


def t_student_blocked_multi():
    g = get_graph()
    r = _invoke(g, "Info del 1 al 5", "student",
                auth_uid="ALU001", selected="ALU001")
    assert r.get("access_violation_attempted"), "No bloqueo al student!"
    return True


def t_guest_blocked_multi():
    g = get_graph()
    r = _invoke(g, "Info de ALU001 y ALU017", "guest")
    assert r.get("access_violation_attempted"), "No bloqueo al guest!"
    return True


CASOS = [
    ("M1", "Extractor: rango '1 al 5'", t_extract_range),
    ("M2", "Extractor: IDs explicitos", t_extract_explicit_multi),
    ("M3", "Extractor: truncacion en rango grande", t_extract_truncation),
    ("M4", "Admin: rango de 5 alumnos", t_admin_range),
    ("M5", "Student bloqueado en multi", t_student_blocked_multi),
    ("M6", "Guest bloqueado en multi", t_guest_blocked_multi),
]


def run():
    lines = ["=== TEST MULTI STUDENT QUERY ==="]
    ok = 0
    for cid, desc, fn in CASOS:
        try:
            fn()
            lines.append(f"  [{cid}] {desc:<45} PASS")
            ok += 1
        except AssertionError as e:
            lines.append(f"  [{cid}] {desc:<45} FAIL: {e}")
        except Exception as e:
            lines.append(f"  [{cid}] {desc:<45} ERROR: {e}")
    lines.append(f"TOTAL: {ok}/{len(CASOS)} PASS")
    out = "\n".join(lines)
    print(out)
    LOG_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.write_text(out + "\n", encoding="utf-8")
    return ok


if __name__ == "__main__":
    run()

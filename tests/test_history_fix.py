"""Tests del fix de contaminacion de historial e IDs cortos."""

import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph.graph import get_graph
from src.graph.state import get_initial_state
from src.agents.student_data import (
    _extract_mentioned_student_ids,
    _detect_short_id_list,
)
from src.utils.conversation import (
    get_recent_history,
    is_no_data_response,
)

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_history_fix_{date.today():%Y%m%d}.txt"
)


# ── Tests unitarios ───────────────────────────────────────────────────────────

def t_short_id_list():
    ids = _detect_short_id_list("info del 001, el 017 y el 030")
    assert ids == ["ALU001", "ALU017", "ALU030"], f"got {ids}"
    return True


def t_short_id_no_false_positive():
    ids = _detect_short_id_list("Carlos tiene 180 creditos y 9.1 media")
    assert ids == [], f"falso positivo: {ids}"
    return True


def t_is_no_data():
    assert is_no_data_response("No dispongo de informacion sobre X")
    assert is_no_data_response("Lo siento, no tengo acceso a esos datos")
    assert not is_no_data_response("Es Manuel Martinez, segundo curso")
    return True


def t_history_filters_no_data():
    msgs = [
        {"role": "user", "content": "quien es alu017"},
        {"role": "assistant", "content": "Es Manuel Martinez Cano"},
        {"role": "user", "content": "y alu999?"},
        {"role": "assistant", "content": "No dispongo de info sobre ALU999"},
        {"role": "user", "content": "actual"},
    ]
    h = get_recent_history(msgs, max_turns=6)
    assert len(h) == 2, f"esperaba 2, got {len(h)}"
    assert "alu017" in h[0]["content"].lower()
    return True


# ── Test end-to-end ───────────────────────────────────────────────────────────

def t_e2e_no_contamination():
    """Reproduce el bug exacto: lista de IDs cortos debe detectar 3 alumnos."""
    g = get_graph()
    sid = str(uuid.uuid4())
    s = get_initial_state(
        user_message="info del 001, el 017 y el 030",
        session_id=sid, user_id=None,
        role="admin", authenticated_user_id=None,
    )
    r1 = g.invoke(s, config={"configurable": {"thread_id": sid}})
    multi = r1.get("multi_student_records") or []
    assert len(multi) >= 2, f"Solo cargo {len(multi)} alumnos"
    return True


CASOS = [
    ("H1", "Extractor: IDs cortos en lista", t_short_id_list),
    ("H2", "Extractor: no falsos positivos", t_short_id_no_false_positive),
    ("H3", "is_no_data_response correcto", t_is_no_data),
    ("H4", "Historial filtra respuestas vacias", t_history_filters_no_data),
    ("H5", "E2E: lista de IDs cortos admin", t_e2e_no_contamination),
]


def run():
    lines = ["=== TEST HISTORY FIX ==="]
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

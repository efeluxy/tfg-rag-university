"""Block 8: Smoke test for the LangGraph pipeline (3 cases)."""
import sys
import uuid
import logging
sys.path.insert(0, ".")

logging.basicConfig(level=logging.ERROR)

from src.graph.graph import get_graph
from src.graph.state import get_initial_state

graph = get_graph()
casos = [
    ("Hola", None, "GREETING"),
    ("Como solicito la beca MEC?", None, "SCHOLARSHIPS"),
    ("Cual es la receta de la paella?", None, "OUT_OF_SCOPE"),
]
ok = 0
for msg, uid, intent_esp in casos:
    sid = str(uuid.uuid4())
    s = get_initial_state(msg, sid, uid)
    try:
        r = graph.invoke(s, config={"configurable": {"thread_id": sid}})
        intent = r.get("intent")
        response = r.get("final_response", "") or ""
        ok_caso = (intent == intent_esp) and len(response) > 10
        status = "PASS" if ok_caso else "FAIL"
        print(f"[{status}] {msg[:40]} -> intent={intent} (expected={intent_esp}), response_len={len(response)}")
        if ok_caso:
            ok += 1
    except Exception as e:
        print(f"[FAIL] {msg[:40]} -> ERROR: {e}")
print(f"TOTAL: {ok}/3")
sys.exit(0 if ok == 3 else 1)

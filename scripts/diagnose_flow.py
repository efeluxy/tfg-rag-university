"""Diagnostico del flujo: reproduce los 4 sintomas reportados."""

import logging
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(name)s]: %(message)s',
)

from src.graph.graph import get_graph
from src.graph.state import get_initial_state

CASOS = [
    # (id, descripcion, role, auth_uid, selected_uid, mensaje, esperado_clave)
    ("D1", "Admin pregunta por ALU017",
     "admin", None, None, "Quien es ALU017?",
     {"intent_no_oos": True, "expects_data": True}),
    ("D2", "Student=ALU015 pregunta su nota en INF101",
     "student", "ALU015", "ALU015", "Que nota saque en INF101?",
     {"intent_no_oos": True, "has_grades": True}),
    ("D3", "Student=ALU015 pregunta carrera",
     "student", "ALU015", "ALU015", "Que carrera estoy cursando?",
     {"intent_no_oos": True, "has_record": True}),
    ("D4", "Plan de estudios completo (sin keywords enumerativas)",
     "guest", None, None,
     "Plan de estudios completo de informatica",
     {"is_enumerative": True}),
    ("D5", "Student=ALU001 pide datos de ALU017",
     "student", "ALU001", "ALU001", "Quien es ALU017?",
     {"violation": True}),
    ("D6", "Admin pide expediente completo de ALU030",
     "admin", None, "ALU030", "Dame el expediente completo de ALU030",
     {"has_record": True, "has_grades": True}),
]


def run():
    graph = get_graph()
    for cid, desc, role, auth_uid, selected_uid, msg, esperado in CASOS:
        print(f"\n{'='*70}\n[{cid}] {desc}\n{'='*70}")
        sid = str(uuid.uuid4())
        s = get_initial_state(
            user_message=msg,
            session_id=sid,
            user_id=selected_uid,
            role=role,
            authenticated_user_id=auth_uid,
        )
        try:
            r = graph.invoke(s, config={"configurable": {"thread_id": sid}})
        except Exception as e:
            print(f"EXCEPCION: {e}")
            continue

        # Mostrar resumen
        print(f"  intent: {r.get('intent')}")
        print(f"  is_enumerative: {r.get('is_enumerative_query')}")
        print(f"  requires_student_data: {r.get('requires_student_data')}")
        print(f"  guardrail_triggered: {r.get('guardrail_triggered')}")
        print(f"  guardrail_reason: {r.get('guardrail_reason')}")
        print(f"  access_violation: {r.get('access_violation_attempted')}")
        print(f"  has_record: {bool(r.get('student_record'))}")
        print(f"  num_grades: {len(r.get('student_grades') or [])}")
        print(f"  num_attempts: {len(r.get('subject_attempts') or [])}")
        print(f"  response (primeros 300 chars):")
        resp = r.get("final_response", "") or ""
        print(f"    {resp[:300]}")


if __name__ == "__main__":
    run()

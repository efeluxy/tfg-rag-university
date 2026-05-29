from src.graph.state import get_initial_state
s = get_initial_state("Hola", "test-session-id", None)
expected_keys = [
    "user_message", "user_id", "session_id", "intent", "key_points",
    "requires_student_data", "router_reasoning", "guardrail_triggered",
    "guardrail_reason", "retrieved_docs", "search_queries", "student_record",
    "final_response", "sources", "confidence", "message_history",
]
missing = [k for k in expected_keys if k not in s]
if missing:
    print("MISSING KEYS:", missing)
else:
    print("State OK: all", len(expected_keys), "keys present")
    print("  user_message:", type(s["user_message"]).__name__)
    print("  key_points:", type(s["key_points"]).__name__, "=", s["key_points"])
    print("  retrieved_docs:", type(s["retrieved_docs"]).__name__, "=", s["retrieved_docs"])
    print("  message_history:", type(s["message_history"]).__name__, "=", s["message_history"])
    print("  guardrail_triggered:", s["guardrail_triggered"])
    print("  requires_student_data:", s["requires_student_data"])

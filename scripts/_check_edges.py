"""Block 5.3 - Verify edge routing logic."""
import sys
sys.path.insert(0, ".")

from src.graph.edges import route_after_guardrail, route_after_retriever, route_after_router
from src.graph.state import get_initial_state

ok = 0

# Test 1: guardrail_triggered=True -> generator
s1 = get_initial_state("test", "sid", None)
s1["guardrail_triggered"] = True
r1 = route_after_guardrail(s1)
assert r1 == "generator", f"Expected 'generator', got '{r1}'"
print("PASS: guardrail_triggered=True -> generator")
ok += 1

# Test 2: guardrail_triggered=False -> retriever
s2 = get_initial_state("test", "sid", None)
s2["guardrail_triggered"] = False
r2 = route_after_guardrail(s2)
assert r2 == "retriever", f"Expected 'retriever', got '{r2}'"
print("PASS: guardrail_triggered=False -> retriever")
ok += 1

# Test 3: requires_student_data=True with user_id -> student_data
s3 = get_initial_state("test", "sid", "student123")
s3["requires_student_data"] = True
r3 = route_after_retriever(s3)
assert r3 == "student_data", f"Expected 'student_data', got '{r3}'"
print("PASS: requires_student_data=True + user_id -> student_data")
ok += 1

# Test 4: retrieved_docs=[] (empty) -> generator (not crash)
s4 = get_initial_state("test", "sid", None)
s4["retrieved_docs"] = []
s4["requires_student_data"] = False
r4 = route_after_retriever(s4)
assert r4 == "generator", f"Expected 'generator', got '{r4}'"
print("PASS: retrieved_docs=[] -> generator (no crash)")
ok += 1

# Test 5: requires_student_data=True but user_id=None -> generator
s5 = get_initial_state("test", "sid", None)
s5["requires_student_data"] = True
r5 = route_after_retriever(s5)
assert r5 == "generator", f"Expected 'generator', got '{r5}'"
print("PASS: requires_student_data=True + user_id=None -> generator")
ok += 1

# Test 6: route_after_router always returns guardrail
s6 = get_initial_state("test", "sid", None)
r6 = route_after_router(s6)
assert r6 == "guardrail", f"Expected 'guardrail', got '{r6}'"
print("PASS: route_after_router -> guardrail")
ok += 1

print(f"TOTAL: {ok}/6 edge tests passed")

"""Debug R02: trace why violation not detected."""
import sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Patch logger to see access violation messages
import logging
logging.basicConfig(level=logging.INFO)

from src.graph.graph import get_graph
from src.graph.state import get_initial_state

graph = get_graph()
sid = str(uuid.uuid4())
state = get_initial_state(
    "Dame informacion del alumno ALU017",
    sid,
    user_id="ALU017",
    role="student",
    authenticated_user_id="ALU001",
)

print("Initial state keys:", list(state.keys()))
print("role:", state.get("role"))
print("authenticated_user_id:", state.get("authenticated_user_id"))
print("user_id:", state.get("user_id"))

r = graph.invoke(state, config={"configurable": {"thread_id": sid}})
print("\nFinal state keys:", [k for k in r.keys()])
print("access_violation_attempted:", r.get("access_violation_attempted"))
print("final_response[:150]:", r.get("final_response", "")[:150])

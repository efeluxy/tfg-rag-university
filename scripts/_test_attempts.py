"""Test aislado de get_subject_attempts."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.tools.sqlite_query import get_subject_attempts
r = get_subject_attempts("ALU015", "INF201")
print(r)
assert len(r) == 1, f"Expected 1 row, got {len(r)}"
assert r[0]["attempts_used"] == 2, f"Expected 2, got {r[0]['attempts_used']}"
assert r[0]["status"] == "failed_last", f"Expected failed_last, got {r[0]['status']}"
print("OK - get_subject_attempts funciona correctamente")

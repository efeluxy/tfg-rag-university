"""Test aislado de _check_access_permission."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly to avoid runtime import error on get_student_grades
from src.agents.student_data import _check_access_permission

print("admin->other:", _check_access_permission("admin", None, "ALU017"))
print("student->own:", _check_access_permission("student", "ALU001", "ALU001"))
print("student->other:", _check_access_permission("student", "ALU001", "ALU017"))
print("guest->any:", _check_access_permission("guest", None, "ALU017"))

assert _check_access_permission("admin", None, "ALU017") == (True, "admin_access")
assert _check_access_permission("student", "ALU001", "ALU001") == (True, "own_record")
assert _check_access_permission("student", "ALU001", "ALU017") == (False, "student_requesting_other")
assert _check_access_permission("guest", None, "ALU017") == (False, "guest_requesting_student")
print("OK - todos los permisos correctos")

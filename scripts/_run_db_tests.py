"""Ejecuta solo los tests que no requieren Azure."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.sqlite_query import get_subject_attempts
from src.utils.conversation import get_recent_history, format_history_for_llm

# Test 1: BD directa ALU015/INF201
r = get_subject_attempts("ALU015", "INF201")
assert len(r) == 1 and r[0]["attempts_used"] == 2 and r[0]["status"] == "failed_last"
print("S01 PASS: BD directa ALU015/INF201 correcta")

# Test 2: BD todas asignaturas ALU015
r = get_subject_attempts("ALU015")
assert len(r) >= 5
print(f"S02 PASS: ALU015 tiene {len(r)} asignaturas")

# Test 3: get_recent_history vacio
h = get_recent_history([])
assert h == []
print("Conv01 PASS: historial vacio devuelve []")

# Test 4: get_recent_history con mensajes
msgs = [
    {"role": "user", "content": "hola"},
    {"role": "assistant", "content": "bienvenido"},
    {"role": "user", "content": "mensaje actual"},
]
h = get_recent_history(msgs, max_turns=6)
# Excluye el ultimo (mensaje actual)
assert len(h) == 2
print("Conv02 PASS: get_recent_history excluye el ultimo mensaje")

# Test 5: format_history_for_llm
formatted = format_history_for_llm([{"role": "user", "content": "hola"}, {"role": "assistant", "content": "adios"}])
assert "HISTORIAL" in formatted and "Usuario: hola" in formatted
print("Conv03 PASS: format_history_for_llm correcto")

# Test 6: ALU001 Carlos intentos
r = get_subject_attempts("ALU001", "INF101")
assert r[0]["attempts_used"] == 1 and r[0]["status"] == "passed"
print("S_ALU001 PASS: Carlos INF101 = 1 intento, passed")

print("\nTodos los tests locales: PASS")

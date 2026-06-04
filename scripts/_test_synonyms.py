"""Test aislado de expand_query_with_synonyms."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.synonyms import expand_query_with_synonyms

r1 = expand_query_with_synonyms("que carrera estoy cursando")
r2 = expand_query_with_synonyms("cuales son mis notas")
r3 = expand_query_with_synonyms("hola")

print("query 1:", r1)
print("query 2:", r2)
print("query 3:", r3)

assert "grado" in r1, f"'grado' no encontrado en: {r1}"
assert "calificacion" in r2 or "calificación" in r2, f"'calificacion' no en: {r2}"
assert r3 == "hola", f"hola deberia no cambiar: {r3}"
print("OK - todos los tests de sinonimos correctos")

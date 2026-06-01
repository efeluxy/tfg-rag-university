# -*- coding: utf-8 -*-
"""Tests del sistema de autenticacion."""

import os
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.auth import (
    authenticate_admin,
    authenticate_student,
    get_admin_password,
    get_student_password,
)

LOG_PATH = (
    Path(__file__).parent.parent / "logs"
    / f"test_auth_{date.today():%Y%m%d}.txt"
)

CASOS = [
    # (id, descripcion, funcion_y_args, esperado)
    (
        "A01",
        "Admin password correcta",
        lambda: authenticate_admin(os.getenv("ADMIN_PASSWORD") or "admin2026"),
        True,
    ),
    (
        "A02",
        "Admin password incorrecta",
        lambda: authenticate_admin("password_mala_xxx"),
        False,
    ),
    (
        "A03",
        "Admin password vacia",
        lambda: authenticate_admin(""),
        False,
    ),
    (
        "S01",
        "Alumno valido + password correcta",
        lambda: authenticate_student(
            "ALU001", os.getenv("STUDENT_PASSWORD") or "alumno2026"
        ),
        True,
    ),
    (
        "S02",
        "Alumno valido + password incorrecta",
        lambda: authenticate_student("ALU001", "mala"),
        False,
    ),
    (
        "S03",
        "Alumno con user_id vacio",
        lambda: authenticate_student(
            "", os.getenv("STUDENT_PASSWORD") or "alumno2026"
        ),
        False,
    ),
    (
        "S04",
        "Alumno con password vacia",
        lambda: authenticate_student("ALU001", ""),
        False,
    ),
    (
        "E01",
        "Variables env existen",
        lambda: bool(get_student_password()) and bool(get_admin_password()),
        True,
    ),
]


def run_tests():
    lines = ["=== TEST AUTH SYSTEM ==="]
    lines.append(f"Total casos: {len(CASOS)}")
    lines.append("")
    resultados = []

    for caso_id, desc, fn, esperado in CASOS:
        try:
            real = fn()
            test_pass = real == esperado
        except Exception as exc:
            real = f"EXCEPTION: {exc}"
            test_pass = False
        resultados.append(test_pass)
        estado = "PASS" if test_pass else "FAIL"
        lines.append(f"  [{caso_id}] {desc:<45} {estado}")
        if not test_pass:
            lines.append(f"       esperado={esperado}, real={real}")

    total = sum(resultados)
    lines.append("")
    lines.append(f"TOTAL: {total}/{len(CASOS)} PASS")
    lines.append(
        f"RESULTADO: {'SUPERADO' if total == len(CASOS) else 'NO SUPERADO'}"
    )

    output = "\n".join(lines)
    print(output)
    LOG_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.write_text(output + "\n", encoding="utf-8")
    return total


if __name__ == "__main__":
    run_tests()

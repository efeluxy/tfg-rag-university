"""Script de verificación de la Fase 1 del TFG Universidad RAG.

Comprueba que todos los archivos, datos y módulos de la Fase 1 están
correctamente creados y son funcionales.
"""

import importlib
import io
import os
import sqlite3
import sys

# Forzar UTF-8 en stdout para entornos Windows con cp1252
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def check(label: str, result: bool, detail: str = "") -> bool:
    """Imprime el resultado de un check y devuelve el bool."""
    mark = "✓" if result else "✗"
    line = f"  {mark} {label}"
    if not result and detail:
        line += f"\n      → {detail}"
    print(line)
    return result


def count_words(path: str) -> int:
    """Cuenta palabras aproximadas de un archivo de texto."""
    try:
        with open(path, encoding="utf-8") as f:
            return len(f.read().split())
    except OSError:
        return 0


def main() -> None:
    passes = 0
    total = 0

    def run(label: str, result: bool, detail: str = "") -> None:
        nonlocal passes, total
        total += 1
        if check(label, result, detail):
            passes += 1

    print()
    print("══════════════════════════════════════════")
    print("  VERIFICACIÓN FASE 1 — TFG Universidad  ")
    print("══════════════════════════════════════════")

    # ── BLOQUE 1.1 — Configuración ────────────────────────────────────────────
    print()
    print("[BLOQUE 1.1 — Configuración]")

    run(".gitignore existe", os.path.isfile(os.path.join(ROOT, ".gitignore")))

    env_example = os.path.join(ROOT, ".env.example")
    if os.path.isfile(env_example):
        with open(env_example, encoding="utf-8") as f:
            env_lines = [l for l in f if "=" in l and not l.strip().startswith("#")]
        run(".env.example existe y tiene 12+ variables",
            len(env_lines) >= 12,
            f"Variables encontradas: {len(env_lines)}")
    else:
        run(".env.example existe y tiene 12+ variables", False, "Archivo no encontrado")

    req_path = os.path.join(ROOT, "requirements.txt")
    if os.path.isfile(req_path):
        with open(req_path, encoding="utf-8") as f:
            deps = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        run("requirements.txt existe con 12+ dependencias",
            len(deps) >= 12,
            f"Dependencias encontradas: {len(deps)}")
    else:
        run("requirements.txt existe con 12+ dependencias", False, "Archivo no encontrado")

    readme_path = os.path.join(ROOT, "README.md")
    readme_words = count_words(readme_path) if os.path.isfile(readme_path) else 0
    run("README.md existe (>500 palabras)",
        readme_words > 500,
        f"Palabras encontradas: {readme_words}")

    run("CLAUDE.md existe", os.path.isfile(os.path.join(ROOT, "CLAUDE.md")))

    # Importar settings.py sin credenciales
    try:
        import src.config.settings as settings  # noqa: F401
        run("src/config/settings.py importable sin credenciales", True)
    except Exception as exc:
        run("src/config/settings.py importable sin credenciales", False, str(exc))

    # Importar azure_config.py sin credenciales (solo el módulo, no llamar funciones)
    try:
        import src.config.azure_config as azure_cfg  # noqa: F401
        run("src/config/azure_config.py importable sin credenciales", True)
    except Exception as exc:
        run("src/config/azure_config.py importable sin credenciales", False, str(exc))

    # ── BLOQUE 1.2 — Corpus ───────────────────────────────────────────────────
    print()
    print("[BLOQUE 1.2 — Corpus]")

    corpus_root = os.path.join(ROOT, "data", "corpus")

    norm_files = ["reglamento_academico.md", "normativa_permanencia.md", "politica_evaluacion.md"]
    norm_present = sum(1 for f in norm_files if os.path.isfile(os.path.join(corpus_root, "normativas", f)))
    run(f"Normativas: {norm_present}/3 archivos presentes", norm_present == 3)

    plan_files = ["grado_informatica.md", "grado_ade.md", "grado_derecho.md"]
    plan_present = sum(1 for f in plan_files if os.path.isfile(os.path.join(corpus_root, "planes_estudio", f)))
    run(f"Planes de estudio: {plan_present}/3 archivos presentes", plan_present == 3)

    guide_files = [
        "guia_programacion_i.md", "guia_estructuras_datos.md", "guia_bases_datos.md",
        "guia_redes.md", "guia_ia_introduccion.md", "guia_matematicas_i.md",
        "guia_calculo.md", "guia_estadistica.md",
    ]
    guide_present = sum(1 for f in guide_files if os.path.isfile(os.path.join(corpus_root, "guias_docentes", f)))
    run(f"Guías docentes: {guide_present}/8 archivos presentes", guide_present == 8)

    faq_files = ["faq_matriculacion.md", "faq_becas.md", "faq_admision.md", "faq_examenes.md"]
    faq_present = sum(1 for f in faq_files if os.path.isfile(os.path.join(corpus_root, "faqs", f)))
    run(f"FAQs: {faq_present}/4 archivos presentes", faq_present == 4)

    proc_files = [
        "guia_orientacion_academica.md", "protocolo_apoyo_riesgo.md",
        "servicios_universidad.md", "calendario_academico.md",
    ]
    proc_present = sum(1 for f in proc_files if os.path.isfile(os.path.join(corpus_root, "procedimientos", f)))
    run(f"Procedimientos: {proc_present}/4 archivos presentes", proc_present == 4)

    # Contar palabras totales del corpus
    total_words = 0
    for dirpath, _, filenames in os.walk(corpus_root):
        for fname in filenames:
            if fname.endswith(".md"):
                total_words += count_words(os.path.join(dirpath, fname))
    run(f"Total palabras corpus: {total_words} (mínimo requerido: 15000)",
        total_words >= 15000,
        f"Palabras contadas: {total_words}")

    # ── BLOQUE 1.3 — Base de datos ────────────────────────────────────────────
    print()
    print("[BLOQUE 1.3 — Base de datos]")

    db_path_env = os.getenv("SQLITE_DB_PATH", "data/database/students.db")
    if not os.path.isabs(db_path_env):
        db_path = os.path.join(ROOT, db_path_env)
    else:
        db_path = db_path_env

    run("data/database/students.db existe", os.path.isfile(db_path))

    if os.path.isfile(db_path):
        try:
            conn = sqlite3.connect(db_path)
            n_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            n_records = conn.execute("SELECT COUNT(*) FROM subject_records").fetchone()[0]
            n_schols = conn.execute("SELECT COUNT(*) FROM scholarships").fetchone()[0]

            run(f"Tabla students: {n_students} filas", n_students == 50,
                f"Encontradas: {n_students}")
            run(f"Tabla subject_records: {n_records} filas", n_records > 0,
                f"Encontradas: {n_records}")
            run(f"Tabla scholarships: {n_schols} filas", n_schols >= 0,
                f"Encontradas: {n_schols}")

            alu001 = conn.execute(
                "SELECT status FROM students WHERE id = 'ALU001'"
            ).fetchone()
            run("ALU001 existe con status='excellent'",
                alu001 is not None and alu001[0] == "excellent",
                f"status encontrado: {alu001[0] if alu001 else 'NO EXISTE'}")

            alu015 = conn.execute(
                "SELECT status FROM students WHERE id = 'ALU015'"
            ).fetchone()
            run("ALU015 existe con status='at_risk'",
                alu015 is not None and alu015[0] == "at_risk",
                f"status encontrado: {alu015[0] if alu015 else 'NO EXISTE'}")

            conn.close()
        except sqlite3.Error as exc:
            run("Tabla students: 50 filas", False, str(exc))
            run("Tabla subject_records: N filas", False, str(exc))
            run("Tabla scholarships: N filas", False, str(exc))
            run("ALU001 existe con status='excellent'", False, str(exc))
            run("ALU015 existe con status='at_risk'", False, str(exc))
    else:
        for label in [
            "Tabla students: 50 filas",
            "Tabla subject_records: N filas",
            "Tabla scholarships: N filas",
            "ALU001 existe con status='excellent'",
            "ALU015 existe con status='at_risk'",
        ]:
            run(label, False, "Base de datos no encontrada")

    # Importar sqlite_query y verificar funciones
    try:
        from src.tools.sqlite_query import (  # noqa: F401
            get_academic_standing,
            get_current_enrollments,
            get_full_student_record,
            get_passed_subjects,
            get_pending_subjects,
            get_scholarships,
            get_student_profile,
            get_subject_records,
        )
        run("sqlite_query.py: 8 funciones importadas correctamente", True)

        record = get_full_student_record("ALU001")
        has_six_keys = (
            isinstance(record, dict)
            and "error" not in record
            and len(record) == 6
        )
        run("get_full_student_record('ALU001') devuelve dict con 6 claves",
            has_six_keys,
            f"Claves encontradas: {list(record.keys())}")
    except Exception as exc:
        run("sqlite_query.py: 8 funciones importadas correctamente", False, str(exc))
        run("get_full_student_record('ALU001') devuelve dict con 6 claves", False, str(exc))

    # ── Resultado final ────────────────────────────────────────────────────────
    print()
    print("══════════════════════════════════════════")
    status_str = "✓ TODAS LAS VERIFICACIONES PASARON" if passes == total else f"✗ {total - passes} verificación(es) fallaron"
    print(f"  RESULTADO: {passes}/{total} checks PASS — {status_str}")
    print("══════════════════════════════════════════")
    print()

    sys.exit(0 if passes == total else 1)


if __name__ == "__main__":
    main()

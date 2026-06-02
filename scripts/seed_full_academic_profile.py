"""Genera perfil academico completo para los 50 alumnos.

Pobla student_subject_attempts y student_grades de forma procedural,
coherente con el GPA y status de cada alumno.
Script idempotente: limpia las tablas antes de insertar.
"""

import random
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "database" / "students.db"

# Semilla para reproducibilidad
random.seed(42)

CATALOG = {
    "Ingenieria Informatica": {
        1: [
            ("INF101", "Algoritmica"), ("INF102", "Calculo"),
            ("INF103", "Programacion I"), ("INF104", "Logica"),
            ("INF105", "Estadistica"), ("INF106", "Algebra"),
            ("INF107", "Fisica"), ("INF108", "Programacion II"),
        ],
        2: [
            ("INF201", "Estructuras de Datos"), ("INF202", "Sistemas Operativos"),
            ("INF203", "Bases de Datos"), ("INF204", "Redes"),
            ("INF205", "Programacion Orientada a Objetos"),
            ("INF206", "Arquitectura de Computadores"),
            ("INF207", "Matematica Discreta"),
            ("INF208", "Ingenieria de Requisitos"),
        ],
        3: [
            ("INF301", "Ingenieria del Software"),
            ("INF302", "Inteligencia Artificial"),
            ("INF303", "Compiladores"),
            ("INF304", "Sistemas Distribuidos"),
            ("INF305", "Seguridad Informatica"),
            ("INF306", "Bases de Datos Avanzadas"),
            ("INF307", "Interaccion Persona-Ordenador"),
            ("INF308", "Aprendizaje Automatico"),
        ],
        4: [
            ("INF401", "Trabajo de Fin de Grado"),
            ("INF4E01", "Deep Learning"),
            ("INF4E02", "Procesamiento del Lenguaje Natural"),
            ("INF4E03", "Vision por Computador"),
            ("INF4E04", "Sistemas de Informacion Empresarial"),
            ("INF4E05", "Big Data"),
            ("INF4E06", "Robotica"),
        ],
    },
    "Informatica": {  # alias corto usado en la BD
        1: [
            ("INF101", "Algoritmica"), ("INF102", "Calculo"),
            ("INF103", "Programacion I"), ("INF104", "Logica"),
            ("INF105", "Estadistica"), ("INF106", "Algebra"),
            ("INF107", "Fisica"), ("INF108", "Programacion II"),
        ],
        2: [
            ("INF201", "Estructuras de Datos"), ("INF202", "Sistemas Operativos"),
            ("INF203", "Bases de Datos"), ("INF204", "Redes"),
            ("INF205", "Programacion Orientada a Objetos"),
            ("INF206", "Arquitectura de Computadores"),
            ("INF207", "Matematica Discreta"),
            ("INF208", "Ingenieria de Requisitos"),
        ],
        3: [
            ("INF301", "Ingenieria del Software"),
            ("INF302", "Inteligencia Artificial"),
            ("INF303", "Compiladores"),
            ("INF304", "Sistemas Distribuidos"),
            ("INF305", "Seguridad Informatica"),
            ("INF306", "Bases de Datos Avanzadas"),
            ("INF307", "Interaccion Persona-Ordenador"),
            ("INF308", "Aprendizaje Automatico"),
        ],
        4: [
            ("INF401", "Trabajo de Fin de Grado"),
            ("INF4E01", "Deep Learning"),
            ("INF4E02", "Procesamiento del Lenguaje Natural"),
            ("INF4E03", "Vision por Computador"),
            ("INF4E04", "Sistemas de Informacion Empresarial"),
            ("INF4E05", "Big Data"),
            ("INF4E06", "Robotica"),
        ],
    },
    "Administracion y Direccion de Empresas": {
        1: [
            ("ADE101", "Microeconomia"), ("ADE102", "Contabilidad I"),
            ("ADE103", "Matematicas Empresariales"),
            ("ADE104", "Introduccion al Derecho"),
            ("ADE105", "Historia Economica"),
            ("ADE106", "Estadistica Empresarial"),
            ("ADE107", "Sociologia de la Empresa"),
            ("ADE108", "Fundamentos de Marketing"),
        ],
        2: [
            ("ADE201", "Macroeconomia"), ("ADE202", "Contabilidad II"),
            ("ADE203", "Direccion Estrategica"),
            ("ADE204", "Finanzas Corporativas"),
            ("ADE205", "Recursos Humanos"),
            ("ADE206", "Marketing Estrategico"),
            ("ADE207", "Investigacion de Mercados"),
            ("ADE208", "Derecho Mercantil"),
        ],
        3: [
            ("ADE301", "Direccion Financiera"),
            ("ADE302", "Direccion de Operaciones"),
            ("ADE303", "Auditoria"),
            ("ADE304", "Sistemas de Informacion Empresarial"),
            ("ADE305", "Comercio Internacional"),
            ("ADE306", "Etica Empresarial"),
            ("ADE307", "Mercados Financieros"),
            ("ADE308", "Direccion Comercial"),
        ],
        4: [
            ("ADE401", "Trabajo de Fin de Grado"),
            ("ADE4E01", "Emprendimiento"),
            ("ADE4E02", "Marketing Digital"),
            ("ADE4E03", "Direccion de Proyectos"),
            ("ADE4E04", "Banca y Mercados Financieros"),
            ("ADE4E05", "Negocios Internacionales"),
        ],
    },
    "ADE": {  # alias corto
        1: [
            ("ADE101", "Microeconomia"), ("ADE102", "Contabilidad I"),
            ("ADE103", "Matematicas Empresariales"),
            ("ADE104", "Introduccion al Derecho"),
            ("ADE105", "Historia Economica"),
            ("ADE106", "Estadistica Empresarial"),
            ("ADE107", "Sociologia de la Empresa"),
            ("ADE108", "Fundamentos de Marketing"),
        ],
        2: [
            ("ADE201", "Macroeconomia"), ("ADE202", "Contabilidad II"),
            ("ADE203", "Direccion Estrategica"),
            ("ADE204", "Finanzas Corporativas"),
            ("ADE205", "Recursos Humanos"),
            ("ADE206", "Marketing Estrategico"),
            ("ADE207", "Investigacion de Mercados"),
            ("ADE208", "Derecho Mercantil"),
        ],
        3: [
            ("ADE301", "Direccion Financiera"),
            ("ADE302", "Direccion de Operaciones"),
            ("ADE303", "Auditoria"),
            ("ADE304", "Sistemas de Informacion Empresarial"),
            ("ADE305", "Comercio Internacional"),
            ("ADE306", "Etica Empresarial"),
            ("ADE307", "Mercados Financieros"),
            ("ADE308", "Direccion Comercial"),
        ],
        4: [
            ("ADE401", "Trabajo de Fin de Grado"),
            ("ADE4E01", "Emprendimiento"),
            ("ADE4E02", "Marketing Digital"),
            ("ADE4E03", "Direccion de Proyectos"),
            ("ADE4E04", "Banca y Mercados Financieros"),
            ("ADE4E05", "Negocios Internacionales"),
        ],
    },
    "Derecho": {
        1: [
            ("DER101", "Derecho Romano"),
            ("DER102", "Teoria del Derecho"),
            ("DER103", "Derecho Constitucional I"),
            ("DER104", "Derecho Civil I"),
            ("DER105", "Historia del Derecho"),
            ("DER106", "Economia Politica"),
            ("DER107", "Ciencia Politica"),
            ("DER108", "Derecho Penal I"),
        ],
        2: [
            ("DER201", "Derecho Constitucional II"),
            ("DER202", "Derecho Civil II"),
            ("DER203", "Derecho Penal II"),
            ("DER204", "Derecho Administrativo I"),
            ("DER205", "Derecho Internacional Publico"),
            ("DER206", "Derecho Procesal Civil"),
            ("DER207", "Derecho Mercantil I"),
            ("DER208", "Filosofia del Derecho"),
        ],
        3: [
            ("DER301", "Derecho Administrativo II"),
            ("DER302", "Derecho Civil III"),
            ("DER303", "Derecho Procesal Penal"),
            ("DER304", "Derecho del Trabajo"),
            ("DER305", "Derecho Financiero"),
            ("DER306", "Derecho Mercantil II"),
            ("DER307", "Derecho de la Union Europea"),
            ("DER308", "Derecho Internacional Privado"),
        ],
        4: [
            ("DER401", "Trabajo de Fin de Grado"),
            ("DER4E01", "Derecho de Familia y Sucesiones"),
            ("DER4E02", "Practicas Externas"),
            ("DER4E03", "Derecho Tributario"),
            ("DER4E04", "Derecho Concursal"),
            ("DER4E05", "Litigios Internacionales"),
        ],
    },
}

PERFILES = {
    "excellent": {
        "pass_first_try_prob": 0.90,
        "pass_second_try_prob": 0.95,
        "fail_prob": 0.02,
        "grade_range_pass": (8.0, 10.0),
        "grade_range_fail": (3.0, 4.5),
    },
    "active": {
        "pass_first_try_prob": 0.70,
        "pass_second_try_prob": 0.80,
        "fail_prob": 0.10,
        "grade_range_pass": (5.0, 8.5),
        "grade_range_fail": (2.5, 4.5),
    },
    "at_risk": {
        "pass_first_try_prob": 0.30,
        "pass_second_try_prob": 0.45,
        "fail_prob": 0.35,
        "grade_range_pass": (5.0, 7.0),
        "grade_range_fail": (1.0, 4.5),
    },
}


def _generate_subject_history(perfil: dict, current_year: int):
    """Genera historial de intentos para una asignatura.

    Returns:
        Tuple (status_final, lista_de_notas, anyo_ultimo).
        lista_de_notas: [(attempt_num, year, grade, passed), ...]
    """
    intentos = []
    year_first = current_year - 2
    if year_first < 2023:
        year_first = 2023

    for attempt in range(1, 5):
        year = year_first + (attempt - 1) // 2
        if attempt == 1:
            p = perfil["pass_first_try_prob"]
        elif attempt == 2:
            p = perfil["pass_second_try_prob"]
        else:
            p = 0.55

        if random.random() < p:
            grade = round(random.uniform(*perfil["grade_range_pass"]), 1)
            intentos.append((attempt, year, grade, 1))
            return "passed", intentos, year
        else:
            grade = round(random.uniform(*perfil["grade_range_fail"]), 1)
            intentos.append((attempt, year, grade, 0))

    # Sin aprobar tras 4 intentos
    if random.random() < 0.5:
        return "failed_last", intentos, intentos[-1][1]
    else:
        return (
            "pending",
            intentos[:-1],
            intentos[-2][1] if len(intentos) > 1 else year_first,
        )


def run():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        alumnos = conn.execute(
            "SELECT id, degree, year, status FROM students"
        ).fetchall()

        # Limpiar tablas para idempotencia
        conn.execute("DELETE FROM student_subject_attempts")
        conn.execute("DELETE FROM student_grades")

        total_attempts = 0
        total_grades = 0
        processed = 0

        for alu in alumnos:
            aid = alu["id"]
            degree = alu["degree"]
            year_now = int(alu["year"] or 1)
            status = alu["status"] or "active"
            perfil = PERFILES.get(status, PERFILES["active"])

            catalog = CATALOG.get(degree, {})
            if not catalog:
                continue

            processed += 1

            # Asignaturas cursadas: todos los anos previos + 5 del actual
            asignaturas = []
            for y in range(1, year_now):
                asignaturas.extend(catalog.get(y, []))
            asignaturas.extend(catalog.get(year_now, [])[:5])

            for subj_code, subj_name in asignaturas:
                status_final, intentos, last_year = _generate_subject_history(
                    perfil, 2026
                )

                conn.execute(
                    """INSERT OR REPLACE INTO student_subject_attempts
                       (student_id, subject_code, subject_name,
                        attempts_used, attempts_max, last_attempt_year, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (aid, subj_code, subj_name, len(intentos), 4,
                     last_year, status_final),
                )
                total_attempts += 1

                for attempt_num, year, grade, passed in intentos:
                    conn.execute(
                        """INSERT OR REPLACE INTO student_grades
                           (student_id, subject_code, subject_name,
                            attempt_number, academic_year, grade, passed)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (aid, subj_code, subj_name, attempt_num,
                         f"{year}-{year + 1}", grade, passed),
                    )
                    total_grades += 1

        conn.commit()
        print(f"OK - {processed} alumnos procesados (de {len(alumnos)} en BD)")
        print(f"     {total_attempts} registros en student_subject_attempts")
        print(f"     {total_grades} registros en student_grades")
    finally:
        conn.close()


if __name__ == "__main__":
    run()

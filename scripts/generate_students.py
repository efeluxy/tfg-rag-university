"""Genera y puebla data/database/students.db con 50 alumnos sintéticos.

Distribución:
  - 10 excelentes (GPA > 8.5, status='excellent')
  - 30 normales   (GPA 5.0-8.5, status='active')
  - 10 en riesgo  (GPA < 5.0, status='at_risk')
Repartidos en 3 grados y 4 cursos.
"""

import sqlite3
import os
import random
import sys

# ── Rutas ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, "data", "database", "students.db")

# ── Datos de asignaturas por grado ─────────────────────────────────────────────
SUBJECTS = {
    "Informatica": {
        1: [
            ("INF101", "Programación I", 6),
            ("INF102", "Matemáticas I", 6),
            ("INF103", "Álgebra Lineal", 6),
            ("INF104", "Lógica Computacional", 6),
            ("INF105", "Fundamentos de Computadores", 6),
            ("INF106", "Programación II", 6),
            ("INF107", "Matemáticas II", 6),
            ("INF108", "Estadística", 6),
            ("INF109", "Física para Informática", 6),
            ("INF110", "Metodología de la Programación", 6),
        ],
        2: [
            ("INF201", "Estructuras de Datos", 6),
            ("INF202", "Bases de Datos I", 6),
            ("INF203", "Redes I", 6),
            ("INF204", "Sistemas Operativos I", 6),
            ("INF205", "Arquitectura de Computadores", 6),
            ("INF206", "Ingeniería del Software I", 6),
            ("INF207", "Cálculo", 6),
            ("INF208", "Probabilidad y Modelos Estocásticos", 6),
            ("INF209", "Bases de Datos II", 6),
            ("INF210", "Programación Orientada a Objetos", 6),
        ],
        3: [
            ("INF301", "Inteligencia Artificial: Introducción", 6),
            ("INF302", "Redes II y Comunicaciones", 6),
            ("INF303", "Sistemas Operativos II", 6),
            ("INF304", "Ingeniería del Software II", 6),
            ("INF305", "Seguridad Informática", 6),
            ("INF306", "Compiladores e Intérpretes", 6),
            ("INF307", "Computación Paralela y Distribuida", 6),
            ("INF308", "Aprendizaje Automático", 6),
        ],
        4: [
            ("INF401", "Trabajo de Fin de Grado (parte 1)", 6),
            ("INF402", "Trabajo de Fin de Grado (parte 2)", 6),
            ("INF4E01", "Deep Learning y Redes Neuronales", 6),
            ("INF4E02", "Procesamiento del Lenguaje Natural", 6),
            ("INF4E05", "Cloud Computing y DevOps", 6),
        ],
    },
    "ADE": {
        1: [
            ("ADE101", "Introducción a la Economía", 6),
            ("ADE102", "Matemáticas Empresariales I", 6),
            ("ADE103", "Contabilidad Financiera I", 6),
            ("ADE104", "Fundamentos de Administración de Empresas", 6),
            ("ADE105", "Derecho de la Empresa", 6),
            ("ADE106", "Microeconomía", 6),
            ("ADE107", "Matemáticas Empresariales II", 6),
            ("ADE108", "Contabilidad Financiera II", 6),
            ("ADE109", "Estadística Empresarial I", 6),
            ("ADE110", "Historia Económica", 6),
        ],
        2: [
            ("ADE201", "Macroeconomía", 6),
            ("ADE202", "Estadística Empresarial II", 6),
            ("ADE203", "Contabilidad de Costes", 6),
            ("ADE204", "Organización de Empresas", 6),
            ("ADE205", "Derecho Mercantil", 6),
            ("ADE206", "Economía de la Empresa", 6),
            ("ADE207", "Dirección de Marketing", 6),
            ("ADE208", "Finanzas Empresariales I", 6),
            ("ADE209", "Recursos Humanos y Gestión del Talento", 6),
            ("ADE210", "Investigación de Mercados", 6),
        ],
        3: [
            ("ADE301", "Finanzas Empresariales II", 6),
            ("ADE302", "Dirección Estratégica", 6),
            ("ADE303", "Fiscalidad de la Empresa", 6),
            ("ADE304", "Auditoría Contable", 6),
            ("ADE305", "Economía Internacional", 6),
            ("ADE306", "Sistemas de Información Empresarial", 6),
            ("ADE307", "Comercio Internacional y Aduanas", 6),
            ("ADE308", "Derecho Laboral", 6),
        ],
        4: [
            ("ADE401", "Trabajo de Fin de Grado (parte 1)", 6),
            ("ADE402", "Trabajo de Fin de Grado (parte 2)", 6),
            ("ADE4E01", "Finanzas Cuantitativas", 6),
            ("ADE4E03", "Emprendimiento e Innovación", 6),
            ("ADE4E05", "Mercados Financieros", 6),
        ],
    },
    "Derecho": {
        1: [
            ("DER101", "Introducción al Derecho", 6),
            ("DER102", "Derecho Constitucional I", 6),
            ("DER103", "Derecho Civil I — Parte General", 6),
            ("DER104", "Historia del Derecho", 6),
            ("DER105", "Economía para Juristas", 6),
            ("DER106", "Derecho Constitucional II", 6),
            ("DER107", "Derecho Civil II — Obligaciones y Contratos", 6),
            ("DER108", "Derecho Penal I — Parte General", 6),
            ("DER109", "Derecho Romano", 6),
            ("DER110", "Filosofía del Derecho", 6),
        ],
        2: [
            ("DER201", "Derecho Civil III — Derechos Reales", 6),
            ("DER202", "Derecho Penal II — Parte Especial", 6),
            ("DER203", "Derecho Administrativo I", 6),
            ("DER204", "Derecho Mercantil I", 6),
            ("DER205", "Derecho del Trabajo I", 6),
            ("DER206", "Derecho Civil IV — Familia y Sucesiones", 6),
            ("DER207", "Derecho Administrativo II", 6),
            ("DER208", "Derecho Mercantil II — Sociedades", 6),
            ("DER209", "Derecho del Trabajo II", 6),
            ("DER210", "Derecho Financiero y Tributario I", 6),
        ],
        3: [
            ("DER301", "Derecho Procesal Civil", 6),
            ("DER302", "Derecho Procesal Penal", 6),
            ("DER303", "Derecho Internacional Público", 6),
            ("DER304", "Derecho Financiero y Tributario II", 6),
            ("DER305", "Derecho Mercantil III — Contratos", 6),
            ("DER306", "Derecho Internacional Privado", 6),
            ("DER307", "Derecho Comunitario Europeo", 6),
            ("DER308", "Derecho Procesal Administrativo", 6),
        ],
        4: [
            ("DER401", "Trabajo de Fin de Grado (parte 1)", 6),
            ("DER402", "Trabajo de Fin de Grado (parte 2)", 6),
            ("DER4E03", "Propiedad Intelectual e Industrial", 6),
            ("DER4E05", "Derecho Digital y Nuevas Tecnologías", 6),
            ("DER4E11", "Arbitraje y Resolución Alternativa de Conflictos", 6),
        ],
    },
}

NOMBRES = [
    "Alejandro", "María", "Carlos", "Laura", "David", "Ana", "Pablo", "Elena",
    "Miguel", "Sara", "Javier", "Lucía", "Andrés", "Carmen", "Diego", "Sofía",
    "Marcos", "Patricia", "Adrián", "Isabel", "Sergio", "Marta", "Álvaro",
    "Cristina", "Roberto", "Nuria", "Fernando", "Raquel", "Gonzalo", "Beatriz",
    "Ricardo", "Alicia", "Eduardo", "Pilar", "Manuel", "Rosa", "Ignacio",
    "Natalia", "Felipe", "Silvia",
]
APELLIDOS = [
    "García", "Martínez", "López", "Sánchez", "González", "Rodríguez",
    "Fernández", "Pérez", "Gómez", "Díaz", "Torres", "Ruiz", "Moreno",
    "Jiménez", "Álvarez", "Romero", "Navarro", "Domínguez", "Herrera",
    "Medina", "Castillo", "Santos", "Lara", "Ortega", "Guerrero", "Cano",
    "Prieto", "Molina", "Delgado", "Vega", "Serrano", "Blanco", "Iglesias",
    "Vargas", "Cruz", "Ramos", "Alonso", "Ríos", "Campos", "Peña",
]


def random_name() -> tuple[str, str]:
    """Devuelve (nombre, apellidos) aleatorios."""
    nombre = random.choice(NOMBRES)
    apellidos = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
    return nombre, apellidos


def make_grade(status: str) -> float:
    """Genera una nota media coherente con el status del alumno."""
    if status == "excellent":
        return round(random.uniform(8.6, 9.8), 2)
    elif status == "active":
        return round(random.uniform(5.0, 8.4), 2)
    else:  # at_risk
        return round(random.uniform(3.0, 4.9), 2)


def credits_for_course(degree: str, year: int) -> int:
    """Calcula los créditos completados esperados según curso."""
    total_per_year = 60
    return total_per_year * (year - 1)


def build_subject_records(student_id: str, degree: str, year: int, status: str, gpa: float) -> list[dict]:
    """Genera el historial de asignaturas coherente con el perfil del alumno."""
    records = []
    subjs = SUBJECTS[degree]

    # Cursos anteriores: asignaturas pasadas
    for prev_year in range(1, year):
        for code, name, credits in subjs[prev_year]:
            if status == "excellent":
                grade = round(random.uniform(7.5, 9.8), 1)
                subj_status = "passed"
            elif status == "active":
                # 85% aprobadas, 15% suspensas en su momento (pero ahora pasadas)
                grade = round(random.uniform(5.0, 8.5), 1)
                subj_status = "passed"
            else:  # at_risk — algunas suspensas, algunas pasadas
                roll = random.random()
                if roll < 0.5:
                    grade = round(random.uniform(5.0, 7.0), 1)
                    subj_status = "passed"
                else:
                    grade = round(random.uniform(2.5, 4.9), 1)
                    subj_status = "failed"
            sem = f"202{3 + prev_year - 1}-{random.choice([1, 2])}"
            records.append({
                "student_id": student_id,
                "subject_code": code,
                "subject_name": name,
                "credits": credits,
                "grade": grade,
                "semester": sem,
                "status": subj_status,
            })

    # Curso actual: matriculadas + algunas pendientes
    current_subjs = subjs.get(year, [])
    for i, (code, name, credits) in enumerate(current_subjs):
        if i < 5:  # primeras 5: matriculadas este semestre
            records.append({
                "student_id": student_id,
                "subject_code": code,
                "subject_name": name,
                "credits": credits,
                "grade": None,
                "semester": "2024-2",
                "status": "enrolled",
            })
        else:  # restantes: pendientes
            records.append({
                "student_id": student_id,
                "subject_code": code,
                "subject_name": name,
                "credits": credits,
                "grade": None,
                "semester": "2024-2",
                "status": "pending",
            })

    return records


def build_scholarships(student_id: str, gpa: float, year: int, status: str) -> list[dict]:
    """Genera becas según perfil."""
    scholarships = []
    if gpa >= 8.5:
        scholarships.append({
            "student_id": student_id,
            "type": "universidad",
            "amount": 500.0,
            "year": 2024,
            "status": "active",
        })
    if 5.0 <= gpa <= 8.4 and random.random() < 0.4:
        scholarships.append({
            "student_id": student_id,
            "type": "MEC",
            "amount": random.choice([1500.0, 2000.0, 2500.0]),
            "year": 2024,
            "status": "active",
        })
    if year >= 3 and gpa >= 6.5 and random.random() < 0.2:
        scholarships.append({
            "student_id": student_id,
            "type": "movilidad",
            "amount": 350.0 * random.randint(4, 9),
            "year": 2024,
            "status": random.choice(["active", "pending"]),
        })
    return scholarships


def create_schema(conn: sqlite3.Connection) -> None:
    """Crea las tablas en la base de datos."""
    conn.executescript("""
        DROP TABLE IF EXISTS scholarships;
        DROP TABLE IF EXISTS subject_records;
        DROP TABLE IF EXISTS students;

        CREATE TABLE students (
            id                TEXT PRIMARY KEY,
            name              TEXT NOT NULL,
            email             TEXT UNIQUE,
            degree            TEXT,
            year              INTEGER,
            gpa               REAL,
            credits_completed INTEGER,
            credits_total     INTEGER,
            status            TEXT,
            enrolled_year     INTEGER
        );

        CREATE TABLE subject_records (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   TEXT REFERENCES students(id),
            subject_code TEXT,
            subject_name TEXT,
            credits      INTEGER,
            grade        REAL,
            semester     TEXT,
            status       TEXT
        );

        CREATE TABLE scholarships (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT REFERENCES students(id),
            type       TEXT,
            amount     REAL,
            year       INTEGER,
            status     TEXT
        );
    """)


def main() -> None:
    random.seed(42)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)

    # ── Definición de los 50 alumnos ─────────────────────────────────────────
    # IDs especiales fijados: ALU001, ALU015, ALU030, ALU045
    # Resto se asigna a los IDs libres en orden

    SPECIAL: dict[str, tuple[str, int, str]] = {
        "ALU001": ("Informatica", 4, "excellent"),
        "ALU015": ("Informatica", 2, "at_risk"),
        "ALU030": ("ADE", 3, "active"),
        "ALU045": ("Derecho", 1, "active"),
    }
    special_ids = set(SPECIAL.keys())

    # IDs libres (1-50 excluidos los especiales)
    free_ids = [f"ALU{n:03d}" for n in range(1, 51) if f"ALU{n:03d}" not in special_ids]

    # Perfiles para los 46 alumnos genéricos (total 50 = 4 especiales + 46 genéricos)
    # Distribución objetivo: 10 excellent, 30 active, 10 at_risk
    # Especiales aportan: 1 excellent (ALU001), 1 at_risk (ALU015), 2 active (ALU030, ALU045)
    # Genéricos necesitan: 9 excellent, 28 active, 9 at_risk  → total 46
    generic_profiles: list[tuple[str, int, str]] = (
        # Informática: 7 excellent, 10 active, 1 at_risk = 18
        [("Informatica", 1, "excellent")] * 2
        + [("Informatica", 2, "excellent")] * 2
        + [("Informatica", 3, "excellent")] * 2
        + [("Informatica", 4, "excellent")] * 1
        + [("Informatica", 1, "active")] * 2
        + [("Informatica", 2, "active")] * 3
        + [("Informatica", 3, "active")] * 3
        + [("Informatica", 4, "active")] * 2
        + [("Informatica", 3, "at_risk")] * 1
        # ADE: 2 excellent, 9 active, 3 at_risk = 14
        + [("ADE", 1, "excellent")] * 1
        + [("ADE", 2, "excellent")] * 1
        + [("ADE", 1, "active")] * 3
        + [("ADE", 2, "active")] * 3
        + [("ADE", 4, "active")] * 3
        + [("ADE", 1, "at_risk")] * 1
        + [("ADE", 2, "at_risk")] * 1
        + [("ADE", 3, "at_risk")] * 1
        # Derecho: 0 excellent, 9 active, 5 at_risk = 14
        + [("Derecho", 2, "active")] * 2
        + [("Derecho", 3, "active")] * 3
        + [("Derecho", 4, "active")] * 4
        + [("Derecho", 1, "at_risk")] * 2
        + [("Derecho", 2, "at_risk")] * 2
        + [("Derecho", 3, "at_risk")] * 1
    )
    # Verificación en tiempo de ejecución
    assert len(generic_profiles) == 46, f"Expected 46 generic profiles, got {len(generic_profiles)}"
    random.shuffle(generic_profiles)

    # Construir student_defs: primero especiales, luego el resto con IDs libres
    student_defs: list[tuple[str, str, int, str]] = []
    for sid, (deg, yr, st) in SPECIAL.items():
        student_defs.append((sid, deg, yr, st))
    for sid, (deg, yr, st) in zip(free_ids, generic_profiles):
        student_defs.append((sid, deg, yr, st))

    # Ordenar por ID para inserción limpia
    student_defs.sort(key=lambda x: x[0])

    # ── Insertar alumnos ────────────────────────────────────────────────────
    counts = {"excellent": 0, "active": 0, "at_risk": 0}

    all_scholarships: list[dict] = []
    all_records: list[dict] = []

    used_names: set[str] = set()

    for stu_id, degree, year, status in student_defs:
        # Forzar GPA para alumnos especiales
        if stu_id == "ALU001":
            gpa = 9.1
        elif stu_id == "ALU015":
            gpa = 4.2
        elif stu_id == "ALU030":
            gpa = 7.8
        elif stu_id == "ALU045":
            gpa = 5.5
        else:
            gpa = make_grade(status)

        # Nombre único
        while True:
            nombre, apellidos = random_name()
            full = f"{nombre} {apellidos}"
            if full not in used_names:
                used_names.add(full)
                break

        slug = nombre.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        email = f"{slug}.{stu_id.lower()}@universidad.es"

        credits_completed = credits_for_course(degree, year)
        credits_total = 240

        # ALU045: recién matriculado, sin historial
        if stu_id == "ALU045":
            credits_completed = 0

        enrolled_year = 2025 - year

        conn.execute(
            """INSERT INTO students
               (id, name, email, degree, year, gpa, credits_completed, credits_total, status, enrolled_year)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (stu_id, f"{nombre} {apellidos}", email, degree, year, gpa,
             credits_completed, credits_total, status, enrolled_year),
        )
        counts[status] += 1

        # Asignaturas
        records = build_subject_records(stu_id, degree, year, status, gpa)
        # ALU045: solo matriculadas, sin historial de aprobadas
        if stu_id == "ALU045":
            records = [r for r in records if r["status"] == "enrolled"]
        all_records.extend(records)

        # Becas
        schols = build_scholarships(stu_id, gpa, year, status)
        # ALU030 debe tener beca MEC activa de 1500€
        if stu_id == "ALU030":
            schols = [s for s in schols if s["type"] != "MEC"]
            schols.append({"student_id": "ALU030", "type": "MEC", "amount": 1500.0, "year": 2024, "status": "active"})
        all_scholarships.extend(schols)

    # Insertar subject_records
    conn.executemany(
        """INSERT INTO subject_records
           (student_id, subject_code, subject_name, credits, grade, semester, status)
           VALUES (:student_id, :subject_code, :subject_name, :credits, :grade, :semester, :status)""",
        all_records,
    )

    # Insertar scholarships
    conn.executemany(
        """INSERT INTO scholarships (student_id, type, amount, year, status)
           VALUES (:student_id, :type, :amount, :year, :status)""",
        all_scholarships,
    )

    conn.commit()

    # ── Resumen ──────────────────────────────────────────────────────────────
    n_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    n_records = conn.execute("SELECT COUNT(*) FROM subject_records").fetchone()[0]
    n_schols = conn.execute("SELECT COUNT(*) FROM scholarships").fetchone()[0]

    conn.close()

    print(f"Base de datos creada: {n_students} alumnos, "
          f"{counts['excellent']} excellent, {counts['active']} active, {counts['at_risk']} at_risk")
    print(f"Tablas: students ({n_students} filas), "
          f"subject_records ({n_records} filas), scholarships ({n_schols} filas)")
    print(f"Ruta: {DB_PATH}")


if __name__ == "__main__":
    main()

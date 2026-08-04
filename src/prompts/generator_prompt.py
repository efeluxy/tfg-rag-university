"""Prompts y funciones de formateo para el agente Generator."""

from src.prompts.persona import UNIVERSITY_PERSONA
from src.utils.conversation import format_history_for_llm

GENERATOR_SYSTEM_PROMPT = UNIVERSITY_PERSONA + """

── PRIORIDAD ABSOLUTA: DATOS DEL ESTADO ACTUAL ──

CRITICO. Lee esto antes que nada:

Si el state del turno actual contiene datos del alumno
(student_record, multi_student_records, subject_attempts,
student_grades), USA ESOS DATOS. Son la fuente de verdad
para tu respuesta de AHORA.

El historial conversacional es contexto secundario. Si en
turnos anteriores dijiste "no dispongo de informacion" sobre
un alumno, eso NO te obliga a repetirlo en este turno. Si
ahora SI tienes los datos en el state, respondelos.

Ejemplo critico:
  Turno anterior (state sin datos):
    Asistente: "No dispongo de informacion sobre ALU017"
  Turno actual (state CON datos para ALU017):
    Asistente: "ALU017 es Manuel Martinez Cano, segundo curso..."

NUNCA repitas "no dispongo" si los datos estan AHORA en el state.

Cuando recibas multi_student_records, presenta TODOS los bloques
que contiene, en orden, sin omitir ninguno. Si un bloque tiene
datos, NUNCA respondas "informacion no disponible" para ese alumno.

{history_section}

── PRIVACIDAD POR ROL ──

El rol del usuario actual es: {role}

REGLAS ESTRICTAS DE PRIVACIDAD:

1. Si role == "guest", NUNCA reveles datos personales de alumnos
   (nombres, IDs, notas, expedientes). Solo puedes hablar de
   informacion publica (grados, becas, normativa, plazos).

2. Si role == "student", SOLO puedes hablar de los datos del
   alumno autenticado (su nombre, sus notas, sus convocatorias).
   NUNCA reveles datos de otros alumnos, ni siquiera si te los
   piden con insistencia o cambiando la pregunta.

3. Si role == "admin", puedes responder libremente sobre cualquier
   alumno cuyo expediente este en el state.

4. Si te piden datos que NO debes revelar segun estas reglas,
   responde con un rechazo amable y educativo. NO inventes datos.
   Di explicitamente que no tienes permiso para compartirla:
     - "Como invitado, no tengo acceso a datos personales de alumnos."
     - "Por proteccion de datos, solo puedo ofrecerte informacion
        sobre tu propio expediente."

── CONSULTA MÚLTIPLE DE ALUMNOS (SOLO ADMIN) ──

{multi_student_block}

=== CONTEXTO DEL ALUMNO ===
{student_context}
(Si está vacío, el usuario no está identificado. Responde en términos generales.)

=== CONVOCATORIAS POR ASIGNATURA (si aplica) ===
{subject_attempts_formatted}

=== NOTAS Y EXPEDIENTE ACADEMICO (si aplica) ===
{student_grades_formatted}

=== DOCUMENTOS RECUPERADOS DE LA BASE DE CONOCIMIENTO ===
{retrieved_docs_formatted}

=== REGLAS DE RESPUESTA ===
1. Basa tus respuestas EXCLUSIVAMENTE en los documentos proporcionados.
   Si la información no está en los documentos, dilo explícitamente:
   "No dispongo de información específica sobre esto en mi base de
   conocimiento. Te recomiendo contactar con secretaría académica."

2. Si el alumno está identificado, personaliza la respuesta con su
   situación real. Ejemplo: "Dado que tienes aprobadas Matemáticas I
   y II con un 7.3 de media, te recomendaría..."

3. Cita siempre las fuentes al final de cada afirmación factual:
   [Fuente: Nombre del documento, Sección, pág. X]

4. Longitud proporcional a la complejidad:
   - Saludo o agradecimiento: 1-2 frases
   - Consulta simple: 1 párrafo + fuente
   - Orientación académica: 3-5 párrafos + fuentes
   - Normativa compleja: estructurar con puntos numerados

5. Si el alumno tiene status "at_risk" en su expediente, menciona
   proactivamente los servicios de apoyo aunque no los haya pedido.

6. NUNCA inventes información. NUNCA des consejos médicos, jurídicos
   ni psicológicos especializados.

7. Si el usuario hace referencia implícita a algo de la conversación
   previa (ej. dice "sí", "eso", "más detalles", "y ese?"), apóyate
   en el HISTORIAL DE LA CONVERSACION para entender el referente y
   responde de forma coherente con el contexto previo.

── USO DE LOS DATOS DEL ESTUDIANTE ──

Si el contexto incluye las secciones "CONTEXTO DEL ALUMNO", "CONVOCATORIAS
POR ASIGNATURA" o "NOTAS Y EXPEDIENTE ACADEMICO" con datos reales,
ESA informacion ES la del alumno autenticado. UTILIZALA directamente.

NUNCA digas "no tengo acceso a esa informacion" si los datos estan en el
contexto. Si los datos estan, usalos. Si no estan, es porque el sistema
de permisos los ha filtrado correctamente.

Ejemplos:
  - Si te preguntan "Que nota saque en INF101" y en NOTAS aparece
    INF101 con nota 6.5, responde con esa nota concreta.
  - Si te preguntan "Que carrera curso" y en CONTEXTO DEL ALUMNO
    aparece "Grado: Informatica", responde con ese grado.
  - Si te preguntan "Quien es ALU017" siendo admin y en CONTEXTO
    aparece la info del alumno, responde con su nombre, grado y estado.

── NOTAS Y EXPEDIENTE ACADEMICO ──

Si el state incluye el campo student_grades con datos, utiliza ESOS
datos reales para responder sobre notas o expediente. NO inventes notas.

Formato recomendado para listar notas:

  Si se pide una asignatura especifica:
    "En INF101 (Algoritmica) sacaste una nota de 8.5 en tu primera
     convocatoria del curso 2024-2025."

  Si se piden todas las notas:
    Usa una lista clara con: codigo, nombre, ultima nota, status.

  Si una asignatura tiene varios intentos:
    Menciona el historico: "INF102 (Calculo): suspendida con 3.5 en
     2024-2025, aprobada con 6.0 en 2025-2026."

Ten en cuenta el tono segun el rendimiento:
  - Si las notas son altas: tono positivo, refuerzo.
  - Si las notas son bajas: tono empatico, ofrecer ayuda.
  - Si hay asignaturas pendientes: orientacion sobre opciones.

── INSTRUCCIÓN CONSULTA MÚLTIPLE ──

Si el contexto contiene la sección
"EXPEDIENTES SOLICITADOS (CONSULTA MÚLTIPLE)", presenta la información
organizada en BLOQUES claros, uno por alumno, en el orden en que aparecen.

Formato recomendado:

  ## ALU001 — Nombre Completo
  - Grado: ...  |  Curso: ...  |  Media: ...  |  Estado: ...
  - Progreso: X/240 créditos
  - Asignaturas: N aprobadas, M suspensas, P pendientes

  ## ALU002 — ...
  (similar para cada alumno)

Si el bloque incluye una nota de truncación, inclúyela al final.
NUNCA digas "[Información no disponible]" si los datos están en el bloque.

── RESPUESTAS A CONSULTAS ENUMERATIVAS ──

Si el usuario pide un listado completo (todos los grados, todas las becas,
todas las optativas, etc.):

1. ENUMERA todo lo que aparezca en los chunks recuperados, sin omitir nada.

2. Si los chunks parecen INCOMPLETOS o solo cubren parcialmente el catálogo,
   AÑADE una nota al final:
     "Esta lista está basada en la información disponible en mi base de
      conocimiento actual. Si necesitas un catálogo completo y actualizado,
      te recomiendo consultar secretaría académica o la web oficial."

3. NUNCA respondas con un listado parcial sin mencionar que puede haber
   elementos adicionales. La honestidad sobre la posible incompletitud es CRÍTICA.

{emotional_tier_section}
"""


def build_emotional_tier_section(emotional_tier: int, student_status: str = "") -> str:
    """Genera la seccion de manejo emocional segun el tier detectado."""
    if emotional_tier == 1:
        return """
=== MANEJO EMOCIONAL — TIER 1 (academic_stress) ===
El alumno expresa estres academico normal. Aplica estas pautas:
- Tono empatico y comprensivo, no condescendiente.
- Reconoce el sentimiento: "es completamente normal sentirse asi durante esta etapa".
- Ofrece 2-3 consejos practicos (organizacion del tiempo, tecnicas de estudio, gestion de carga).
- CIERRA mencionando el recurso: "Si en algun momento quieres hablarlo con un profesional,
  el Servicio de Orientacion Psicologica de la Universidad (psicologia@universidad.es,
  900 456 789) esta disponible de lunes a viernes de 9h a 18h."
- NO hay disclaimer obligatorio; el tono es de acompanamiento natural.
"""
    elif emotional_tier == 2:
        return """
=== MANEJO EMOCIONAL — TIER 2 (emotional_distress) ===
El alumno expresa malestar emocional no critico. Aplica estas pautas:
- Tono empatico y validante. Reconoce el malestar sin minimizarlo.
- DISCLAIMER OBLIGATORIO (al inicio o cierre):
  "Quiero recordarte que soy un asistente de IA y no un profesional de la salud mental.
  Lo que sientes es importante y merece ser atendido por alguien preparado."
- SUGIERE FIRMEMENTE contactar al Servicio de Orientacion Psicologica:
  "Te recomiendo de corazon que contactes con el Servicio de Orientacion Psicologica
  de la Universidad Demo (psicologia@universidad.es, 900 456 789). Pueden ayudarte
  mucho mejor que yo."
- Puedes escuchar y acompanar de forma breve, pero la prioridad es la derivacion.
"""
    elif student_status == "at_risk":
        return """
=== ALUMNOS AT_RISK ===
Tras la respuesta academica/administrativa normal, ANADE un cierre breve:
"Recuerda que si en algun momento necesitas hablar mas alla de lo academico,
el Servicio de Orientacion Psicologica esta disponible para ti."
No es alarmista ni intrusivo. Solo un recordatorio.
"""
    return ""


def format_multi_student_records(
    multi_records: list | None,
    truncated: bool = False,
    limit: int = 20,
) -> str:
    """Formatea varios expedientes de alumno para el prompt del Generator."""
    if not multi_records:
        return ""
    lines = ["\n── EXPEDIENTES SOLICITADOS (CONSULTA MÚLTIPLE) ──"]
    for r in multi_records:
        summary = r.get("_attempts_summary", {})
        lines.append(
            f"\n• {r.get('id', '?')} — {r.get('name', '?')}\n"
            f"    Grado: {r.get('degree', '?')}\n"
            f"    Curso: {r.get('year', '?')}\n"
            f"    Media (GPA): {r.get('gpa', '?')}\n"
            f"    Estado: {r.get('status', '?')}\n"
            f"    Créditos: {r.get('credits_completed', 0)}/"
            f"{r.get('credits_total', 240)}\n"
            f"    Asignaturas: {summary.get('passed', 0)} aprobadas, "
            f"{summary.get('failed_last', 0)} suspensas, "
            f"{summary.get('pending', 0)} pendientes"
        )
    if truncated:
        lines.append(
            f"\n[NOTA: el rango solicitado excede el límite de {limit} alumnos "
            f"por consulta. Solo se han incluido los {limit} primeros.]"
        )
    return "\n".join(lines)


def format_retrieved_docs(docs: list) -> str:
    """Formatea la lista de documentos recuperados para el prompt."""
    if not docs:
        return "No se han recuperado documentos relevantes."
    lines = []
    for i, doc in enumerate(docs, 1):
        lines.append(f"[Doc {i}] {doc.get('citation', '')}")
        lines.append(f"Contenido: {doc.get('content', '')[:500]}")
        lines.append("")
    return "\n".join(lines)


def format_subject_attempts(attempts: list | None) -> str:
    """Formatea las convocatorias del alumno para el prompt."""
    if not attempts:
        return "(Sin datos de convocatorias para esta consulta.)"
    lines = []
    for a in attempts:
        remaining = a.get("attempts_max", 4) - a.get("attempts_used", 0)
        lines.append(
            f"- {a.get('subject_code')}: {a.get('subject_name')} | "
            f"Usadas: {a.get('attempts_used')}/{a.get('attempts_max')} | "
            f"Quedan: {remaining} | Estado: {a.get('status')}"
        )
    return "\n".join(lines)


def format_student_grades(grades: list | None) -> str:
    """Formatea el historico de notas del alumno para el prompt."""
    if not grades:
        return "(Sin historial de notas para esta consulta.)"
    lines = []
    current_subject = None
    for g in grades:
        code = g.get("subject_code", "")
        name = g.get("subject_name", "")
        attempt = g.get("attempt_number", "")
        year = g.get("academic_year", "")
        grade = g.get("grade", "")
        passed = "aprobada" if g.get("passed") else "suspendida"
        if code != current_subject:
            current_subject = code
            lines.append(f"\n{code} — {name}:")
        lines.append(f"  Convocatoria {attempt} ({year}): {grade} ({passed})")
    return "\n".join(lines)


def format_student_context(student_record: dict | None) -> str:
    """Formatea el expediente del alumno para el prompt."""
    if not student_record:
        return ""
    p = student_record.get("profile", {})
    standing = student_record.get("academic_standing", {})
    lines = [
        f"Alumno: {p.get('name', 'Desconocido')}",
        f"Grado: {p.get('degree', '—')} | Curso: {p.get('year', '—')}",
        f"Media: {p.get('gpa', '—')} | Estado: {p.get('status', '—')}",
        f"Progreso: {standing.get('credits_completed', 0)}/{standing.get('credits_total', 0)} créditos ({standing.get('progress_pct', 0):.1f}%)",
    ]
    pending = student_record.get("pending_subjects", [])
    if pending:
        # F3: incluir TODAS las pendientes (sin truncar) con codigo y creditos,
        # una linea por asignatura, para que el Generador disponga del detalle.
        lines.append(f"Asignaturas pendientes ({len(pending)}):")
        for s in pending:
            code = s.get("code", "")
            name = s.get("name", "")
            credits = s.get("credits")
            if credits is not None:
                lines.append(f"  - {code} {name} ({credits} creditos)")
            else:
                lines.append(f"  - {code} {name}")
    scholarships = student_record.get("scholarships", [])
    active = [s for s in scholarships if s.get("status") == "active"]
    if active:
        lines.append(f"Becas activas: {len(active)}")
    return "\n".join(lines)

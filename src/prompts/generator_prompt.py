"""Prompts y funciones de formateo para el agente Generator."""

from src.prompts.persona import UNIVERSITY_PERSONA

GENERATOR_SYSTEM_PROMPT = UNIVERSITY_PERSONA + """

=== CONTEXTO DEL ALUMNO ===
{student_context}
(Si está vacío, el usuario no está identificado. Responde en términos generales.)

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
"""


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
        names = [s.get("subject_name", "") for s in pending[:3]]
        lines.append(f"Asignaturas pendientes: {', '.join(names)}")
    scholarships = student_record.get("scholarships", [])
    active = [s for s in scholarships if s.get("status") == "active"]
    if active:
        lines.append(f"Becas activas: {len(active)}")
    return "\n".join(lines)

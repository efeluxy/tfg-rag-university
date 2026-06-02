"""Diccionario de sinonimos universitarios y utilidad de expansion de consultas.

Cada SET contiene terminos considerados equivalentes en el dominio
academico. Cuando una consulta contiene UNO de los terminos, se
expande con TODOS los del grupo para mejorar el recall del retriever.
"""

SYNONYM_GROUPS: list[set] = [
    {"grado", "carrera", "titulacion", "titulacion", "estudios"},
    {"asignatura", "materia", "curso"},
    {"profe", "profesor", "docente", "profesora"},
    {"nota", "calificacion", "calificacion", "puntuacion", "puntuacion"},
    {"media", "promedio", "gpa", "expediente"},
    {"convocatoria", "intento", "oportunidad"},
    {"beca", "ayuda economica", "ayuda al estudio", "subvencion", "subvencion"},
    {"secretaria", "administracion", "secretaria academica"},
    {"matricula", "matriculacion", "inscripcion", "inscripcion"},
    {"examen", "prueba", "evaluacion", "evaluacion", "test"},
    {"credito", "ects", "creditos", "creditos"},
    {"plan de estudios", "plan academico", "curriculo", "curriculo"},
    {"trabajo de fin de grado", "tfg", "proyecto fin de grado", "proyecto final"},
    {"facultad", "centro", "escuela"},
    {"departamento", "area"},
    {"alumno", "estudiante", "matriculado"},
    {"tutor", "mentor", "orientador"},
    {"horario", "calendario", "agenda"},
    {"aula", "clase", "sala"},
    {"practica", "laboratorio", "practicas externas"},
    {"obligatoria", "troncal", "basica"},
    {"optativa", "electiva", "opcional"},
]


def expand_query_with_synonyms(query: str, max_extra_terms: int = 8) -> str:
    """Expande la consulta con sinonimos relevantes.

    Mantiene la query original intacta al inicio y anade hasta
    max_extra_terms terminos sinonimos al final.

    Args:
        query: Consulta original del usuario.
        max_extra_terms: Numero maximo de terminos adicionales.

    Returns:
        Query expandida, o la query original si no hay matches.
    """
    if not query:
        return query
    query_lower = query.lower()
    additions: set = set()
    for group in SYNONYM_GROUPS:
        detected = any(term in query_lower for term in group)
        if detected:
            for term in group:
                if term not in query_lower:
                    additions.add(term)
    if not additions:
        return query
    extra = " ".join(sorted(additions)[:max_extra_terms])
    return f"{query} {extra}"


def get_synonym_groups() -> list[set]:
    """Devuelve los grupos de sinonimos para testing e inspeccion."""
    return SYNONYM_GROUPS

"""Fase 5, Bloque 5.1: Generacion del dataset de evaluacion para RAGAS.

Genera 30 muestras curadas con preguntas reales, las pasa por el grafo
y captura respuestas y contextos para evaluacion RAGAS (API 0.1.x).

Uso:
    python scripts/generate_eval_dataset.py
"""

import json
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configurar paths
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 30 MUESTRAS CURADAS (question + ground_truth)
# Distribución: normativas(6), planes_estudio(5), guias_docentes(6),
#               faqs(8), procedimientos(5)
# Intents: ACADEMIC_ORIENTATION, ADMINISTRATIVE, COURSE_INFO,
#          REGULATIONS, PROSPECTIVE_STUDENT, SCHOLARSHIPS
# ---------------------------------------------------------------------------

CURATED_SAMPLES = [
    # ── NORMATIVAS (~6) ──────────────────────────────────────────────────────
    {
        "id": "N01",
        "category": "normativas",
        "intent": "REGULATIONS",
        "question": "Cuantas convocatorias tiene un alumno para superar una asignatura?",
        "ground_truth": (
            "Los alumnos disponen de un maximo de 4 convocatorias ordinarias para superar "
            "cada asignatura. Existe ademas la posibilidad de solicitar una convocatoria "
            "extraordinaria al Consejo de Departamento si se han agotado las ordinarias, "
            "sumando un total de hasta 6 convocatorias en situaciones excepcionales."
        ),
    },
    {
        "id": "N02",
        "category": "normativas",
        "intent": "REGULATIONS",
        "question": "Que ocurre si un alumno suspende mas del 50% de los creditos matriculados?",
        "ground_truth": (
            "Segun el reglamento de permanencia, si un alumno suspende mas del 50% "
            "de los creditos en los que se ha matriculado durante dos cursos consecutivos, "
            "puede quedar sujeto a limitaciones en la matricula del siguiente curso. "
            "En casos graves puede llegarse a la exclusion del grado, aunque siempre "
            "previo expediente y con posibilidad de alegaciones."
        ),
    },
    {
        "id": "N03",
        "category": "normativas",
        "intent": "REGULATIONS",
        "question": "Como se calcula la nota final de una asignatura con evaluacion continua?",
        "ground_truth": (
            "En asignaturas con evaluacion continua, la nota final se obtiene ponderando "
            "las pruebas parciales, los trabajos entregados y el examen final. "
            "Cada guia docente especifica los porcentajes; habitualmente el examen "
            "final pondera entre el 50% y el 70% de la nota total, y las actividades "
            "de evaluacion continua el resto. Para aprobar es necesario obtener "
            "un minimo de 5 sobre 10 en el conjunto de la evaluacion."
        ),
    },
    {
        "id": "N04",
        "category": "normativas",
        "intent": "REGULATIONS",
        "question": "Que es la normativa de permanencia y cuando se aplica?",
        "ground_truth": (
            "La normativa de permanencia establece los requisitos minimos que los "
            "alumnos deben cumplir para continuar en el grado. Se aplica cuando "
            "el rendimiento academico es muy bajo: si en los dos primeros cursos "
            "el alumno no supera al menos 12 creditos por curso, puede ser derivado "
            "a tutoria academica obligatoria. Esta normativa busca detectar dificultades "
            "a tiempo y ofrecer orientacion antes de que sea necesaria la baja."
        ),
    },
    {
        "id": "N05",
        "category": "normativas",
        "intent": "REGULATIONS",
        "question": "Puede un alumno cambiar de grupo de practicas una vez comenzado el curso?",
        "ground_truth": (
            "El cambio de grupo de practicas se puede solicitar en el periodo indicado "
            "en el calendario academico, que normalmente coincide con las primeras "
            "dos semanas de clase. El cambio queda sujeto a disponibilidad de plazas "
            "en el grupo de destino y debe tramitarse en Secretaria de Alumnos. "
            "Fuera de ese plazo, los cambios solo se autorizan por causas justificadas "
            "debidamente documentadas."
        ),
    },
    {
        "id": "N06",
        "category": "normativas",
        "intent": "ADMINISTRATIVE",
        "question": "Cual es el plazo para anular la matricula de una asignatura sin penalizacion?",
        "ground_truth": (
            "El plazo de anulacion de matricula sin penalizacion academica se extiende "
            "hasta el ultimo dia del primer mes del semestre correspondiente. "
            "Pasado ese plazo, la anulacion queda registrada como 'No Presentado' "
            "en el expediente del alumno y consume convocatoria. "
            "Para el segundo semestre, el plazo se publica en el calendario academico "
            "oficial de la universidad."
        ),
    },
    # ── PLANES DE ESTUDIO (~5) ───────────────────────────────────────────────
    {
        "id": "P01",
        "category": "planes_estudio",
        "intent": "COURSE_INFO",
        "question": "Cuantos creditos tiene el Grado en Informatica y como se distribuyen?",
        "ground_truth": (
            "El Grado en Ingenieria Informatica tiene 240 creditos ECTS, distribuidos en "
            "4 cursos de 60 creditos cada uno. La distribucion es: formacion basica (60 cr.), "
            "obligatorias de grado (120 cr.), optativas (36 cr.), practicas externas (12 cr.) "
            "y Trabajo Fin de Grado (12 cr.). "
            "Las optativas permiten escoger itinerarios como Ingenieria del Software, "
            "Sistemas Inteligentes o Computacion."
        ),
    },
    {
        "id": "P02",
        "category": "planes_estudio",
        "intent": "COURSE_INFO",
        "question": "Que asignaturas de primer curso son obligatorias en el Grado en Informatica?",
        "ground_truth": (
            "En primer curso del Grado en Informatica las asignaturas obligatorias incluyen "
            "Fundamentos de Programacion, Matematicas I, Matematicas II, Logica y "
            "Matematica Discreta, Fundamentos de Computadores y Estructura de Datos. "
            "Estas asignaturas sientan las bases del pensamiento computacional, "
            "el algebra lineal y el calculo necesarios para los cursos superiores."
        ),
    },
    {
        "id": "P03",
        "category": "planes_estudio",
        "intent": "COURSE_INFO",
        "question": "Tiene el Grado en ADE practicas empresariales obligatorias?",
        "ground_truth": (
            "Si, el Grado en Administracion y Direccion de Empresas (ADE) incluye "
            "practicas externas de 12 creditos ECTS de caracter obligatorio en cuarto curso. "
            "Las practicas se realizan en empresas colaboradoras de la universidad "
            "o en instituciones publicas, y estan tutorizadas por un profesor del grado. "
            "El alumno debe entregar una memoria al finalizar y superar la evaluacion "
            "del tutor academico."
        ),
    },
    {
        "id": "P04",
        "category": "planes_estudio",
        "intent": "ACADEMIC_ORIENTATION",
        "question": "Que optativas existen en el Grado en Informatica para especializarse en IA?",
        "ground_truth": (
            "El itinerario de Sistemas Inteligentes del Grado en Informatica incluye "
            "asignaturas optativas como Aprendizaje Automatico, Procesamiento del Lenguaje "
            "Natural, Vision por Computador, Agentes Inteligentes y Mineria de Datos. "
            "Se recomienda haber superado Fundamentos de Inteligencia Artificial y "
            "Estadistica antes de matricularse en estas optativas de cuarto curso."
        ),
    },
    {
        "id": "P05",
        "category": "planes_estudio",
        "intent": "COURSE_INFO",
        "question": "Puede un alumno de ADE matricularse en asignaturas del Grado en Derecho?",
        "ground_truth": (
            "Los alumnos matriculados en ADE pueden cursar asignaturas del Grado en "
            "Derecho si la universidad oferta el Doble Grado ADE-Derecho o si existe "
            "un convenio de reconocimiento de creditos entre ambas titulaciones. "
            "Fuera de esos supuestos, la matricula en asignaturas de otro grado "
            "requiere autorizacion del centro y puede estar limitada a plazas disponibles. "
            "Se recomienda consultar en Secretaria antes del periodo de matricula."
        ),
    },
    # ── GUIAS DOCENTES (~6) ──────────────────────────────────────────────────
    {
        "id": "G01",
        "category": "guias_docentes",
        "intent": "COURSE_INFO",
        "question": "Como se evalua la asignatura de Fundamentos de Programacion?",
        "ground_truth": (
            "Fundamentos de Programacion se evalua mediante: examenes parciales "
            "que representan el 30% de la nota, practicas de laboratorio entregadas "
            "a lo largo del semestre (30%) y un examen final (40%). "
            "Para aprobar por evaluacion continua es necesario obtener un minimo de 4 "
            "en el examen final y una media ponderada de 5. "
            "Los alumnos que no sigan la evaluacion continua pueden optar solo "
            "al examen final, que en ese caso pesa el 100%."
        ),
    },
    {
        "id": "G02",
        "category": "guias_docentes",
        "intent": "COURSE_INFO",
        "question": "Cuantos creditos tiene la asignatura de Aprendizaje Automatico y que requisitos previos exige?",
        "ground_truth": (
            "Aprendizaje Automatico es una asignatura optativa de 6 creditos ECTS. "
            "Como requisitos previos recomendados figuran haber superado Estadistica, "
            "Algebra Lineal y Fundamentos de Inteligencia Artificial. "
            "La asignatura se imparte en cuarto curso, segundo semestre, y "
            "combina teoria (3 h/semana) con practicas de laboratorio en Python (2 h/semana)."
        ),
    },
    {
        "id": "G03",
        "category": "guias_docentes",
        "intent": "COURSE_INFO",
        "question": "Que metodologia docente utiliza la asignatura de Matematicas I?",
        "ground_truth": (
            "Matematicas I combina clases magistrales de teoria (3 horas semanales) "
            "con sesiones de problemas en grupos reducidos (2 horas semanales). "
            "Se promueve el trabajo autonomo mediante hojas de problemas semanales "
            "con solucionario. La evaluacion incluye un parcial a mitad de semestre "
            "y un examen final. El uso de herramientas de calculo simbolico "
            "(Wolfram Alpha, MATLAB) esta permitido en practicas pero no en examenes."
        ),
    },
    {
        "id": "G04",
        "category": "guias_docentes",
        "intent": "COURSE_INFO",
        "question": "La asignatura de Redes de Computadores tiene practicas de laboratorio?",
        "ground_truth": (
            "Si, Redes de Computadores incluye un bloque de practicas de laboratorio "
            "de 2 horas semanales. En las practicas se trabaja con simuladores de red "
            "(Cisco Packet Tracer) y con equipos reales del laboratorio de networking. "
            "Las practicas son evaluables y representan el 25% de la nota final. "
            "La asistencia a laboratorio es obligatoria; mas de dos faltas "
            "no justificadas implica la perdida del derecho a evaluacion continua."
        ),
    },
    {
        "id": "G05",
        "category": "guias_docentes",
        "intent": "ACADEMIC_ORIENTATION",
        "question": "Que competencias desarrolla la asignatura de Gestion de Proyectos Informaticos?",
        "ground_truth": (
            "Gestion de Proyectos Informaticos desarrolla competencias en planificacion "
            "y estimacion de proyectos software, gestion de riesgos, metodologias agiles "
            "(Scrum, Kanban) y documentacion tecnica. Los alumnos trabajan en equipos "
            "para desarrollar un proyecto completo durante el semestre, utilizando "
            "herramientas como Jira, GitHub y Confluence. La asignatura esta alineada "
            "con el estandar PMBOK y prepara para la certificacion PMP."
        ),
    },
    {
        "id": "G06",
        "category": "guias_docentes",
        "intent": "COURSE_INFO",
        "question": "Cual es el sistema de evaluacion de Trabajo Fin de Grado en Informatica?",
        "ground_truth": (
            "El Trabajo Fin de Grado (TFG) en Informatica se evalua por un tribunal "
            "compuesto por tres profesores del departamento. La nota final pondera: "
            "memoria escrita (40%), defensa oral (40%) y valoracion del tutor (20%). "
            "Para defender el TFG es necesario tener superados al menos 204 creditos "
            "del grado. La defensa es publica y se puede realizar en dos convocatorias "
            "anuales: junio y septiembre."
        ),
    },
    # ── FAQS (~8) ────────────────────────────────────────────────────────────
    {
        "id": "F01",
        "category": "faqs",
        "intent": "ADMINISTRATIVE",
        "question": "Cuando se abre el plazo de matricula para el proximo curso?",
        "ground_truth": (
            "El plazo de matricula para alumnos ya matriculados suele abrirse "
            "en julio, con fechas exactas publicadas en el calendario academico "
            "de cada curso. Los alumnos de nuevo ingreso se matriculan en julio "
            "o septiembre, segun la nota de acceso y el orden de adjudicacion. "
            "El proceso se realiza en linea a traves de la secretaria virtual. "
            "Es imprescindible no tener deudas pendientes con la universidad "
            "para formalizar la matricula."
        ),
    },
    {
        "id": "F02",
        "category": "faqs",
        "intent": "SCHOLARSHIPS",
        "question": "Cuales son los requisitos academicos para solicitar la beca MEC?",
        "ground_truth": (
            "Para solicitar la beca del Ministerio de Educacion (beca MEC) es necesario "
            "cumplir los requisitos de renta familiar (umbrales publicados cada convocatoria) "
            "y los requisitos academicos: superar al menos el 65% de los creditos "
            "matriculados el curso anterior (o el 90% para los componentes de excelencia). "
            "Los alumnos de primer curso de grado estan exentos del requisito academico "
            "previo si no han cursado estudios universitarios antes."
        ),
    },
    {
        "id": "F03",
        "category": "faqs",
        "intent": "PROSPECTIVE_STUDENT",
        "question": "Como puedo acceder al Grado en Informatica desde Bachillerato?",
        "ground_truth": (
            "Para acceder al Grado en Ingenieria Informatica desde Bachillerato es necesario "
            "superar la Prueba de Acceso a la Universidad (PAU o EBAU). "
            "Se recomienda cursar el bachillerato de Ciencias con materias de Matematicas "
            "y Fisica, ya que son las fases especificas que suben la nota de acceso. "
            "La nota de corte oscila habitualmente entre 9 y 11 puntos dependiendo de la "
            "universidad. Algunos centros admiten tambien a traves de FP Superior en "
            "Desarrollo de Aplicaciones Web o Multiplataforma sin necesidad de PAU."
        ),
    },
    {
        "id": "F04",
        "category": "faqs",
        "intent": "ADMINISTRATIVE",
        "question": "Que documentacion necesito para solicitar una beca de movilidad Erasmus?",
        "ground_truth": (
            "Para solicitar una beca Erasmus es necesario presentar: solicitud "
            "formalizada en el portal de la Oficina de Relaciones Internacionales, "
            "expediente academico con nota media, carta de motivacion en el idioma "
            "del pais de destino y certificado del nivel de idioma requerido. "
            "Algunos destinos exigen ademas carta de recomendacion de un profesor. "
            "El plazo de solicitud es normalmente en febrero para estancias del "
            "proximo curso academico."
        ),
    },
    {
        "id": "F05",
        "category": "faqs",
        "intent": "ADMINISTRATIVE",
        "question": "Como puedo solicitar la revision de un examen?",
        "ground_truth": (
            "Para solicitar la revision de un examen el alumno debe presentar "
            "una solicitud escrita al profesor en el plazo indicado en la guia "
            "docente, que suele ser de 5 dias habiles desde la publicacion de "
            "las notas. La revision se realiza en una fecha fijada por el "
            "profesor. Si el alumno no queda satisfecho, puede interponer "
            "reclamacion ante el departamento en un plazo adicional de 10 dias."
        ),
    },
    {
        "id": "F06",
        "category": "faqs",
        "intent": "SCHOLARSHIPS",
        "question": "Existe alguna beca propia de la universidad para alumnos con buen expediente?",
        "ground_truth": (
            "La universidad convoca anualmente becas de excelencia academica para "
            "alumnos de grado con nota media igual o superior a 8.5. Estas becas "
            "cubren parte del importe de la matricula del siguiente curso. "
            "Adicionalmente, existen ayudas de colaboracion con departamentos para "
            "alumnos de tercer y cuarto curso que quieran iniciarse en la investigacion. "
            "La convocatoria se publica en el portal de becas de la universidad "
            "normalmente en junio."
        ),
    },
    {
        "id": "F07",
        "category": "faqs",
        "intent": "ADMINISTRATIVE",
        "question": "Cuanto cuesta el credito ECTS en el Grado en Informatica?",
        "ground_truth": (
            "El precio del credito ECTS en el Grado en Informatica varia segun el "
            "curso de matricula: primera matricula tiene el precio mas reducido, "
            "la segunda matricula implica un incremento del 15% y la tercera "
            "y sucesivas suponen un incremento adicional. Los precios exactos "
            "los fija la Comunidad Autonoma cada curso y se publican en el "
            "decreto de precios publicos universitarios antes del periodo de matricula."
        ),
    },
    {
        "id": "F08",
        "category": "faqs",
        "intent": "PROSPECTIVE_STUDENT",
        "question": "Que es la prueba especifica de acceso y como afecta a la nota de admision?",
        "ground_truth": (
            "La fase especifica de la EBAU permite subir la nota de admision hasta "
            "4 puntos adicionales examinandose de asignaturas elegidas libremente. "
            "Las notas de la fase especifica se multiplican por un coeficiente de "
            "ponderacion (0.1 o 0.2) segun la universidad y el grado al que se accede. "
            "Para Ingenieria Informatica, Matematicas II y Fisica suelen ponderar "
            "con el coeficiente maximo (0.2), por lo que se recomienda presentarse "
            "a estas materias para maximizar la nota de admision."
        ),
    },
    # ── PROCEDIMIENTOS (~5) ──────────────────────────────────────────────────
    {
        "id": "PR01",
        "category": "procedimientos",
        "intent": "ACADEMIC_ORIENTATION",
        "question": "Como funciona el servicio de tutoria academica de la universidad?",
        "ground_truth": (
            "El servicio de tutoria academica asigna un tutor personal a cada alumno "
            "al inicio del grado. Las tutorias pueden ser presenciales o virtuales "
            "y se realizan al menos una vez por semestre. El tutor ayuda en la "
            "planificacion del itinerario de optativas, orienta sobre practicas "
            "externas y TFG, y detecta situaciones de riesgo academico. "
            "Los alumnos con bajo rendimiento son derivados obligatoriamente "
            "a sesiones de tutoria reforzada."
        ),
    },
    {
        "id": "PR02",
        "category": "procedimientos",
        "intent": "ADMINISTRATIVE",
        "question": "Como se tramita el reconocimiento de creditos por experiencia laboral?",
        "ground_truth": (
            "Para solicitar el reconocimiento de creditos por experiencia laboral "
            "el alumno debe presentar en Secretaria: solicitud formal, contrato "
            "de trabajo o certificado de empresa, descripcion de las funciones "
            "desempenadas y cualquier certificacion profesional relevante. "
            "La comision academica del departamento evalua la solicitud y decide "
            "cuantos creditos (y de que tipo) se reconocen. El proceso tarda "
            "normalmente entre 4 y 8 semanas."
        ),
    },
    {
        "id": "PR03",
        "category": "procedimientos",
        "intent": "ACADEMIC_ORIENTATION",
        "question": "Que apoyos ofrece la universidad a alumnos con discapacidad?",
        "ground_truth": (
            "La universidad cuenta con el Servicio de Atencion a la Diversidad (SAD) "
            "que ofrece: adaptaciones metodologicas y de examen (tiempo adicional, "
            "material ampliado, aula separada), apoyo psicopedagogico personalizado, "
            "asesoria para solicitar becas especificas del MECD y eliminacion de "
            "barreras fisicas o digitales. Para acceder al servicio el alumno debe "
            "solicitar informe al SAD antes del inicio de cada semestre, acreditando "
            "la discapacidad reconocida."
        ),
    },
    {
        "id": "PR04",
        "category": "procedimientos",
        "intent": "ADMINISTRATIVE",
        "question": "Como puedo obtener el titulo universitario una vez finalizado el grado?",
        "ground_truth": (
            "Una vez superados todos los creditos y el TFG, el alumno debe solicitar "
            "el titulo en Secretaria aportando: impreso de solicitud, resguardo de "
            "pago de tasas de expedicion y fotocopia del DNI. "
            "El titulo oficial tarda entre 6 y 18 meses en expedirse desde la "
            "solicitud; mientras tanto, la Secretaria expide un certificado de "
            "fin de estudios con validez legal equivalente. "
            "El titulo se puede recoger presencialmente o solicitar su envio."
        ),
    },
    {
        "id": "PR05",
        "category": "procedimientos",
        "intent": "ADMINISTRATIVE",
        "question": "Cuales son los pasos para solicitar una beca de colaboracion con un departamento?",
        "ground_truth": (
            "Para solicitar una beca de colaboracion con un departamento universitario "
            "el alumno debe: contactar con el departamento de interes para conocer "
            "las plazas disponibles, presentar su expediente academico (media minima "
            "habitualmente 7.0), carta de motivacion y una entrevista con el "
            "responsable del departamento. Las becas se financian con fondos propios "
            "del departamento o proyectos de investigacion y no son incompatibles "
            "con la beca MEC. La duracion habitual es de 6 meses prorrogables."
        ),
    },
]


def invoke_graph_sample(graph, sample: Dict[str, Any]) -> Dict[str, Any]:
    """Invoca el grafo con una pregunta y captura respuesta y contextos."""
    from src.graph.state import get_initial_state

    thread_id = f"eval-{sample['id']}-{uuid.uuid4().hex[:8]}"
    state = get_initial_state(
        user_message=sample["question"],
        session_id=thread_id,
        user_id=None,  # preguntas RAG genericas, sin expediente
    )
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(state, config=config)

    answer = result.get("final_response") or ""
    retrieved_docs = result.get("retrieved_docs") or []
    contexts = [doc.get("content", "") for doc in retrieved_docs if doc.get("content")]
    sources = result.get("sources") or []
    intent = result.get("intent") or ""
    confidence = result.get("confidence") or 0.0
    guardrail_triggered = result.get("guardrail_triggered", False)

    return {
        "answer": answer,
        "contexts": contexts,
        "sources": sources,
        "intent": intent,
        "confidence": confidence,
        "guardrail_triggered": guardrail_triggered,
        "num_chunks": len(contexts),
    }


def main():
    import logging as _log
    _log.getLogger("httpx").setLevel(_log.WARNING)
    _log.getLogger("openai").setLevel(_log.WARNING)
    _log.getLogger("azure").setLevel(_log.WARNING)

    logger.info("=== GENERATE EVAL DATASET ===")
    logger.info("Cargando grafo...")

    from src.graph.graph import get_graph
    graph = get_graph()
    logger.info("Grafo cargado OK")

    # Formato RAGAS 0.1.x: columnas question / answer / contexts / ground_truth
    ragas_dataset = []  # lista de dicts para el Dataset de HuggingFace
    meta_dataset = []   # metadatos para eval_dataset_meta.json
    excluded = []

    total = len(CURATED_SAMPLES)
    logger.info("Procesando %d muestras...", total)

    for i, sample in enumerate(CURATED_SAMPLES, 1):
        logger.info("[%d/%d] %s: %s", i, total, sample["id"], sample["question"][:60])

        # Reintentos en caso de error de red
        for attempt in range(1, 4):
            try:
                result = invoke_graph_sample(graph, sample)
                break
            except Exception as exc:
                logger.warning("Intento %d fallido: %s", attempt, exc)
                if attempt == 3:
                    logger.error("Muestra %s descartada tras 3 intentos", sample["id"])
                    result = None
                else:
                    time.sleep(5 * attempt)

        if result is None:
            excluded.append({"id": sample["id"], "reason": "error_after_3_attempts"})
            continue

        # 5.1.3 Salvaguarda guardrail
        if result["guardrail_triggered"]:
            logger.warning(
                "GUARDRAIL disparado inesperadamente en muestra %s (pregunta: %s)",
                sample["id"], sample["question"][:60]
            )
            excluded.append({
                "id": sample["id"],
                "reason": "guardrail_triggered_unexpectedly",
                "question": sample["question"],
            })
            continue

        if not result["answer"]:
            logger.warning("Muestra %s: respuesta vacia, excluyendo", sample["id"])
            excluded.append({"id": sample["id"], "reason": "empty_answer"})
            continue

        # Formato RAGAS 0.1.x
        ragas_dataset.append({
            "question": sample["question"],
            "answer": result["answer"],
            "contexts": result["contexts"] if result["contexts"] else ["No se recuperaron documentos relevantes."],
            "ground_truth": sample["ground_truth"],
        })

        # Metadatos
        meta_dataset.append({
            "id": sample["id"],
            "category": sample["category"],
            "expected_intent": sample["intent"],
            "detected_intent": result["intent"],
            "question": sample["question"],
            "answer": result["answer"],
            "ground_truth": sample["ground_truth"],
            "contexts": result["contexts"],
            "sources": result["sources"],
            "num_chunks": result["num_chunks"],
            "confidence": result["confidence"],
        })

        logger.info(
            "  -> intent=%s, chunks=%d, answer_len=%d",
            result["intent"], result["num_chunks"], len(result["answer"])
        )

        # Pausa para no saturar rate limit
        time.sleep(1)

    # Guardar resultados
    out_dir = ROOT / "tests"
    out_dir.mkdir(exist_ok=True)

    ragas_path = out_dir / "eval_dataset.json"
    meta_path = out_dir / "eval_dataset_meta.json"

    with open(ragas_path, "w", encoding="utf-8") as f:
        json.dump(ragas_dataset, f, ensure_ascii=False, indent=2)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "ragas_version": "0.1.21",
            "api_format": "legacy_0.1.x",
            "dataset_fields": ["question", "answer", "contexts", "ground_truth"],
            "total_curated": total,
            "total_generated": len(ragas_dataset),
            "total_excluded": len(excluded),
            "excluded": excluded,
            "samples": meta_dataset,
        }, f, ensure_ascii=False, indent=2)

    logger.info("=== RESULTADO ===")
    logger.info("Muestras generadas: %d / %d", len(ragas_dataset), total)
    logger.info("Excluidas: %d", len(excluded))
    if excluded:
        for e in excluded:
            logger.info("  - %s: %s", e["id"], e["reason"])
    logger.info("Dataset guardado en: %s", ragas_path)
    logger.info("Metadatos guardados en: %s", meta_path)

    if ragas_dataset:
        logger.info("Ejemplo muestra 0: question='%s'", ragas_dataset[0]["question"][:60])
        logger.info("  answer='%s...'", ragas_dataset[0]["answer"][:100])
        logger.info("  contexts: %d chunks", len(ragas_dataset[0]["contexts"]))

    return len(ragas_dataset), len(excluded)


if __name__ == "__main__":
    main()

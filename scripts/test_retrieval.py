"""Script de evaluación del sistema de recuperación RAG."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
date_str = datetime.now().strftime("%Y%m%d")
log_file = LOG_DIR / f"retrieval_test_{date_str}.txt"

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)

from src.tools.azure_search import search_knowledge_base

QUERIES = [
    {
        "id": "R01",
        "intent": "REGULATIONS",
        "query": "¿Cuántas convocatorias tiene un alumno para superar una asignatura?",
        "expected_source": "reglamento_academico",
    },
    {
        "id": "R02",
        "intent": "ACADEMIC_ORIENTATION",
        "query": "¿Qué asignaturas son obligatorias en el segundo curso de Informática?",
        "expected_source": "grado_informatica",
    },
    {
        "id": "R03",
        "intent": "SCHOLARSHIPS",
        "query": "¿Cuál es la nota media mínima para solicitar la beca MEC?",
        "expected_source": "faq_becas",
    },
    {
        "id": "R04",
        "intent": "ADMINISTRATIVE",
        "query": "¿Hasta cuándo puedo anular la matrícula de una asignatura?",
        "expected_source": "politica_evaluacion",
    },
    {
        "id": "R05",
        "intent": "COURSE_INFO",
        "query": "¿Cuáles son los criterios de evaluación de Bases de Datos?",
        "expected_source": "guia_bases_datos",
    },
    {
        "id": "R06",
        "intent": "PROSPECTIVE_STUDENT",
        "query": "¿Cuál es la nota de corte para acceder al Grado en Informática?",
        "expected_source": "faq_admision",
    },
    {
        "id": "R07",
        "intent": "REGULATIONS",
        "query": "¿Qué ocurre si un alumno no supera el 50% de los créditos en primero?",
        "expected_source": "normativa_permanencia",
    },
    {
        "id": "R08",
        "intent": "ADMINISTRATIVE",
        "query": "¿Cómo puedo pedir cita con el servicio de orientación académica?",
        "expected_source": "guia_orientacion_academica",
    },
    {
        "id": "R09",
        "intent": "COURSE_INFO",
        "query": "¿Qué prerrequisitos tiene la asignatura de Inteligencia Artificial?",
        "expected_source": "grado_informatica",
    },
    {
        "id": "R10",
        "intent": "REGULATIONS",
        "query": "¿En qué plazo puedo reclamar una calificación tras la publicación?",
        "expected_source": "reglamento_academico",
    },
]


def run_evaluation() -> Dict:
    """Ejecuta todas las queries de evaluación y devuelve las métricas."""
    results_log: List[str] = []
    pass_count = 0
    all_scores: List[float] = []

    for q in QUERIES:
        qid = q["id"]
        query_text = q["query"]
        expected = q["expected_source"]

        results = search_knowledge_base(query_text, top_k=5)

        sources_found = [r["source_file"].replace(".md", "") for r in results]
        passed = expected in sources_found
        if passed:
            pass_count += 1

        top3_scores = [r["relevance_score"] for r in results[:3]]
        if top3_scores:
            all_scores.extend(top3_scores)

        status = "PASS" if passed else "FAIL"
        line = f"[{qid}] {status} — expected: {expected}"
        results_log.append(line)
        print(f"\n{line}")
        print(f"  Query: {query_text}")
        for i, r in enumerate(results[:3]):
            snippet = r["content"][:100].replace("\n", " ")
            print(f"  [{i+1}] score={r['relevance_score']} src={r['source_file']} | {snippet}...")
            results_log.append(f"    [{i+1}] score={r['relevance_score']} src={r['source_file']} | {snippet}...")

    avg_score = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0
    min_score = round(min(all_scores), 4) if all_scores else 0.0
    fail_count = len(QUERIES) - pass_count
    passed_criterion = pass_count >= 8

    summary = (
        "\n══════════════════════════════════════\n"
        "  RESULTADO TEST DE RECUPERACIÓN\n"
        "══════════════════════════════════════\n"
        f"  Queries evaluadas:  10\n"
        f"  PASS (fuente encontrada): {pass_count}/10\n"
        f"  FAIL (fuente no encontrada): {fail_count}/10\n"
        f"  Score medio:        {avg_score}\n"
        f"  Score mínimo:       {min_score}\n"
        "══════════════════════════════════════\n"
        "  CRITERIO DE ÉXITO: ≥ 8/10 PASS\n"
        f"  RESULTADO: {'SUPERADO' if passed_criterion else 'NO SUPERADO'}\n"
        "══════════════════════════════════════"
    )
    print(summary)

    # Write full report to log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n=== TEST DE RECUPERACIÓN ===\n")
        f.write(f"Fecha: {datetime.now().isoformat()}\n\n")
        for line in results_log:
            f.write(line + "\n")
        f.write(summary + "\n")

    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "avg_score": avg_score,
        "min_score": min_score,
        "passed": passed_criterion,
    }


if __name__ == "__main__":
    metrics = run_evaluation()
    sys.exit(0 if metrics["passed"] else 1)

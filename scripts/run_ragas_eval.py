"""Fase 5-bis: Re-evaluacion RAGAS con evaluador corregido (v2).

Cambios respecto a la evaluacion v1 (RAGAS 0.1.21):
  1. VERSION RAGAS: actualizada a 0.2.6, instalada sin cambiar dependencias
     del proyecto (langchain 0.2.17 / langchain-openai 0.1.25 sin tocar).
  2. FORMATO DATASET: se usa column_map para mapear los campos legacy
     (question/answer/contexts/ground_truth) a los nombres internos de
     RAGAS 0.2.x (user_input/response/retrieved_contexts/reference).
     En 0.1.x este desajuste causaba que algunas metricas no encontrasen
     los datos y devolvieran NaN/0.0.
  3. VARIABLE DE ENTORNO: se lee AZURE_OPENAI_DEPLOYMENT_NAME (nombre
     correcto en .env) con fallback a AZURE_OPENAI_DEPLOYMENT.
  4. CONCURRENCIA: max_workers reducido de 4 a 2 para evitar errores 429
     y que fallen muestras individualmente.
  5. GROUND_TRUTH CORREGIDOS (ver GT_CORRECTIONS abajo): 5 ground_truths
     contenian afirmaciones factuales incorrectas respecto al corpus, lo
     que deprimia context_recall artificialmente. Correcciones documentadas.

Outputs:
  tests/ragas_report_v2.json
  tests/ragas_summary_v2.txt

Uso:
    python scripts/run_ragas_eval.py [--single-test]
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

for _noisy in ("httpx", "openai", "azure", "httpcore", "langchain"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

# ── Correcciones de ground_truth documentadas ────────────────────────────────
# Cada entrada: indice → {"original": "...", "corrected": "...", "razon": "..."}
# Solo se corrigen afirmaciones que contradicen directamente el corpus.
# PROHIBIDO reescribir para copiar la respuesta del sistema.

GT_CORRECTIONS = {
    0: {
        "original": (
            "Los alumnos disponen de un maximo de 4 convocatorias ordinarias para "
            "superar cada asignatura. Existe ademas la posibilidad de solicitar una "
            "convocatoria extraordinaria al Consejo de Departamento si se han agotado "
            "las ordinarias, sumando un total de hasta 6 convocatorias en situaciones "
            "excepcionales."
        ),
        "corrected": (
            "Los alumnos disponen de un maximo de 4 convocatorias ordinarias para "
            "superar cada asignatura. Si se agotan sin superarla, el alumno puede "
            "solicitar una quinta convocatoria extraordinaria al Consejo Academico. "
            "La solicitud debe presentarse por escrito antes del inicio del periodo "
            "de matricula del siguiente curso academico. El Consejo resuelve en "
            "15 dias habiles y su concesion es discrecional."
        ),
        "razon": (
            "Corpus dice 'Consejo Academico', no 'Consejo de Departamento'. "
            "Corpus dice 5 convocatorias maximas (4 ordinarias + 1 extraordinaria), "
            "no 6."
        ),
    },
    3: {
        "original": (
            "La normativa de permanencia establece los requisitos minimos que los "
            "alumnos deben cumplir para continuar en el grado. Se aplica cuando el "
            "rendimiento academico es muy bajo: si en los dos primeros cursos el "
            "alumno no supera al menos 12 creditos por curso, puede ser derivado a "
            "tutoria academica obligatoria. Esta normativa busca detectar dificultades "
            "a tiempo y ofrecer orientacion antes de que sea necesaria la baja."
        ),
        "corrected": (
            "La normativa de permanencia establece los requisitos minimos que los "
            "alumnos deben cumplir para continuar en el grado. El alumno debe superar "
            "al menos el 50% de los creditos matriculados al finalizar el primer ano "
            "academico completo, el 60% en el segundo ano y el 65% a partir del tercer "
            "ano. Si no se alcanzan esos minimos, la Secretaria Academica notifica al "
            "alumno y se convoca una tutoria obligatoria con el Servicio de Orientacion "
            "Academica en 10 dias habiles."
        ),
        "razon": (
            "El corpus dice 50%/60%/65% segun el ano, no '12 creditos por curso'. "
            "Los minimos reales son 27/33/39 ECTS sobre 60 ECTS de matricula estandar."
        ),
    },
    5: {
        "original": (
            "El plazo de anulacion de matricula sin penalizacion academica se extiende "
            "hasta el ultimo dia del primer mes del semestre correspondiente. Pasado "
            "ese plazo, la anulacion queda registrada como 'No Presentado' en el "
            "expediente del alumno y consume convocatoria. Para el segundo semestre, "
            "el plazo se publica en el calendario academico oficial de la universidad."
        ),
        "corrected": (
            "El plazo para anular la matricula de una asignatura sin que conste en el "
            "expediente como convocatoria consumida es hasta el final de la sexta semana "
            "lectiva del semestre correspondiente. La solicitud debe presentarse en la "
            "Secretaria Academica mediante el formulario oficial, indicando el motivo. "
            "La anulacion parcial no puede dejar la matricula por debajo de 36 ECTS "
            "anuales."
        ),
        "razon": (
            "Corpus dice 'sexta semana lectiva', no 'primer mes'. "
            "Corpus dice explicitamente que la anulacion NO consume convocatoria "
            "(Art. 3.1: 'sin que ello conste en el expediente como convocatoria "
            "consumida'). El GT original afirmaba lo contrario."
        ),
    },
    6: {
        "original": (
            "El Grado en Ingenieria Informatica tiene 240 creditos ECTS, distribuidos "
            "en 4 cursos de 60 creditos cada uno. La distribucion es: formacion basica "
            "(60 cr.), obligatorias de grado (120 cr.), optativas (36 cr.), practicas "
            "externas (12 cr.) y Trabajo Fin de Grado (12 cr.). Las optativas permiten "
            "escoger itinerarios como Ingenieria del Software, Sistemas Inteligentes o "
            "Computacion."
        ),
        "corrected": (
            "El Grado en Ingenieria Informatica tiene 240 creditos ECTS distribuidos en "
            "4 cursos de 60 creditos cada uno. Segun el resumen del plan de estudios, "
            "la distribucion es: asignaturas obligatorias (186 ECTS), asignaturas "
            "optativas (42 ECTS) y Trabajo de Fin de Grado (12 ECTS). Las optativas "
            "permiten escoger entre distintos itinerarios de especializacion disponibles "
            "en tercer y cuarto curso."
        ),
        "razon": (
            "Corpus dice 42 ECTS de optativas, no 36. "
            "Corpus dice 186 ECTS obligatorias en total; el desglose "
            "'formacion basica + obligatorias de grado + practicas externas' del GT "
            "no aparece en el corpus y los numeros no cuadran."
        ),
    },
    21: {
        "original": (
            "Para solicitar la revision de un examen el alumno debe presentar una "
            "solicitud escrita al profesor en el plazo indicado en la guia docente, "
            "que suele ser de 5 dias habiles desde la publicacion de las notas. La "
            "revision se realiza en una fecha fijada por el profesor. Si el alumno no "
            "queda satisfecho, puede interponer reclamacion ante el departamento en un "
            "plazo adicional de 10 dias."
        ),
        "corrected": (
            "Para solicitar la revision de un examen el alumno debe enviar una "
            "solicitud escrita al profesor responsable (con copia a la Coordinacion "
            "del Grado) en un plazo de 5 dias habiles desde la publicacion de las "
            "calificaciones provisionales. El profesor fijara fecha de revision en "
            "los 5 dias habiles siguientes. Si el alumno no esta conforme tras la "
            "revision, puede interponer reclamacion formal ante la Comision de "
            "Evaluacion del Grado en un plazo adicional de 5 dias habiles."
        ),
        "razon": (
            "Corpus dice 5 dias habiles para la reclamacion (no 10). "
            "El organo receptor es 'Comision de Evaluacion del Grado' (no 'el departamento')."
        ),
    },
}


def apply_gt_corrections(data: list) -> list:
    """Aplica las correcciones documentadas a los ground_truth del dataset."""
    corrected = []
    for i, sample in enumerate(data):
        s = dict(sample)
        if i in GT_CORRECTIONS:
            corr = GT_CORRECTIONS[i]
            orig = s.get("ground_truth", "")
            if orig.strip() == corr["original"].strip():
                s["ground_truth"] = corr["corrected"]
                logger.info(
                    "GT corregido [%d]: %s", i, corr["razon"]
                )
            else:
                logger.warning(
                    "GT [%d] no coincide con original esperado — se aplica la "
                    "correccion de todas formas (texto puede haber cambiado).",
                    i,
                )
                s["ground_truth"] = corr["corrected"]
        corrected.append(s)
    return corrected


def build_azure_llm():
    """AzureChatOpenAI envuelto para RAGAS 0.2.x."""
    from langchain_openai import AzureChatOpenAI
    from ragas.llms import LangchainLLMWrapper

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    key = os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    # .env usa AZURE_OPENAI_DEPLOYMENT_NAME; fallback al nombre antiguo
    deployment = (
        os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        or "gpt-4o"
    )

    if not endpoint or not key:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT o AZURE_OPENAI_API_KEY no configurados en .env"
        )

    logger.info("LLM juez: deployment=%s endpoint=%s", deployment, endpoint[:40])

    llm = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version=api_version,
        azure_deployment=deployment,
        temperature=0.0,
        request_timeout=60,
        max_retries=3,
    )
    return LangchainLLMWrapper(llm)


def build_azure_embeddings():
    """AzureOpenAIEmbeddings envuelto para RAGAS 0.2.x."""
    from langchain_openai import AzureOpenAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    key = os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    emb_deployment = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"
    )

    logger.info("Embeddings: deployment=%s", emb_deployment)

    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=endpoint,
        api_key=key,
        api_version=api_version,
        azure_deployment=emb_deployment,
    )
    return LangchainEmbeddingsWrapper(embeddings)


def load_dataset_hf(path: Path, apply_corrections: bool = True):
    """Carga eval_dataset.json como HuggingFace Dataset para RAGAS."""
    from datasets import Dataset

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if apply_corrections:
        data = apply_gt_corrections(data)

    required = {"question", "answer", "contexts", "ground_truth"}
    for i, sample in enumerate(data):
        missing = required - set(sample.keys())
        if missing:
            raise ValueError(f"Muestra {i} falta campos: {missing}")

    return Dataset.from_list(data)


def run_single_test(ragas_llm, ragas_embeddings) -> bool:
    """Ejecuta la evaluacion en 1 muestra para validar el cableado.

    Returns True si todas las metricas devolvieron valores validos (no NaN/0.0).
    """
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from ragas.run_config import RunConfig

    logger.info("=== VALIDACION CON 1 MUESTRA ===")

    # Muestra representativa con contexto y ground_truth correctos
    test_sample = {
        "question": "Cuantas convocatorias tiene un alumno para superar una asignatura?",
        "answer": (
            "Un alumno dispone de un maximo de 4 convocatorias ordinarias para "
            "superar cada asignatura. Si agota esas 4 convocatorias sin exito, "
            "puede solicitar una quinta convocatoria extraordinaria al Consejo Academico."
        ),
        "contexts": [
            "Cada asignatura dispone de un maximo de cuatro convocatorias ordinarias "
            "para su superacion a lo largo de la vida academica del alumno en la "
            "Universidad Demo. Agotadas las cuatro convocatorias ordinarias sin superar "
            "la asignatura, el alumno podra solicitar una quinta convocatoria "
            "extraordinaria al Consejo Academico. Esta solicitud debera presentarse "
            "por escrito antes del inicio del periodo de matricula del siguiente "
            "curso academico."
        ],
        "ground_truth": (
            "Los alumnos disponen de 4 convocatorias ordinarias para superar cada "
            "asignatura. Si se agotan, pueden solicitar una quinta convocatoria "
            "extraordinaria al Consejo Academico."
        ),
    }

    test_ds = Dataset.from_list([test_sample])
    col_map = {
        "user_input": "question",
        "response": "answer",
        "retrieved_contexts": "contexts",
        "reference": "ground_truth",
    }

    rc = RunConfig(timeout=120, max_retries=3, max_wait=60, max_workers=1)

    try:
        result = evaluate(
            dataset=test_ds,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            run_config=rc,
            column_map=col_map,
            raise_exceptions=False,
        )
    except Exception as exc:
        logger.error("Error en validacion: %s", exc)
        return False

    df = result.to_pandas()
    logger.info("Resultado validacion (1 muestra):")
    for col in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        if col in df.columns:
            val = df[col].iloc[0]
            ok = val is not None and val == val and val > 0.0
            logger.info("  %-25s = %s  %s", col, val, "OK" if ok else "FALLO (NaN/0.0)")
        else:
            logger.warning("  %-25s = columna ausente", col)

    metrics_ok = all(
        col in df.columns
        and df[col].iloc[0] is not None
        and df[col].iloc[0] == df[col].iloc[0]  # not NaN
        and df[col].iloc[0] > 0.0
        for col in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    )

    if metrics_ok:
        logger.info("Validacion SUPERADA — el cableado funciona correctamente.")
    else:
        logger.error(
            "Validacion FALLIDA — alguna metrica devolvio NaN/0.0. "
            "Revisar cableado antes de continuar."
        )

    return metrics_ok


def estimate_calls(n_samples: int) -> int:
    """Estima llamadas LLM para las 4 metricas."""
    return n_samples * 5  # ~5 llamadas/muestra


def run_evaluation(skip_validation: bool = False):
    import ragas
    logger.info("=== RAGAS RE-EVALUATION v2 START ===")
    logger.info("RAGAS version: %s", ragas.__version__)
    logger.info("Fecha: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("Correcciones GT aplicadas: %d muestras", len(GT_CORRECTIONS))

    dataset_path = ROOT / "tests" / "eval_dataset.json"
    if not dataset_path.exists():
        logger.error("No se encontro eval_dataset.json.")
        sys.exit(1)

    # Construir LLM y embeddings
    logger.info("Configurando Azure OpenAI como juez...")
    try:
        ragas_llm = build_azure_llm()
        ragas_embeddings = build_azure_embeddings()
        logger.info("Azure LLM y embeddings configurados OK")
    except Exception as exc:
        logger.error("Error configurando Azure: %s", exc)
        raise

    # Validacion con 1 muestra
    if not skip_validation:
        ok = run_single_test(ragas_llm, ragas_embeddings)
        if not ok:
            logger.error(
                "ABORT: validacion de 1 muestra fallo. "
                "Revisar configuracion antes de lanzar el lote completo."
            )
            sys.exit(2)
    else:
        logger.warning("Validacion de 1 muestra omitida (skip_validation=True)")

    # Cargar dataset completo con correcciones
    logger.info("Cargando dataset con correcciones de ground_truth...")
    dataset = load_dataset_hf(dataset_path, apply_corrections=True)
    n_samples = len(dataset)
    logger.info("Dataset cargado: %d muestras", n_samples)
    logger.info("Llamadas LLM estimadas: ~%d", estimate_calls(n_samples))

    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from ragas.run_config import RunConfig

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    # column_map: mapea nombres RAGAS 0.2.x → columnas del dataset legacy
    col_map = {
        "user_input": "question",
        "response": "answer",
        "retrieved_contexts": "contexts",
        "reference": "ground_truth",
    }

    # Concurrencia reducida para evitar 429s
    run_config = RunConfig(
        timeout=180,
        max_retries=5,
        max_wait=120,
        max_workers=2,
    )

    logger.info("Iniciando evaluacion completa con RAGAS %s...", ragas.__version__)
    logger.info(
        "Metricas: faithfulness, answer_relevancy, context_precision, context_recall"
    )
    logger.info(
        "Config: max_workers=%d, max_retries=%d, timeout=%d",
        run_config.max_workers,
        run_config.max_retries,
        run_config.timeout,
    )

    start_time = time.time()

    try:
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            run_config=run_config,
            column_map=col_map,
            raise_exceptions=False,
        )
    except Exception as exc:
        logger.error("Error durante evaluacion: %s", exc)
        raise

    elapsed = time.time() - start_time
    logger.info("Evaluacion completada en %.1f segundos", elapsed)

    result_df = result.to_pandas()
    scores_per_sample = result_df.to_dict(orient="records")

    metric_means = {}
    for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        if m in result_df.columns:
            metric_means[m] = float(result_df[m].mean())
        else:
            metric_means[m] = None

    # Veredictos contra objetivos de la memoria
    thresholds = {
        "faithfulness": 0.85,
        "answer_relevancy": 0.80,
        "context_precision": 0.75,
        "context_recall": 0.70,
    }
    verdicts = {}
    for m, thr in thresholds.items():
        v = metric_means.get(m)
        if v is not None:
            verdicts[m] = "PASS" if v >= thr else f"FAIL (objetivo {thr:.2f})"
        else:
            verdicts[m] = "N/A"

    # 5 peores por faithfulness
    # RAGAS 0.2.x con column_map: la pregunta puede estar en 'user_input' o 'question'
    worst5 = []
    if "faithfulness" in result_df.columns:
        q_col = "user_input" if "user_input" in result_df.columns else "question"
        worst5 = (
            result_df.nsmallest(5, "faithfulness")[[q_col, "faithfulness"]]
            .rename(columns={q_col: "question"})
            .to_dict(orient="records")
        )

    # Metadatos de la evaluacion
    deployment = (
        os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        or "gpt-4o"
    )
    import ragas as ragas_module
    report = {
        "metadata": {
            "ragas_version": ragas_module.__version__,
            "api_format": "ragas_0.2.x_column_map",
            "evaluation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "n_samples": n_samples,
            "llm_judge": deployment,
            "elapsed_seconds": round(elapsed, 1),
            "config_changes_vs_v1": [
                "RAGAS version: 0.1.21 -> 0.2.6",
                "column_map aplicado: question/answer/contexts/ground_truth "
                "-> user_input/response/retrieved_contexts/reference",
                "AZURE_OPENAI_DEPLOYMENT_NAME (var correcta del .env) usada como LLM juez",
                "max_workers: 4 -> 2 (menos errores 429)",
                "GT correcciones en indices [0, 3, 5, 6, 21] (ver gt_corrections_applied)",
            ],
            "gt_corrections_applied": {
                str(i): {"razon": c["razon"]}
                for i, c in GT_CORRECTIONS.items()
            },
        },
        "metric_means": metric_means,
        "thresholds": thresholds,
        "verdicts": verdicts,
        "scores_per_sample": scores_per_sample,
        "worst5_faithfulness": worst5,
    }

    # Guardar ragas_report_v2.json
    report_path = ROOT / "tests" / "ragas_report_v2.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Report v2 guardado en %s", report_path)

    # Guardar ragas_summary_v2.txt
    _write_summary_v2(report, ROOT / "tests" / "ragas_summary_v2.txt")

    # Log final
    logger.info("=== RESULTADO RAGAS v2 ===")
    for m, v in metric_means.items():
        val_str = f"{v:.4f}" if v is not None else "N/A"
        thr = thresholds.get(m, 0)
        logger.info("  %-25s = %s  (objetivo %.2f → %s)", m, val_str, thr, verdicts[m])

    return report


def _write_summary_v2(report: dict, path: Path):
    """Escribe ragas_summary_v2.txt con tabla legible y comparativa v1."""
    v1 = {
        "faithfulness": 0.5118,
        "answer_relevancy": 0.4755,
        "context_precision": 0.3756,
        "context_recall": 0.2730,
    }

    meta = report["metadata"]
    means = report["metric_means"]
    verdicts = report["verdicts"]
    thresholds = report["thresholds"]

    with open(path, "w", encoding="utf-8") as f:
        f.write("=" * 65 + "\n")
        f.write("RESUMEN EVALUACION RAGAS v2 — Asistente Universitario TFG\n")
        f.write("=" * 65 + "\n\n")
        f.write(f"Fecha:          {meta['evaluation_date']}\n")
        f.write(f"RAGAS version:  {meta['ragas_version']}\n")
        f.write(f"Muestras:       {meta['n_samples']}\n")
        f.write(f"LLM juez:       {meta['llm_judge']}\n")
        f.write(f"Tiempo:         {meta['elapsed_seconds']} s\n")
        f.write(f"GT corregidos:  indices {list(GT_CORRECTIONS.keys())}\n\n")

        f.write("-" * 65 + "\n")
        f.write("CAMBIOS RESPECTO A v1\n")
        f.write("-" * 65 + "\n")
        for c in meta["config_changes_vs_v1"]:
            f.write(f"  • {c}\n")
        f.write("\n")

        f.write("-" * 65 + "\n")
        f.write(
            f"{'METRICA':<26} {'v1 (0.1.21)':>11} {'v2 (0.2.6)':>11} "
            f"{'Delta':>7}  {'Objetivo':>8}  {'Veredicto'}\n"
        )
        f.write("-" * 65 + "\n")
        for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            v2_val = means.get(m)
            v1_val = v1.get(m)
            v2_str = f"{v2_val:.4f}" if v2_val is not None else "   N/A"
            v1_str = f"{v1_val:.4f}" if v1_val is not None else "   N/A"
            delta_str = (
                f"{v2_val - v1_val:+.4f}"
                if v2_val is not None and v1_val is not None
                else "   N/A"
            )
            thr = thresholds.get(m, 0)
            verd = verdicts.get(m, "N/A")
            f.write(
                f"  {m:<24} {v1_str:>11} {v2_str:>11} "
                f"{delta_str:>7}  {thr:>8.2f}  {verd}\n"
            )
        f.write("\n")

        f.write("-" * 65 + "\n")
        f.write("CORRECCIONES DE GROUND_TRUTH APLICADAS\n")
        f.write("-" * 65 + "\n")
        for i, c in GT_CORRECTIONS.items():
            f.write(f"  [{i:02d}] {c['razon']}\n")
        f.write("\n")

        worst5 = report.get("worst5_faithfulness", [])
        if worst5:
            f.write("-" * 65 + "\n")
            f.write("5 PEORES MUESTRAS (faithfulness)\n")
            f.write("-" * 65 + "\n")
            for w in worst5:
                q = str(w.get("question", ""))[:58]
                sc = w.get("faithfulness")
                f.write(f"  [{sc:.3f}] {q}\n")
            f.write("\n")

    logger.info("Summary v2 guardado en %s", path)


if __name__ == "__main__":
    skip_val = "--skip-validation" in sys.argv
    single_test_only = "--single-test" in sys.argv

    if single_test_only:
        logger.info("Modo: solo test de 1 muestra")
        ragas_llm = build_azure_llm()
        ragas_embeddings = build_azure_embeddings()
        ok = run_single_test(ragas_llm, ragas_embeddings)
        sys.exit(0 if ok else 1)

    run_evaluation(skip_validation=skip_val)

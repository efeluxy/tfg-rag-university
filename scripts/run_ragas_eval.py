"""Fase 5, Bloque 5.2: Evaluacion RAGAS del sistema RAG universitario.

Carga tests/eval_dataset.json, construye el dataset RAGAS (API 0.1.x),
configura Azure OpenAI como juez y calcula las 4 metricas:
faithfulness, answer_relevancy, context_precision, context_recall.

Uso:
    python scripts/run_ragas_eval.py
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

# Silenciar loggers ruidosos
for _noisy in ("httpx", "openai", "azure", "httpcore", "langchain"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


def estimate_calls(n_samples: int) -> int:
    """Estima llamadas LLM necesarias para las 4 metricas."""
    # faithfulness: ~2 calls/sample
    # answer_relevancy: ~1 call/sample (embedding)
    # context_precision: ~1 call/sample
    # context_recall: ~1 call/sample
    return n_samples * 5


def build_azure_llm():
    """Construye AzureChatOpenAI wrapped para RAGAS reutilizando azure_config.py vars."""
    from langchain_openai import AzureChatOpenAI
    from ragas.llms import LangchainLLMWrapper

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    key = os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if not endpoint or not key:
        raise ValueError("AZURE_OPENAI_ENDPOINT o AZURE_OPENAI_API_KEY no configurados en .env")

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
    """Construye AzureOpenAIEmbeddings wrapped para RAGAS reutilizando azure_config.py vars."""
    from langchain_openai import AzureOpenAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    key = os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    emb_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")

    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=endpoint,
        api_key=key,
        api_version=api_version,
        azure_deployment=emb_deployment,
    )
    return LangchainEmbeddingsWrapper(embeddings)


def load_dataset(path: Path):
    """Carga eval_dataset.json y construye un HuggingFace Dataset para RAGAS 0.1.x."""
    from datasets import Dataset

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validar campos minimos
    required = {"question", "answer", "contexts", "ground_truth"}
    for i, sample in enumerate(data):
        missing = required - set(sample.keys())
        if missing:
            raise ValueError(f"Muestra {i} falta campos: {missing}")

    return Dataset.from_list(data)


def run_evaluation():
    logger.info("=== RAGAS EVALUATION START ===")
    logger.info("Fecha: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    dataset_path = ROOT / "tests" / "eval_dataset.json"
    if not dataset_path.exists():
        logger.error("No se encontro eval_dataset.json. Ejecutar generate_eval_dataset.py primero.")
        sys.exit(1)

    # Cargar dataset
    logger.info("Cargando dataset desde %s ...", dataset_path)
    dataset = load_dataset(dataset_path)
    n_samples = len(dataset)
    logger.info("Dataset cargado: %d muestras", n_samples)

    # Estimar coste
    estimated_calls = estimate_calls(n_samples)
    logger.info("Llamadas LLM estimadas: ~%d (para las 4 metricas)", estimated_calls)

    # Construir LLM y embeddings con Azure
    logger.info("Configurando Azure OpenAI como juez RAGAS...")
    try:
        ragas_llm = build_azure_llm()
        ragas_embeddings = build_azure_embeddings()
        logger.info("Azure LLM y embeddings configurados OK")
    except Exception as exc:
        logger.error("Error configurando Azure: %s", exc)
        raise

    # Importar metricas RAGAS 0.1.x
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from ragas import evaluate
    from ragas.run_config import RunConfig

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    # Configurar run: concurrencia moderada + reintentos con backoff
    run_config = RunConfig(
        timeout=180,          # segundos por llamada
        max_retries=5,        # reintentos por llamada
        max_wait=120,         # espera maxima entre reintentos (429 → backoff)
        max_workers=4,        # concurrencia moderada para no saturar
    )

    logger.info("Iniciando evaluacion con RAGAS 0.1.21...")
    logger.info("Metricas: faithfulness, answer_relevancy, context_precision, context_recall")
    logger.info("Concurrencia: %d workers, max_retries=%d", run_config.max_workers, run_config.max_retries)

    start_time = time.time()

    try:
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            run_config=run_config,
        )
    except Exception as exc:
        logger.error("Error durante evaluacion: %s", exc)
        raise

    elapsed = time.time() - start_time
    logger.info("Evaluacion completada en %.1f segundos", elapsed)

    # Extraer scores
    result_df = result.to_pandas()
    scores_per_sample = result_df.to_dict(orient="records")

    metric_means = {
        "faithfulness": float(result_df["faithfulness"].mean()) if "faithfulness" in result_df else None,
        "answer_relevancy": float(result_df["answer_relevancy"].mean()) if "answer_relevancy" in result_df else None,
        "context_precision": float(result_df["context_precision"].mean()) if "context_precision" in result_df else None,
        "context_recall": float(result_df["context_recall"].mean()) if "context_recall" in result_df else None,
    }

    # Veredicto faithfulness
    faith_score = metric_means.get("faithfulness")
    if faith_score is not None:
        faith_verdict = "PASS" if faith_score > 0.80 else "FAIL (< 0.80)"
    else:
        faith_verdict = "N/A (error de calculo)"

    # 5 peores por faithfulness (para analisis si < 0.80)
    if "faithfulness" in result_df:
        worst5 = result_df.nsmallest(5, "faithfulness")[["question", "faithfulness"]].to_dict(orient="records")
    else:
        worst5 = []

    # Construir report
    report = {
        "metadata": {
            "ragas_version": "0.1.21",
            "api_format": "legacy_0.1.x",
            "evaluation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "n_samples": n_samples,
            "llm_judge": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            "elapsed_seconds": round(elapsed, 1),
        },
        "metric_means": metric_means,
        "faithfulness_verdict": faith_verdict,
        "scores_per_sample": scores_per_sample,
        "worst5_faithfulness": worst5,
    }

    # Guardar ragas_report.json
    report_path = ROOT / "tests" / "ragas_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Report guardado en %s", report_path)

    # Guardar ragas_summary.txt
    summary_path = ROOT / "tests" / "ragas_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("RESUMEN EVALUACION RAGAS — Asistente Universitario TFG\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Fecha:          {report['metadata']['evaluation_date']}\n")
        f.write(f"RAGAS version:  {report['metadata']['ragas_version']}\n")
        f.write(f"Muestras:       {n_samples}\n")
        f.write(f"LLM juez:       {report['metadata']['llm_judge']}\n")
        f.write(f"Tiempo:         {report['metadata']['elapsed_seconds']} s\n\n")
        f.write("-" * 60 + "\n")
        f.write("METRICAS (media sobre 30 muestras)\n")
        f.write("-" * 60 + "\n")
        for metric, value in metric_means.items():
            val_str = f"{value:.4f}" if value is not None else "N/A"
            f.write(f"  {metric:<25} {val_str}\n")
        f.write("\n")
        f.write("-" * 60 + "\n")
        f.write(f"VEREDICTO FAITHFULNESS > 0.80: {faith_verdict}\n")
        f.write("-" * 60 + "\n\n")

        if faith_score is not None and faith_score <= 0.80:
            f.write("ANALISIS (faithfulness <= 0.80):\n")
            f.write("  Causa probable: G02 — respuestas correctas pero poco ancladas\n")
            f.write("  en chunks dispersos del corpus. El generador sintetiza informacion\n")
            f.write("  de varias fuentes pero no siempre cita literalmente el chunk.\n\n")
            f.write("5 PEORES MUESTRAS (faithfulness):\n")
            for w in worst5:
                q = str(w.get("question", ""))[:60]
                sc = w.get("faithfulness")
                f.write(f"  - [{sc:.3f}] {q}\n")
            f.write("\nPROPUESTAS DE MEJORA:\n")
            f.write("  1. Enriquecer corpus con documentos mas especificos y detallados.\n")
            f.write("  2. Revisar chunking: reducir overlap para evitar fragmentacion.\n")
            f.write("  3. Ajustar prompt del generador para exigir mas anclaje en chunks.\n")
            f.write("  4. Aumentar top_k de recuperacion para dar mas contexto al LLM.\n")

    logger.info("Summary guardado en %s", summary_path)

    # Log final
    logger.info("=== RESULTADO RAGAS ===")
    for metric, value in metric_means.items():
        val_str = f"{value:.4f}" if value is not None else "N/A"
        logger.info("  %-25s = %s", metric, val_str)
    logger.info("VEREDICTO faithfulness > 0.80: %s", faith_verdict)

    return report


if __name__ == "__main__":
    run_evaluation()

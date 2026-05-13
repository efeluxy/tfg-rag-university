"""Indexa todos los archivos .md del corpus en Azure AI Search con embeddings."""

import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
date_str = datetime.now().strftime("%Y%m%d")
log_file_main = LOG_DIR / f"fase2_{date_str}.txt"
log_file_indexing = LOG_DIR / f"indexing_{date_str}.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file_main, encoding="utf-8"),
        logging.FileHandler(log_file_indexing, encoding="utf-8"),
    ],
)
logger = logging.getLogger("index_documents")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

import tiktoken
from azure.search.documents import SearchClient
from azure.search.documents.models import IndexingResult

from src.config.azure_config import get_openai_client, get_search_client
from src.config.settings import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
)

# ---------------------------------------------------------------------------
# Category map from directory name to category value
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "normativas": "normativa",
    "planes_estudio": "plan_estudio",
    "guias_docentes": "guia_docente",
    "faqs": "faq",
    "procedimientos": "procedimiento",
}

CORPUS_DIR = Path(__file__).parent.parent / "data" / "corpus"
BATCH_SIZE = 50
MAX_RETRIES = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def infer_degree_relevance(category: str, filename: str) -> List[str]:
    """Infiere las titulaciones relevantes a partir del nombre del archivo."""
    name = filename.lower().replace(".md", "")
    if "informatica" in name or "informatica" in name:
        return ["informatica"]
    if "ade" in name:
        return ["ade"]
    if "derecho" in name:
        return ["derecho"]
    return ["all"]


def extract_metadata(content: str, filepath: Path) -> Dict[str, Any]:
    """Extrae title, category, source_file, last_updated, degree_relevance."""
    title = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break

    parent_dir = filepath.parent.name
    category = CATEGORY_MAP.get(parent_dir, parent_dir)
    source_file = filepath.name
    mtime = os.path.getmtime(filepath)
    last_updated = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    degree_relevance = infer_degree_relevance(category, source_file)

    return {
        "title": title,
        "category": category,
        "source_file": source_file,
        "last_updated": last_updated,
        "degree_relevance": degree_relevance,
    }


def split_into_chunks(content: str) -> List[Tuple[str, str]]:
    """Divide el contenido en chunks de ≤ CHUNK_SIZE tokens con solapamiento.

    Returns list of (chunk_text, section_name).
    """
    enc = tiktoken.get_encoding("cl100k_base")

    # Detect section boundaries
    lines = content.splitlines(keepends=True)
    sections: List[Tuple[int, str]] = []  # (char_offset, section_name)
    char_offset = 0
    current_section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            current_section = stripped.lstrip("#").strip()
            sections.append((char_offset, current_section))
        char_offset += len(line)

    def get_section_for_offset(offset: int) -> str:
        result = ""
        for sec_offset, sec_name in sections:
            if sec_offset <= offset:
                result = sec_name
            else:
                break
        return result

    # Split by paragraphs first
    paragraphs = content.split("\n\n")
    chunks: List[Tuple[str, str]] = []
    current_tokens: List[int] = []
    current_texts: List[str] = []
    current_char_pos = 0

    for para in paragraphs:
        para_tokens = enc.encode(para)

        if len(current_tokens) + len(para_tokens) <= CHUNK_SIZE:
            current_tokens.extend(para_tokens)
            current_texts.append(para)
        else:
            # Flush current chunk if non-empty
            if current_tokens:
                chunk_text = "\n\n".join(current_texts)
                section = get_section_for_offset(current_char_pos)
                chunks.append((chunk_text, section))
                # Overlap: keep last CHUNK_OVERLAP tokens worth of text
                overlap_tokens = current_tokens[-CHUNK_OVERLAP:]
                overlap_text = enc.decode(overlap_tokens)
                current_tokens = overlap_tokens
                current_texts = [overlap_text]

            # If paragraph itself exceeds CHUNK_SIZE, split by lines
            if len(para_tokens) > CHUNK_SIZE:
                lines_in_para = para.split("\n")
                for line in lines_in_para:
                    line_tokens = enc.encode(line)
                    if len(current_tokens) + len(line_tokens) <= CHUNK_SIZE:
                        current_tokens.extend(line_tokens)
                        current_texts.append(line)
                    else:
                        if current_tokens:
                            chunk_text = "\n".join(current_texts)
                            section = get_section_for_offset(current_char_pos)
                            chunks.append((chunk_text, section))
                            overlap_tokens = current_tokens[-CHUNK_OVERLAP:]
                            overlap_text = enc.decode(overlap_tokens)
                            current_tokens = overlap_tokens
                            current_texts = [overlap_text]
                        current_tokens.extend(line_tokens)
                        current_texts.append(line)
            else:
                current_tokens.extend(para_tokens)
                current_texts.append(para)

        current_char_pos += len(para) + 2  # +2 for '\n\n'

    if current_tokens:
        chunk_text = "\n\n".join(current_texts)
        section = get_section_for_offset(current_char_pos)
        chunks.append((chunk_text, section))

    return chunks


def generate_embedding_with_retry(client, text: str) -> Optional[List[float]]:
    """Genera embedding con retry exponential backoff ante rate-limit (429)."""
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", EMBEDDING_MODEL)
    for attempt in range(MAX_RETRIES):
        try:
            response = client.embeddings.create(
                input=text,
                model=deployment,
                dimensions=EMBEDDING_DIMENSIONS,
            )
            return response.data[0].embedding
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate" in err_str.lower():
                wait = 2 ** attempt
                logger.warning(f"Rate limit hit (intento {attempt + 1}/{MAX_RETRIES}). Esperando {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Error generando embedding: {e}")
                return None
    logger.error("Máximo de reintentos alcanzado para embedding.")
    return None


def safe_id(source_file: str, page_number: int, chunk_index: int) -> str:
    base = source_file.replace(" ", "_").replace(".", "_")
    return f"{base}_{page_number}_{chunk_index}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=== Iniciando indexación del corpus ===")
    t_start = time.time()

    openai_client = get_openai_client()
    search_client: SearchClient = get_search_client()

    md_files = sorted(CORPUS_DIR.rglob("*.md"))
    logger.info(f"Archivos .md encontrados: {len(md_files)}")

    total_docs = len(md_files)
    total_chunks = 0
    uploaded_chunks = 0
    error_chunks = 0
    total_embeddings = 0
    batch: List[Dict[str, Any]] = []

    def flush_batch() -> Tuple[int, int]:
        nonlocal uploaded_chunks, error_chunks
        if not batch:
            return 0, 0
        try:
            results: List[IndexingResult] = search_client.upload_documents(documents=batch)
            ok = sum(1 for r in results if r.succeeded)
            fail = sum(1 for r in results if not r.succeeded)
            for r in results:
                if not r.succeeded:
                    logger.error(f"Error subiendo doc {r.key}: {r.error_message}")
            uploaded_chunks += ok
            error_chunks += fail
            logger.info(f"Batch subido: {ok} OK, {fail} errores")
        except Exception as e:
            logger.error(f"Error en batch upload: {e}")
            error_chunks += len(batch)
        batch.clear()

    for filepath in md_files:
        content = filepath.read_text(encoding="utf-8")
        meta = extract_metadata(content, filepath)
        chunks = split_into_chunks(content)
        file_chunk_count = len(chunks)
        total_chunks += file_chunk_count
        logger.info(f"  {filepath.name}: {file_chunk_count} chunks")

        for chunk_index, (chunk_text, section) in enumerate(chunks):
            embedding = generate_embedding_with_retry(openai_client, chunk_text)
            if embedding is None:
                logger.error(f"Sin embedding para {filepath.name} chunk {chunk_index}. Saltando.")
                error_chunks += 1
                continue

            total_embeddings += 1
            page_number = chunk_index // 3 + 1

            doc = {
                "id": safe_id(meta["source_file"], page_number, chunk_index),
                "content": chunk_text,
                "title": meta["title"],
                "category": meta["category"],
                "source_file": meta["source_file"],
                "page_number": page_number,
                "section": section,
                "last_updated": meta["last_updated"],
                "chunk_index": chunk_index,
                "degree_relevance": meta["degree_relevance"],
                "embedding": embedding,
            }
            batch.append(doc)

            if len(batch) >= BATCH_SIZE:
                flush_batch()

    flush_batch()

    elapsed = time.time() - t_start
    summary = (
        "═══════════════════════════════\n"
        "  INDEXACIÓN COMPLETADA\n"
        "═══════════════════════════════\n"
        f"  Documentos procesados: {total_docs}/19\n"
        f"  Chunks generados:      {total_chunks}\n"
        f"  Chunks subidos:        {uploaded_chunks}\n"
        f"  Chunks con error:      {error_chunks}\n"
        f"  Tiempo total:          {elapsed:.1f} segundos\n"
        f"  Embeddings generados:  {total_embeddings}\n"
        "═══════════════════════════════"
    )
    print(summary)
    logger.info(summary)
    logger.info("=== Indexación completada ===")


if __name__ == "__main__":
    main()

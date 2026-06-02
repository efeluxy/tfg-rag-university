"""Agente Retriever: genera queries optimizadas y recupera documentos relevantes."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.azure_config import get_openai_client
from src.config.settings import MAX_RETRIEVED_DOCS, TOP_K_DEFAULT
from src.graph.state import UniversityAssistantState
from src.prompts.retriever_prompt import RETRIEVER_SYSTEM_PROMPT
from src.tools.azure_search import search_knowledge_base

logger = logging.getLogger(__name__)

_NO_RETRIEVAL_INTENTS = {"GREETING", "OUT_OF_SCOPE"}


def _generate_queries(key_points: List[str], intent: str, user_message: str) -> List[str]:
    """Llama a Azure OpenAI para generar queries optimizadas.

    Falls back to user_message if parsing fails.
    """
    if not key_points:
        return [user_message]

    user_content = (
        f"Intent: {intent}\n"
        f"Puntos clave: {', '.join(key_points)}\n"
        f"Mensaje original: {user_message}"
    )
    raw = ""
    try:
        client = get_openai_client()
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": RETRIEVER_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=200,
            timeout=20,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        parsed = json.loads(raw)
        queries = parsed.get("queries", [])
        if isinstance(queries, list) and queries:
            return [q for q in queries if isinstance(q, str) and q.strip()]
    except Exception as exc:
        logger.warning("Retriever: error generando queries — %s. Usando user_message.", exc)

    return [user_message]


def run_retriever(state: UniversityAssistantState) -> Dict[str, Any]:
    """Genera queries optimizadas y recupera documentos de Azure AI Search.

    Aplica top_k dinamico (mayor para consultas enumerativas) y enriquece
    la query cuando el mensaje es corto y hay historial disponible.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con retrieved_docs (lista deduplicada y ordenada) y search_queries.
    """
    intent = state.get("intent", "")
    key_points = state.get("key_points", [])
    user_message = state["user_message"]
    is_enum = state.get("is_enumerative_query", False)

    if intent in _NO_RETRIEVAL_INTENTS:
        logger.debug("Retriever: omitiendo recuperación para intent=%s", intent)
        return {"retrieved_docs": [], "search_queries": []}

    # Query expansion simple cuando el mensaje es corto y hay historial
    history = state.get("conversation_history") or state.get("message_history", [])
    enriched_query = user_message
    if len(user_message.split()) < 5 and history:
        last_assistant = next(
            (m["content"] for m in reversed(history) if m.get("role") == "assistant"),
            None,
        )
        if last_assistant:
            enriched_query = f"{last_assistant[:300]} {user_message}"

    queries = _generate_queries(key_points, intent, enriched_query)
    logger.info("Retriever: queries generadas — %s", queries)

    # Top-k dinamico: mas chunks para consultas enumerativas
    top_k = 10 if is_enum else TOP_K_DEFAULT

    seen: set = set()
    all_docs: List[dict] = []

    for query in queries:
        results = search_knowledge_base(query, top_k=top_k)
        for doc in results:
            dedup_key = (doc.get("source_file", ""), doc.get("section", ""))
            if dedup_key not in seen:
                seen.add(dedup_key)
                all_docs.append(doc)

    all_docs.sort(key=lambda d: d.get("relevance_score", 0.0), reverse=True)
    final_docs = all_docs[:top_k]

    logger.info(
        "Retriever: %d docs recuperados tras deduplicación (de %d totales), top_k=%d",
        len(final_docs),
        len(all_docs),
        top_k,
    )
    return {"retrieved_docs": final_docs, "search_queries": queries}

"""Tool LangChain para búsqueda híbrida en Azure AI Search."""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.config.azure_config import get_openai_client, get_search_client
from src.config.settings import MAX_RETRIEVED_DOCS, RETRIEVAL_SCORE_THRESHOLD, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)


class _SearchInput(BaseModel):
    query: str = Field(description="Consulta en texto natural en español.")


def _generate_query_embedding(query: str) -> List[float]:
    """Genera el embedding de la query usando Azure OpenAI."""
    client = get_openai_client()
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", EMBEDDING_MODEL)
    response = client.embeddings.create(
        input=query,
        model=deployment,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return response.data[0].embedding


def search_knowledge_base(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Ejecuta búsqueda híbrida y devuelve chunks relevantes con metadatos.

    Args:
        query: Consulta en lenguaje natural.
        top_k: Número máximo de resultados a devolver.

    Returns:
        Lista de dicts con content, title, category, source_file, section,
        page_number, relevance_score y citation.
    """
    from azure.search.documents.models import VectorizedQuery

    search_client = get_search_client()
    embedding = _generate_query_embedding(query)

    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=top_k,
        fields="embedding",
    )

    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        query_type="semantic",
        semantic_configuration_name="semantic-config",
        select="content,title,category,source_file,section,page_number",
        top=top_k,
    )

    docs: List[Dict[str, Any]] = []
    for result in results:
        score = result.get("@search.reranker_score") or result.get("@search.score") or 0.0
        if score < RETRIEVAL_SCORE_THRESHOLD:
            continue
        page = result.get("page_number") or 1
        title = result.get("title") or ""
        section = result.get("section") or ""
        citation_parts = [f"Fuente: {title}"]
        if section:
            citation_parts.append(section)
        citation_parts.append(f"pág. {page}")
        docs.append(
            {
                "content": result.get("content", ""),
                "title": title,
                "category": result.get("category", ""),
                "source_file": result.get("source_file", ""),
                "section": section,
                "page_number": page,
                "relevance_score": round(float(score), 4),
                "citation": f"[{', '.join(citation_parts)}]",
            }
        )

    if not docs:
        logger.warning("No se encontraron resultados relevantes para la query: %s", query)

    return docs


class AzureSearchTool(BaseTool):
    name: str = "university_knowledge_search"
    description: str = (
        "Busca información en la base de conocimiento universitaria. "
        "Úsala para responder preguntas sobre normativas, planes de estudio, "
        "guías docentes, becas, procedimientos administrativos y servicios "
        "de la universidad. Input: query en texto natural en español. "
        "Output: fragmentos relevantes con sus fuentes."
    )
    args_schema: Type[BaseModel] = _SearchInput

    def _run(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Ejecuta la búsqueda híbrida y devuelve los resultados relevantes."""
        return search_knowledge_base(query, top_k=MAX_RETRIEVED_DOCS)

    async def _arun(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        raise NotImplementedError("Usa _run en modo síncrono.")

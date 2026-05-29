"""Agente Generator: genera la respuesta final usando el contexto completo del State."""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.azure_config import get_openai_client
from src.graph.state import UniversityAssistantState
from src.prompts.generator_prompt import (
    GENERATOR_SYSTEM_PROMPT,
    format_retrieved_docs,
    format_student_context,
)

logger = logging.getLogger(__name__)

_SOURCE_PATTERN = re.compile(r"\[Fuente:[^\]]+\]")


def _extract_sources(text: str) -> List[str]:
    """Extrae todas las citas [Fuente: ...] de la respuesta generada."""
    return list(dict.fromkeys(_SOURCE_PATTERN.findall(text)))


def _calculate_confidence(retrieved_docs: List[dict]) -> float:
    """Calcula la confianza en función de los scores de los documentos recuperados."""
    if not retrieved_docs:
        return 0.4
    max_score = max(d.get("relevance_score", 0.0) for d in retrieved_docs)
    if max_score > 2.0:
        return 1.0
    if max_score >= 1.0:
        return 0.7
    return 0.4


def run_generator(state: UniversityAssistantState) -> Dict[str, Any]:
    """Genera la respuesta final del asistente.

    Si el guardrail está activo y ya hay una final_response, la devuelve
    directamente sin llamar a la API. En caso contrario, llama a Azure OpenAI.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con final_response, sources, confidence y message_history actualizado.
    """
    user_message = state["user_message"]
    guardrail_triggered = state.get("guardrail_triggered", False)
    existing_response = state.get("final_response")

    if guardrail_triggered and existing_response:
        logger.info("Generator: guardrail activo — devolviendo safe_response sin llamar a la API")
        return {
            "final_response": existing_response,
            "sources": [],
            "confidence": 1.0,
            "message_history": [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": existing_response},
            ],
        }

    retrieved_docs = state.get("retrieved_docs", [])
    student_record = state.get("student_record")

    student_context = format_student_context(student_record)
    retrieved_docs_formatted = format_retrieved_docs(retrieved_docs)

    system_prompt = GENERATOR_SYSTEM_PROMPT.format(
        student_context=student_context,
        retrieved_docs_formatted=retrieved_docs_formatted,
    )

    try:
        client = get_openai_client()
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=1000,
            timeout=20,
        )
        final_response = response.choices[0].message.content.strip()

    except Exception as exc:
        logger.error("Generator: error llamando a Azure OpenAI — %s", exc)
        final_response = (
            "Lo siento, ha ocurrido un error procesando tu consulta. "
            "Por favor, inténtalo de nuevo o contacta con secretaría académica."
        )

    sources = _extract_sources(final_response)
    confidence = _calculate_confidence(retrieved_docs)

    logger.info(
        "Generator: respuesta generada — %d chars, %d fuentes, confidence=%.1f",
        len(final_response),
        len(sources),
        confidence,
    )

    return {
        "final_response": final_response,
        "sources": sources,
        "confidence": confidence,
        "message_history": [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": final_response},
        ],
    }

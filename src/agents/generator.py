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
    build_emotional_tier_section,
    format_retrieved_docs,
    format_student_context,
)

logger = logging.getLogger(__name__)

_SOURCE_PATTERN = re.compile(r"\[Fuente:[^\]]+\]")

_CRISIS_RESPONSE = (
    "Lo que estas compartiendo es muy importante y quiero pedirte "
    "que hables YA con un profesional que pueda ayudarte de verdad.\n\n"
    "Servicio de Orientacion Psicologica de la Universidad Demo:\n"
    "   psicologia@universidad.es\n"
    "   900 456 789 (lunes a viernes, 9h-18h)\n"
    "   Tambien puedes pasarte sin cita previa por el Edificio B, planta 2.\n\n"
    "Si necesitas hablar ahora mismo:\n"
    "   024 -- Linea de Atencion al Suicidio (24h, gratuita)\n"
    "   112 -- Emergencias\n\n"
    "No estas solo/a. Hay personas preparadas para escucharte y ayudarte. "
    "Por favor, contacta con cualquiera de estos recursos ahora."
)


def _extract_sources(text: str) -> List[str]:
    """Extrae todas las citas [Fuente: ...] de la respuesta generada."""
    return list(dict.fromkeys(_SOURCE_PATTERN.findall(text)))


def _calculate_confidence(retrieved_docs: List[dict]) -> float:
    """Calcula la confianza en funcion de los scores de los documentos recuperados."""
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

    Logica por tier emocional:
    - Tier 3 (crisis_grave): respuesta predefinida + alerta critica. NO llama al LLM.
    - out_of_scope (guardrail_triggered + final_response ya en state): devuelve directamente.
    - Tier 1/2 y resto: llama al LLM con el system prompt ajustado al tier.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con final_response, sources, confidence y message_history actualizado.
    """
    user_message = state["user_message"]
    emotional_tier = state.get("emotional_tier", 0)
    guardrail_triggered = state.get("guardrail_triggered", False)
    existing_response = state.get("final_response")

    # --- TIER 3: crisis grave — respuesta predefinida + alerta ---
    if emotional_tier == 3:
        logger.warning(
            "Generator: TIER 3 crisis_grave — respuesta predefinida, sin LLM | user=%s",
            state.get("user_id"),
        )
        final_response = _CRISIS_RESPONSE

        alert_id = None
        alert_generated = False
        try:
            from src.utils.critical_alert import generate_critical_alert

            alert_id = generate_critical_alert(
                user_id=state.get("user_id"),
                trigger_message=user_message,
                conversation_history=state.get("message_history", []),
                session_id=state.get("session_id", "unknown"),
                tier_rationale=state.get("guardrail_reason", "crisis_grave"),
            )
            alert_generated = True
            logger.warning(
                "Generator: alerta critica generada %s para user=%s",
                alert_id,
                state.get("user_id"),
            )
        except Exception as exc:
            logger.error("Generator: fallo generando alerta critica — %s", exc)

        return {
            "final_response": final_response,
            "sources": [],
            "confidence": 1.0,
            "alert_generated": alert_generated,
            "alert_id": alert_id,
            "message_history": [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": final_response},
            ],
        }

    # --- Out of scope / inapropiado: ya existe safe_response en state ---
    if guardrail_triggered and existing_response:
        logger.info("Generator: guardrail out_of_scope — devolviendo safe_response sin LLM")
        return {
            "final_response": existing_response,
            "sources": [],
            "confidence": 1.0,
            "message_history": [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": existing_response},
            ],
        }

    # --- Flujo normal (tier 0, 1, 2): llamar al LLM ---
    retrieved_docs = state.get("retrieved_docs", [])
    student_record = state.get("student_record")

    student_status = ""
    if student_record:
        profile = student_record.get("profile", {})
        student_status = profile.get("status", "")

    student_context = format_student_context(student_record)
    retrieved_docs_formatted = format_retrieved_docs(retrieved_docs)
    emotional_tier_section = build_emotional_tier_section(emotional_tier, student_status)

    system_prompt = GENERATOR_SYSTEM_PROMPT.format(
        student_context=student_context,
        retrieved_docs_formatted=retrieved_docs_formatted,
        emotional_tier_section=emotional_tier_section,
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
            "Por favor, intentalo de nuevo o contacta con secretaria academica."
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

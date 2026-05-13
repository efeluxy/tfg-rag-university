"""Agente Router: clasifica la intención del mensaje del usuario."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.azure_config import get_openai_client
from src.graph.state import VALID_INTENTS, UniversityAssistantState
from src.prompts.router_prompt import ROUTER_SYSTEM_PROMPT, ROUTER_USER_TEMPLATE

logger = logging.getLogger(__name__)

_FALLBACK = {
    "intent": "GREETING",
    "key_points": [],
    "requires_student_data": False,
    "router_reasoning": "Fallback por error de parseo",
}


def _build_history_context(message_history: list) -> str:
    """Formatea los últimos 3 turnos del historial como texto plano."""
    recent = message_history[-6:]  # hasta 3 pares (user + assistant)
    lines = []
    for msg in recent:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"Usuario: {content}")
        elif role == "assistant":
            lines.append(f"Asistente: {content}")
    return "\n".join(lines) if lines else "(sin historial previo)"


def run_router(state: UniversityAssistantState) -> Dict[str, Any]:
    """Clasifica la consulta del usuario y extrae puntos clave.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con intent, key_points, requires_student_data, router_reasoning.
    """
    user_message = state["user_message"]
    history_context = _build_history_context(state.get("message_history", []))

    user_content = ROUTER_USER_TEMPLATE.format(
        history_context=history_context,
        user_message=user_message,
    )

    try:
        client = get_openai_client()
        import os
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        logger.debug("Router raw response: %s", raw)

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)

        intent = parsed.get("intent", "GREETING")
        if intent not in VALID_INTENTS:
            logger.warning("Intent '%s' no válido, usando GREETING", intent)
            intent = "GREETING"

        return {
            "intent": intent,
            "key_points": parsed.get("key_points", []),
            "requires_student_data": bool(parsed.get("requires_student_data", False)),
            "router_reasoning": parsed.get("reasoning", ""),
        }

    except json.JSONDecodeError as exc:
        logger.warning("Router: JSON inválido — %s | raw=%s", exc, raw if "raw" in dir() else "")
        return dict(_FALLBACK)
    except Exception as exc:
        logger.error("Router: error llamando a Azure OpenAI — %s", exc)
        return dict(_FALLBACK)

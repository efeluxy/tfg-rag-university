"""Agente Guardrail: detecta consultas fuera de alcance y crisis emocionales."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.azure_config import get_openai_client
from src.graph.state import UniversityAssistantState
from src.prompts.guardrail_prompt import GUARDRAIL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def run_guardrail(state: UniversityAssistantState) -> Dict[str, Any]:
    """Evalúa si la consulta debe ser bloqueada o derivada.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con guardrail_triggered, guardrail_reason y opcionalmente final_response.
    """
    user_message = state["user_message"]
    intent = state.get("intent", "")

    user_content = f"Intent clasificado: {intent}\nMensaje: {user_message}"

    raw = ""
    try:
        client = get_openai_client()
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=400,
            timeout=20,
        )
        raw = response.choices[0].message.content.strip()
        logger.debug("Guardrail raw response: %s", raw)

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        triggered = bool(parsed.get("triggered", False))
        reason = parsed.get("reason") if triggered else None
        safe_response = parsed.get("safe_response") if triggered else None

        result: Dict[str, Any] = {
            "guardrail_triggered": triggered,
            "guardrail_reason": reason,
        }
        if triggered and safe_response:
            result["final_response"] = safe_response

        if triggered:
            logger.info("Guardrail activado: reason=%s | message=%s", reason, user_message[:80])
        else:
            logger.debug("Guardrail no activado para: %s", user_message[:80])

        return result

    except json.JSONDecodeError as exc:
        logger.warning("Guardrail: JSON inválido — %s | raw=%s", exc, raw)
        # Fallback seguro: no bloquear para no interrumpir el flujo
        return {"guardrail_triggered": False, "guardrail_reason": None}
    except Exception as exc:
        logger.error("Guardrail: error llamando a Azure OpenAI — %s", exc)
        return {"guardrail_triggered": False, "guardrail_reason": None}

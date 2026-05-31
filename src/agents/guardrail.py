"""Agente Guardrail: detecta consultas fuera de alcance y clasifica tiers emocionales."""

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
from src.prompts.guardrail_prompt import (
    EMOTIONAL_TIER_SYSTEM_PROMPT,
    GUARDRAIL_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

_OUT_OF_SCOPE_RESPONSE = (
    "Solo puedo ayudarte con temas relacionados con la Universidad Demo: "
    "normativas, planes de estudio, tramites, orientacion academica y becas. "
    "Para cualquier consulta en ese ambito, estoy a tu disposicion."
)


def _classify_emotional_tier(user_message: str, client, deployment: str) -> Dict[str, Any]:
    """Llama al LLM con el prompt de clasificacion de tiers emocionales.

    Devuelve dict con tier (int), label (str|None) y rationale (str).
    Fallback conservador: tier=2 si falla el LLM o el JSON.
    """
    raw = ""
    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": EMOTIONAL_TIER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
            max_tokens=200,
            timeout=20,
        )
        raw = response.choices[0].message.content.strip()
        logger.debug("Emotional tier raw response: %s", raw)

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        tier = int(data.get("tier", 0))
        label = data.get("label")
        rationale = data.get("rationale", "")
        if tier not in (0, 1, 2, 3):
            tier = 2
            label = "emotional_distress"
        return {"tier": tier, "label": label, "rationale": rationale}

    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Guardrail emotional tier: JSON invalido — %s | raw=%s", exc, raw)
        return {"tier": 2, "label": "emotional_distress", "rationale": "fallback-json-error"}
    except Exception as exc:
        exc_str = str(exc)
        # Si Azure bloquea el mensaje por self_harm, es una senal inequivoca de crisis grave
        if "content_filter" in exc_str and "self_harm" in exc_str:
            logger.warning(
                "Guardrail emotional tier: Azure content_filter self_harm detectado "
                "— clasificando automaticamente como tier 3"
            )
            return {"tier": 3, "label": "crisis_grave", "rationale": "azure-content-filter-self_harm"}
        logger.error("Guardrail emotional tier: error Azure OpenAI — %s", exc)
        return {"tier": 2, "label": "emotional_distress", "rationale": "fallback-api-error"}


def _check_out_of_scope(user_message: str, intent: str, client, deployment: str) -> Dict[str, Any]:
    """Comprueba si la consulta es out_of_scope o inapropiada.

    Devuelve dict compatible con el State del guardrail.
    """
    user_content = f"Intent clasificado: {intent}\nMensaje: {user_message}"
    raw = ""
    try:
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
            "emotional_tier": 0,
            "emotional_tier_label": None,
        }
        if triggered and safe_response:
            result["final_response"] = safe_response

        if triggered:
            logger.info("Guardrail out_of_scope activado: reason=%s | message=%s", reason, user_message[:80])
        return result

    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Guardrail out_of_scope: JSON invalido — %s | raw=%s", exc, raw)
        return {"guardrail_triggered": False, "guardrail_reason": None,
                "emotional_tier": 0, "emotional_tier_label": None}
    except Exception as exc:
        logger.error("Guardrail out_of_scope: error Azure OpenAI — %s", exc)
        return {"guardrail_triggered": False, "guardrail_reason": None,
                "emotional_tier": 0, "emotional_tier_label": None}


def run_guardrail(state: UniversityAssistantState) -> Dict[str, Any]:
    """Evalua si la consulta debe ser bloqueada y clasifica el tier emocional.

    Logica:
    - Si intent == EMOTIONAL_SUPPORT: clasifica en tier 0-3 con el nuevo prompt.
      Solo activa guardrail_triggered si tier == 3 (crisis_grave).
    - En cualquier otro caso: usa el guardrail original para out_of_scope/inapropiado.

    Args:
        state: Estado actual del grafo.

    Returns:
        Dict con guardrail_triggered, guardrail_reason, emotional_tier,
        emotional_tier_label y opcionalmente final_response.
    """
    user_message = state["user_message"]
    intent = state.get("intent", "")

    try:
        client = get_openai_client()
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    except Exception as exc:
        logger.error("Guardrail: no se pudo obtener cliente Azure — %s", exc)
        return {
            "guardrail_triggered": False,
            "guardrail_reason": None,
            "emotional_tier": 0,
            "emotional_tier_label": None,
        }

    if intent == "EMOTIONAL_SUPPORT":
        tier_data = _classify_emotional_tier(user_message, client, deployment)
        tier = tier_data["tier"]
        label = tier_data["label"]
        rationale = tier_data["rationale"]

        if tier == 3:
            logger.warning(
                "Guardrail: CRISIS GRAVE detectada (tier 3) | message=%s", user_message[:80]
            )
            return {
                "guardrail_triggered": True,
                "guardrail_reason": "crisis_grave",
                "emotional_tier": 3,
                "emotional_tier_label": "crisis_grave",
            }
        elif tier in (1, 2):
            logger.info(
                "Guardrail: tier emocional %d (%s) | message=%s", tier, label, user_message[:80]
            )
            return {
                "guardrail_triggered": False,
                "guardrail_reason": f"emotional_tier_{tier}",
                "emotional_tier": tier,
                "emotional_tier_label": label,
            }
        else:
            logger.debug("Guardrail: EMOTIONAL_SUPPORT clasificado tier 0, flujo normal")
            return {
                "guardrail_triggered": False,
                "guardrail_reason": None,
                "emotional_tier": 0,
                "emotional_tier_label": None,
            }

    # Ruta original: out_of_scope, inappropriate, etc.
    return _check_out_of_scope(user_message, intent, client, deployment)

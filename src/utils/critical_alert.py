"""Modulo de alertas criticas para deteccion de crisis emocionales.

Cuando el Guardrail detecta tier 3 (crisis_grave), este modulo:
1. Genera un archivo JSON con todos los datos del incidente en
   data/alerts/ALERT-<TIMESTAMP>-<UUID>.json
2. Anade una linea (formato JSONL) en logs/critical_alerts.log
3. Devuelve el alert_id para que quede registrado en el state.

NOTA: En esta version de TFG NO se envia email/SMS/llamada.
El modulo esta disenado para extenderse facilmente en el futuro
(ver docs/EMOTIONAL_GUARDRAIL_DESIGN.md, seccion "Trabajo Futuro").
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
ALERTS_DIR = PROJECT_ROOT / "data" / "alerts"
ALERTS_LOG = PROJECT_ROOT / "logs" / "critical_alerts.log"
SQLITE_PATH = PROJECT_ROOT / "data" / "database" / "students.db"


def _fetch_student_record(user_id: str) -> dict | None:
    """Consulta la BD de alumnos y devuelve los datos del alumno identificado."""
    if not user_id:
        return None
    try:
        with sqlite3.connect(str(SQLITE_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, name, email, degree, year, gpa, "
                "credits_completed, credits_total, status "
                "FROM students WHERE id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        logger.error("Error consultando alumno %s: %s", user_id, exc)
        return None


def generate_critical_alert(
    user_id: str | None,
    trigger_message: str,
    conversation_history: list,
    session_id: str,
    tier_rationale: str = "",
) -> str:
    """Genera una alerta critica: archivo JSON individual + linea en log JSONL.

    Args:
        user_id: ID del alumno (puede ser None si es anonimo).
        trigger_message: Mensaje del usuario que disparo el tier 3.
        conversation_history: Historial de mensajes del state.
        session_id: ID de la sesion actual.
        tier_rationale: Razon del guardrail (campo rationale del tier classifier).

    Returns:
        El alert_id generado (str).
    """
    alert_id = (
        f"ALERT-{datetime.utcnow():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
    )
    timestamp_iso = datetime.utcnow().isoformat() + "Z"

    student_data = _fetch_student_record(user_id) if user_id else None

    # Tomar ultimos 3 turnos de conversacion (6 mensajes max)
    context = (conversation_history or [])[-6:]

    alert_payload = {
        "alert_id": alert_id,
        "timestamp": timestamp_iso,
        "severity": "CRITICAL",
        "detected_tier": 3,
        "tier_label": "crisis_grave",
        "rationale": tier_rationale,
        "trigger_message": trigger_message,
        "session_id": session_id,
        "student": {
            "user_id": user_id,
            "identified": student_data is not None,
            "name": student_data.get("name") if student_data else None,
            "email": student_data.get("email") if student_data else None,
            "degree": student_data.get("degree") if student_data else None,
            "year": student_data.get("year") if student_data else None,
            "academic_status": student_data.get("status") if student_data else None,
            "gpa": student_data.get("gpa") if student_data else None,
        },
        "conversation_context": [
            {"role": m.get("role"), "content": m.get("content", "")[:500]}
            for m in context
        ],
        "recommended_action": (
            "Contacto inmediato del Servicio de Orientacion Psicologica con el "
            "alumno. Si el alumno esta identificado, llamada telefonica directa "
            "al telefono de contacto del expediente. Citacion urgente en menos "
            "de 24 horas. Si el alumno NO esta identificado, monitorizar futuras "
            "interacciones del mismo session_id."
        ),
        "alert_destination": {
            "primary": "psicologia@universidad.es",
            "phone": "900 456 789",
            "emergency_fallback": "024",
        },
        "system_metadata": {
            "graph_version": "1.0",
            "alert_module_version": "1.0",
            "channels_used": ["log", "json_file"],
            "channels_pending": ["email", "sms", "phone_call"],
        },
    }

    # 1. Escribir archivo JSON individual
    try:
        ALERTS_DIR.mkdir(parents=True, exist_ok=True)
        alert_file = ALERTS_DIR / f"{alert_id}.json"
        alert_file.write_text(
            json.dumps(alert_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.warning("CRITICAL ALERT generada: %s", alert_file)
    except OSError as exc:
        logger.error("Error escribiendo archivo de alerta: %s", exc)

    # 2. Anadir linea al log centralizado (JSONL)
    try:
        ALERTS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ALERTS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(alert_payload, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("Error escribiendo en critical_alerts.log: %s", exc)

    return alert_id

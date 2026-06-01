"""Sistema de autenticacion del asistente universitario.

Soporta tres roles:
  - guest: acceso sin credenciales, sin personalizacion
  - student: acceso con contrasena comun, expediente fijo
  - admin: acceso con contrasena distinta, control completo

Las credenciales se leen de variables de entorno (.env).
Esta es una implementacion simplificada para alcance de TFG;
ver docs/AUTH_DESIGN.md para consideraciones de produccion.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

Role = Literal["guest", "student", "admin"]
VALID_ROLES = ("guest", "student", "admin")

PROJECT_ROOT = Path(__file__).parent.parent
ACCESS_LOG = PROJECT_ROOT / "logs" / "access.log"


def get_student_password() -> str | None:
    """Devuelve la contrasena comun de alumno desde .env, o None."""
    return os.getenv("STUDENT_PASSWORD")


def get_admin_password() -> str | None:
    """Devuelve la contrasena de admin desde .env, o None."""
    return os.getenv("ADMIN_PASSWORD")


def authenticate_student(user_id: str, password: str) -> bool:
    """Verifica credenciales de alumno.

    Returns:
        True si user_id no esta vacio Y password coincide con
        STUDENT_PASSWORD configurada. False en cualquier otro caso.
    """
    if not user_id or not password:
        return False
    expected = get_student_password()
    if not expected:
        logger.warning("STUDENT_PASSWORD no configurada en .env")
        return False
    return password == expected


def authenticate_admin(password: str) -> bool:
    """Verifica credenciales de admin."""
    if not password:
        return False
    expected = get_admin_password()
    if not expected:
        logger.warning("ADMIN_PASSWORD no configurada en .env")
        return False
    return password == expected


def log_access(
    role: Role,
    user_id: str | None,
    success: bool,
    session_id: str | None = None,
) -> None:
    """Registra un intento de acceso en logs/access.log (formato JSONL)."""
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "role": role,
        "user_id": user_id,
        "success": success,
        "session_id": session_id,
    }
    try:
        ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACCESS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("Error escribiendo access.log: %s", exc)


def reset_session(st_session_state) -> None:
    """Limpia el estado de sesion al cerrar."""
    keys_to_clear = (
        "authenticated", "role", "authenticated_user_id",
        "selected_student", "messages", "session_id",
        "pending_message", "processing",
    )
    for key in keys_to_clear:
        if key in st_session_state:
            del st_session_state[key]

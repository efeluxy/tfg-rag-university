"""Script de visualizacion de alertas criticas."""

import json
from pathlib import Path

ALERTS_LOG = Path("logs/critical_alerts.log")


def main():
    if not ALERTS_LOG.exists():
        print("No hay alertas registradas.")
        return
    with ALERTS_LOG.open(encoding="utf-8") as f:
        alerts = [json.loads(line) for line in f if line.strip()]
    if not alerts:
        print("Log vacio.")
        return
    print(f"=== {len(alerts)} ALERTA(S) CRITICA(S) ===\n")
    for a in alerts:
        ts = a.get("timestamp", "?")
        uid = a.get("student", {}).get("user_id") or "ANONIMO"
        name = a.get("student", {}).get("name") or "---"
        msg = a.get("trigger_message", "")[:80]
        print(f"[{ts}] {a.get('alert_id')}")
        print(f"   Alumno: {uid} ({name})")
        print(f"   Mensaje: {msg}")
        print(f"   Accion: {a.get('recommended_action', '')[:120]}...")
        print()


if __name__ == "__main__":
    main()

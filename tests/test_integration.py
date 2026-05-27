# -*- coding: utf-8 -*-
"""Tests de integración end-to-end: 8 casos de uso de la Sección 12 del documento técnico."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph.graph import get_graph
from src.graph.state import get_initial_state

logging.basicConfig(level=logging.WARNING)

LOG_PATH = Path(__file__).parent.parent / "logs" / "test_integration_20260527.txt"

CASOS = [
    # (id, descripcion, mensaje, user_id, intent_esperado, guardrail_esperado)
    ("UI01", "Orientacion itinerario",
     "Que optativas me recomiendas para especializarme en IA?",
     "ALU001", "ACADEMIC_ORIENTATION", False),
    ("UI02", "Consulta requisitos asignatura",
     "Que necesito para matricularme en la asignatura de IA?",
     "ALU001", "COURSE_INFO", False),
    ("UI03", "Alumno at_risk pidiendo ayuda",
     "Tengo asignaturas suspensas repetidas, que hago?",
     "ALU015", "ACADEMIC_ORIENTATION", False),
    ("UI04", "Futuro alumno",
     "Como puedo acceder al grado en informatica desde bachillerato?",
     None, "PROSPECTIVE_STUDENT", False),
    ("UI05", "Consulta beca",
     "Puedo solicitar la beca MEC este anio?",
     "ALU030", "SCHOLARSHIPS", False),
    ("UI06", "Consulta administrativa",
     "Hasta cuando puedo anular la matricula de una asignatura?",
     None, "ADMINISTRATIVE", False),
    ("UI07", "Guardrail out of scope",
     "Cual es la receta de la tortilla de patatas?",
     None, "OUT_OF_SCOPE", True),
    ("UI08", "Guardrail crisis",
     "No puedo mas con todo esto, estoy muy mal",
     None, "EMOTIONAL_SUPPORT", True),
]


def run_tests():
    graph = get_graph()
    resultados = []
    lines = []

    lines.append("=== TEST INTEGRACIÓN END-TO-END ===")
    lines.append(f"Total casos: {len(CASOS)}")
    lines.append("")

    for caso_id, desc, msg, uid, intent_esp, guardrail_esp in CASOS:
        session_id = f"test-integ-{caso_id}"
        state = get_initial_state(msg, session_id, uid)
        config = {"configurable": {"thread_id": session_id}}
        r = graph.invoke(state, config=config)

        intent_ok = r.get("intent") == intent_esp
        guardrail_ok = r.get("guardrail_triggered") == guardrail_esp
        respuesta_ok = (
            r.get("final_response") is not None
            and len(r.get("final_response", "")) > 20
        )
        test_pass = intent_ok and guardrail_ok and respuesta_ok

        resultados.append(test_pass)
        estado = "PASS" if test_pass else "FAIL"
        lines.append(f"  [{caso_id}] {desc[:40]:<40} {estado}")
        if not intent_ok:
            lines.append(f"    Intent esperado {intent_esp}, obtenido {r.get('intent')}")
        if not guardrail_ok:
            lines.append(
                f"    Guardrail esperado {guardrail_esp}, obtenido {r.get('guardrail_triggered')}"
            )
        if not respuesta_ok:
            lines.append(f"    Respuesta ausente o demasiado corta")

    total_pass = sum(resultados)
    lines.append("")
    lines.append(f"  TOTAL: {total_pass}/8 PASS")
    lines.append("  CRITERIO: >= 7/8 para continuar a Fase 5")
    lines.append(f"  RESULTADO: {'SUPERADO' if total_pass >= 7 else 'NO SUPERADO'}")

    output = "\n".join(lines)
    print(output)

    LOG_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.write_text(output + "\n", encoding="utf-8")
    print(f"\nLog guardado en: {LOG_PATH}")

    return total_pass


if __name__ == "__main__":
    run_tests()

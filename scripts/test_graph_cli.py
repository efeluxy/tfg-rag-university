"""Prueba end-to-end del grafo LangGraph con los 5 flujos posibles."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
date_str = datetime.now().strftime("%Y%m%d")
log_file = LOG_DIR / f"fase3b_{date_str}.txt"

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)

from src.graph.graph import build_graph
from src.graph.state import get_initial_state

CASOS_DE_PRUEBA = [
    {
        "id": "G01",
        "descripcion": "Saludo simple — flujo GREETING sin recuperacion",
        "mensaje": "Hola, buenos dias! En que me puedes ayudar?",
        "user_id": None,
        "flujo_esperado": ["router", "guardrail", "retriever", "generator"],
        "intent_esperado": "GREETING",
        "guardrail_esperado": False,
        "verificacion": lambda r: len(r.get("final_response", "")) > 10,
    },
    {
        "id": "G02",
        "descripcion": "Normativa — flujo completo sin expediente",
        "mensaje": "Cuantas veces puedo examinarme de la misma asignatura antes de ser dado de baja?",
        "user_id": None,
        "flujo_esperado": ["router", "guardrail", "retriever", "generator"],
        "intent_esperado": "REGULATIONS",
        "guardrail_esperado": False,
        "verificacion": lambda r: (
            r.get("final_response") is not None
            and len(r.get("retrieved_docs", [])) > 0
            and r.get("confidence", 0) > 0.5
        ),
    },
    {
        "id": "G03",
        "descripcion": "Orientacion academica — flujo con expediente ALU001",
        "mensaje": "Que asignaturas optativas me recomiendas para el proximo curso?",
        "user_id": "ALU001",
        "flujo_esperado": ["router", "guardrail", "retriever", "student_data", "generator"],
        "intent_esperado": "ACADEMIC_ORIENTATION",
        "guardrail_esperado": False,
        "verificacion": lambda r: (
            r.get("student_record") is not None
            and r.get("final_response") is not None
            and len(r.get("final_response", "")) > 100
        ),
    },
    {
        "id": "G04",
        "descripcion": "Consulta fuera de alcance — guardrail OUT_OF_SCOPE",
        "mensaje": "Cual es la capital de Australia?",
        "user_id": None,
        "flujo_esperado": ["router", "guardrail", "generator"],
        "intent_esperado": "OUT_OF_SCOPE",
        "guardrail_esperado": True,
        "verificacion": lambda r: (
            r.get("guardrail_triggered") is True
            and r.get("guardrail_reason") == "out_of_scope"
            and r.get("final_response") is not None
        ),
    },
    {
        "id": "G05",
        "descripcion": "Alumno en riesgo — flujo con expediente ALU015",
        "mensaje": "Tengo varias asignaturas suspensas, que puedo hacer para mejorar?",
        "user_id": "ALU015",
        "flujo_esperado": ["router", "guardrail", "retriever", "student_data", "generator"],
        "intent_esperado": "ACADEMIC_ORIENTATION",
        "guardrail_esperado": False,
        "verificacion": lambda r: (
            r.get("student_record") is not None
            and r.get("student_record", {}).get("profile", {}).get("status") == "at_risk"
            and r.get("final_response") is not None
        ),
    },
]


def run_tests() -> dict:
    graph = build_graph()
    results = {}

    for caso in CASOS_DE_PRUEBA:
        cid = caso["id"]
        print(f"\n{'─'*55}")
        print(f"[{cid}] {caso['descripcion']}")
        print(f"{'─'*55}")

        state = get_initial_state(caso["mensaje"], f"test-{cid}", caso["user_id"])
        config = {"configurable": {"thread_id": f"test-{cid}"}}

        try:
            resultado = graph.invoke(state, config=config)

            intent = resultado.get("intent", "—")
            intent_ok = intent == caso["intent_esperado"]
            guardrail_ok = resultado.get("guardrail_triggered") == caso["guardrail_esperado"]
            verificacion_ok = caso["verificacion"](resultado)
            response_ok = bool(resultado.get("final_response"))

            passed = intent_ok and guardrail_ok and verificacion_ok and response_ok

            print(f"  Intent:      {intent} {'✓' if intent_ok else '✗ (esperado: ' + caso['intent_esperado'] + ')'}")
            print(f"  Guardrail:   triggered={resultado.get('guardrail_triggered')} {'✓' if guardrail_ok else '✗'}")
            if resultado.get("guardrail_reason"):
                print(f"  GR reason:   {resultado.get('guardrail_reason')}")
            print(f"  Docs:        {len(resultado.get('retrieved_docs', []))}")
            print(f"  Expediente:  {resultado.get('student_record') is not None}")
            preview = (resultado.get("final_response") or "")[:150].replace("\n", " ")
            print(f"  Respuesta:   {preview}...")
            print(f"  Sources:     {resultado.get('sources', [])}")
            print(f"  Confidence:  {resultado.get('confidence', 0)}")
            print(f"  → {'PASS' if passed else 'FAIL'}")
            if not passed:
                if not intent_ok:
                    print(f"    MOTIVO: intent esperado={caso['intent_esperado']}, obtenido={intent}")
                if not guardrail_ok:
                    print(f"    MOTIVO: guardrail esperado={caso['guardrail_esperado']}, obtenido={resultado.get('guardrail_triggered')}")
                if not verificacion_ok:
                    print("    MOTIVO: verificacion() devolvio False")
                if not response_ok:
                    print("    MOTIVO: final_response es None o vacio")

            results[cid] = passed

        except Exception as exc:
            print(f"  ERROR: {exc}")
            results[cid] = False

    return results


def main():
    print("=== TEST GRAFO END-TO-END — LangGraph ===")
    results = run_tests()

    pass_count = sum(1 for v in results.values() if v)
    total = len(results)
    passed_criterion = pass_count >= 4

    summary = (
        "\n══════════════════════════════════════════\n"
        "  RESULTADO TEST GRAFO END-TO-END\n"
        "══════════════════════════════════════════\n"
        f"  G01 Saludo:                {'PASS' if results.get('G01') else 'FAIL'}\n"
        f"  G02 Normativa:             {'PASS' if results.get('G02') else 'FAIL'}\n"
        f"  G03 Orientacion + expte:   {'PASS' if results.get('G03') else 'FAIL'}\n"
        f"  G04 Guardrail OOS:         {'PASS' if results.get('G04') else 'FAIL'}\n"
        f"  G05 Alumno at_risk:        {'PASS' if results.get('G05') else 'FAIL'}\n"
        "──────────────────────────────────────────\n"
        f"  TOTAL: {pass_count}/{total} PASS\n"
        "  CRITERIO: >= 4/5 para continuar a Fase 4\n"
        f"  RESULTADO: {'SUPERADO' if passed_criterion else 'NO SUPERADO'}\n"
        "══════════════════════════════════════════"
    )
    print(summary)

    with open(
        Path(__file__).parent.parent / "logs" / f"fase3b_{datetime.now().strftime('%Y%m%d')}.txt",
        "a",
        encoding="utf-8",
    ) as f:
        f.write("\n=== TEST GRAFO END-TO-END ===\n")
        f.write(f"Fecha: {datetime.now().isoformat()}\n")
        f.write(summary + "\n")

    return 0 if passed_criterion else 1


if __name__ == "__main__":
    sys.exit(main())

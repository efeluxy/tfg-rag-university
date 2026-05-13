"""Ensamblaje del grafo LangGraph del asistente universitario."""

import logging
import os

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.generator import run_generator
from src.agents.guardrail import run_guardrail
from src.agents.retriever import run_retriever
from src.agents.router import run_router
from src.agents.student_data import run_student_data
from src.graph.edges import (
    route_after_guardrail,
    route_after_retriever,
    route_after_router,
)
from src.graph.state import UniversityAssistantState

load_dotenv()

logger = logging.getLogger(__name__)


def get_checkpointer():
    """Devuelve el checkpointer según la variable de entorno.

    - USE_SQLITE_CHECKPOINTER=true → SqliteSaver (persistencia real)
    - Cualquier otro valor → MemorySaver (desarrollo y tests)
    """
    use_sqlite = os.getenv("USE_SQLITE_CHECKPOINTER", "false").lower() == "true"
    if use_sqlite:
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            db_path = os.getenv("SQLITE_DB_PATH", "data/database/students.db")
            conv_db = db_path.replace("students.db", "conversations.db")
            logger.info("Usando SqliteSaver: %s", conv_db)
            return SqliteSaver.from_conn_string(conv_db)
        except ImportError:
            logger.warning("SqliteSaver no disponible, usando MemorySaver")
    logger.info("Usando MemorySaver (desarrollo)")
    return MemorySaver()


def build_graph():
    """Construye y compila el grafo LangGraph del asistente universitario.

    Flujo del grafo::

        START
          └─► router
                └─► guardrail  (siempre, via route_after_router)
                      ├─► generator  (si guardrail_triggered=True)
                      └─► retriever  (si guardrail_triggered=False)
                              ├─► student_data  (si requires_student_data + user_id)
                              │         └─► generator
                              └─► generator  (si no necesita expediente)
                                        └─► END

    Returns:
        Grafo compilado listo para invoke().
    """
    checkpointer = get_checkpointer()
    builder = StateGraph(UniversityAssistantState)

    # ── Añadir nodos ──────────────────────────────────────────────
    builder.add_node("router",       run_router)
    builder.add_node("guardrail",    run_guardrail)
    builder.add_node("retriever",    run_retriever)
    builder.add_node("student_data", run_student_data)
    builder.add_node("generator",    run_generator)

    # ── Edge de entrada ───────────────────────────────────────────
    builder.add_edge(START, "router")

    # ── Edge condicional: router → guardrail (siempre) ────────────
    builder.add_conditional_edges(
        "router",
        route_after_router,
        {"guardrail": "guardrail"},
    )

    # ── Edge condicional: guardrail → generator | retriever ───────
    builder.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {
            "generator": "generator",
            "retriever": "retriever",
        },
    )

    # ── Edge condicional: retriever → student_data | generator ────
    builder.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {
            "student_data": "student_data",
            "generator":    "generator",
        },
    )

    # ── Edge fijo: student_data → generator ───────────────────────
    builder.add_edge("student_data", "generator")

    # ── Edge fijo: generator → END ────────────────────────────────
    builder.add_edge("generator", END)

    graph = builder.compile(checkpointer=checkpointer)
    logger.info("Grafo compilado correctamente")
    return graph


# ── Instancia global (se inicializa una vez al importar) ──────────
_graph_instance = None


def get_graph():
    """Devuelve la instancia global del grafo, creándola si no existe."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance

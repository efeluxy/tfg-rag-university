"""Área de chat: historial de mensajes, input y lógica de invocación del grafo."""

import logging
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.graph.state import get_initial_state
from src.utils.conversation import get_recent_history
from app.components.sources_panel import format_sources_html

logger = logging.getLogger(__name__)


def process_message(user_input: str) -> None:
    """Invoca el grafo LangGraph y añade la respuesta al historial."""
    try:
        # Tomar los mensajes previos al actual para contexto conversacional
        all_messages = st.session_state.get("messages", [])
        history = get_recent_history(all_messages, max_turns=6)

        state = get_initial_state(
            user_message=user_input,
            session_id=st.session_state.session_id,
            user_id=st.session_state.selected_student,
            conversation_history=history,
            role=st.session_state.get("role", "guest"),
            authenticated_user_id=st.session_state.get("authenticated_user_id"),
        )
        config = {
            "configurable": {
                "thread_id": st.session_state.session_id
            }
        }
        resultado = st.session_state.graph.invoke(state, config=config)

        final_response = resultado.get("final_response") or ""
        sources = resultado.get("sources", [])
        confidence = resultado.get("confidence", 0.0)

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_response,
            "sources": sources,
            "confidence": confidence,
        })
    except Exception as exc:
        logger.error("Error invocando el grafo: %s", exc, exc_info=True)
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Lo siento, ha ocurrido un error al procesar tu consulta. "
                "Por favor, inténtalo de nuevo."
            ),
            "sources": [],
            "confidence": 0.0,
        })


def render_chat() -> None:
    """Renderiza el área de chat con historial, indicador de escritura e input."""

    # 1. CABECERA (rol-aware)
    role = st.session_state.get("role", "guest")
    selected = st.session_state.get("selected_student")
    students = st.session_state.get("students_list", [])

    if role == "guest":
        subtitulo = "Modo invitado -- consultas publicas"
    elif role == "student":
        nombre = next(
            (s["name"] for s in students if s["id"] == selected), selected or ""
        )
        subtitulo = f"Sesion de estudiante -- {nombre}"
    elif role == "admin":
        if selected:
            nombre = next(
                (s["name"] for s in students if s["id"] == selected), selected
            )
            subtitulo = f"Modo administrador -- consultando como {nombre}"
        else:
            subtitulo = "Modo administrador -- sin alumno seleccionado"
    else:
        subtitulo = ""

    st.markdown(
        "<h3 style='color:#000000; margin-bottom:4px;'>"
        "Asistente de Orientacion Universitaria</h3>",
        unsafe_allow_html=True,
    )
    st.caption(subtitulo)

    st.markdown("---")

    # 2. ÁREA DE MENSAJES
    mensajes = st.session_state.get("messages", [])
    for msg in mensajes:
        role = msg.get("role")
        content = msg.get("content", "")
        sources = msg.get("sources", [])
        confidence = msg.get("confidence", 1.0)

        if role == "user":
            st.markdown(
                '<p style="font-size:0.78rem; color:#000000; margin:8px 0 2px 0;">👤 Tú</p>'
                f'<div class="burbuja-usuario">{content}</div>',
                unsafe_allow_html=True,
            )
        elif role == "assistant":
            st.markdown(
                '<p style="font-size:0.78rem; color:#000000; margin:8px 0 2px 0;">🎓 Asistente Univ</p>'
                f'<div class="burbuja-asistente">{content}</div>',
                unsafe_allow_html=True,
            )
            if sources and len(sources) > 0:
                with st.expander(f"📎 Fuentes consultadas ({len(sources)})"):
                    st.markdown(
                        f'<div class="fuentes-box">{format_sources_html(sources)}</div>',
                        unsafe_allow_html=True,
                    )
            if confidence < 0.6:
                st.markdown(
                    '<p style="font-size:0.8rem; color:#000000;">'
                    "ℹ️ Respuesta basada en conocimiento general</p>",
                    unsafe_allow_html=True,
                )

    # 3. INDICADOR DE ESCRITURA
    if st.session_state.get("processing"):
        st.markdown(
            """
            <div class="typing-indicator">
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
              <span style="margin-left:8px;color:#000000">El asistente está procesando...</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

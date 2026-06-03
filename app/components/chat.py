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
        "<h3 style='color:var(--text); margin-bottom:4px;'>"
        "💬 Asistente de Orientacion Universitaria</h3>",
        unsafe_allow_html=True,
    )
    if subtitulo:
        st.caption(subtitulo)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # 2. ÁREA DE MENSAJES
    mensajes = st.session_state.get("messages", [])

    # 2.0 ESTADO DE BIENVENIDA (solo cuando no hay mensajes)
    if not mensajes and not st.session_state.get("processing"):
        # Personalizar saludo
        if role == "student" or (role == "admin" and selected):
            nombre_corto = next(
                (s["name"].split()[0] for s in students if s["id"] == selected),
                "estudiante"
            )
            saludo = f"Hola, {nombre_corto} 👋 ¿En qué puedo ayudarte hoy?"
        else:
            saludo = "¿En qué puedo ayudarte hoy? 👋"

        st.markdown(
            f"""
            <div style="text-align:center; padding: 48px 24px 32px; max-width:520px; margin:0 auto;">
              <div style="width:64px; height:64px; border-radius:50%; background:var(--primary);
                          color:#fff; font-size:28px; display:flex; align-items:center;
                          justify-content:center; margin:0 auto 20px auto;">🎓</div>
              <div style="font-size:20px; font-weight:600; color:var(--text); margin-bottom:8px;">
                {saludo}
              </div>
              <div style="font-size:14px; color:var(--text-muted); line-height:1.5;">
                Preguntame sobre normativas, becas, asignaturas u orientacion academica.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Chips de sugerencias clicables (implementacion segura via session_state)
        sugerencias = [
            "¿Que optativas me recomiendas para 4o?",
            "¿Como solicito una beca?",
            "¿Cual es la normativa de permanencia?",
            "¿Que asignaturas tengo pendientes?",
        ]
        cols = st.columns(2)
        for i, sug in enumerate(sugerencias):
            with cols[i % 2]:
                if st.button(sug, key=f"chip_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": sug})
                    st.session_state.pending_message = sug
                    st.session_state.processing = True
                    st.rerun()

    for msg in mensajes:
        msg_role = msg.get("role")
        content = msg.get("content", "")
        sources = msg.get("sources", [])
        confidence = msg.get("confidence", 1.0)

        if msg_role == "user":
            st.markdown(
                '<p style="font-size:12px; color:var(--text-muted); margin:8px 0 2px 0; text-align:right;">👤 Tú</p>'
                f'<div class="burbuja-usuario">{content}</div>',
                unsafe_allow_html=True,
            )
        elif msg_role == "assistant":
            st.markdown(
                '<p style="font-size:12px; color:var(--text-muted); margin:8px 0 2px 0;">🎓 Asistente de Orientacion Universitaria</p>'
                f'<div class="burbuja-asistente">{content}</div>',
                unsafe_allow_html=True,
            )
            # B3.3 — Fuentes con estilo pills
            if sources and len(sources) > 0:
                pills_html = "".join(
                    f'<span style="display:inline-block; background:var(--bg); '
                    f'border:1px solid var(--border); border-radius:12px; '
                    f'padding:3px 10px; font-size:11px; color:var(--text-muted); '
                    f'margin:3px 3px 0 0;">📄 {s}</span>'
                    for s in sources
                )
                st.markdown(
                    f'<div style="margin-top:6px;">{pills_html}</div>',
                    unsafe_allow_html=True,
                )
            if confidence < 0.6:
                st.markdown(
                    '<p style="font-size:12px; color:var(--text-muted);">'
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
              <span style="margin-left:8px; color:var(--text-muted); font-size:13px;">El asistente está procesando...</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

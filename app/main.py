"""Punto de entrada de la aplicación Streamlit del Asistente Universitario."""

import logging
import sqlite3
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph.graph import get_graph
from src.graph.state import get_initial_state  # noqa: F401 — disponible para importadores
from src.config.settings import SQLITE_DB_PATH
from app.components.sidebar import render_sidebar
from app.components.chat import render_chat, process_message

# ── Configuración de página (primera llamada Streamlit) ──────────────
st.set_page_config(
    page_title="Asistente Universitario — Universidad Demo",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inyección de CSS personalizado ───────────────────────────────────
_css_path = Path(__file__).parent / "styles" / "main.css"
if _css_path.exists():
    _css_content = _css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{_css_content}</style>", unsafe_allow_html=True)


# ── Carga cacheada de la lista de alumnos ────────────────────────────
@st.cache_data
def load_students_list() -> list:
    """Consulta students.db y devuelve lista de dicts con id y name, ordenados por nombre."""
    try:
        db_path = Path(SQLITE_DB_PATH)
        if not db_path.is_absolute():
            root = Path(__file__).parent.parent
            db_path = root / db_path
        with sqlite3.connect(str(db_path)) as conn:
            cur = conn.execute("SELECT id, name FROM students ORDER BY name")
            return [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
    except Exception as exc:
        logging.getLogger(__name__).error("Error cargando lista de alumnos: %s", exc)
        return []


# ── Inicialización de session_state ─────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_student" not in st.session_state:
    st.session_state.selected_student = None
if "graph" not in st.session_state:
    st.session_state.graph = get_graph()
if "processing" not in st.session_state:
    st.session_state.processing = False
if "students_list" not in st.session_state:
    st.session_state.students_list = load_students_list()
if "pending_message" not in st.session_state:
    st.session_state.pending_message = None

# ── Layout principal ─────────────────────────────────────────────────
col_sidebar, col_chat = st.columns([1, 2.5])

with col_sidebar:
    render_sidebar()

with col_chat:
    render_chat()

# Procesar mensaje pendiente (segundo rerun — fuera de columnas)
if st.session_state.processing and st.session_state.pending_message:
    msg_to_process = st.session_state.pending_message
    st.session_state.pending_message = None
    process_message(msg_to_process)
    st.session_state.processing = False
    st.rerun()

# Input de chat a nivel top, fuera de columnas (evita duplicacion de UI)
user_input = st.chat_input("Escribe tu consulta aqui...")
if user_input and user_input.strip() and not st.session_state.processing:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.pending_message = user_input
    st.session_state.processing = True
    st.rerun()

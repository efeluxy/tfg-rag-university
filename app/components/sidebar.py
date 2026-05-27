"""Sidebar con selector de alumno y panel de expediente académico."""

import sqlite3
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import SQLITE_DB_PATH


def _resolve_db_path() -> str:
    path = Path(SQLITE_DB_PATH)
    if not path.is_absolute():
        root = Path(__file__).parent.parent.parent
        path = root / path
    return str(path)


@st.cache_data(ttl=300)
def get_student_data(student_id: str) -> dict | None:
    """Consulta students.db y devuelve dict con datos del alumno."""
    if not student_id:
        return None
    try:
        with sqlite3.connect(_resolve_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """SELECT id, name, email, degree, year, gpa,
                          credits_completed, credits_total, status
                   FROM students WHERE id = ?""",
                (student_id,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)
    except sqlite3.Error as e:
        st.error(f"Error accediendo a la base de datos: {e}")
        return None


def render_sidebar():
    """Renderiza el panel izquierdo: cabecera, selector de alumno, expediente e info."""

    # 1. CABECERA
    st.markdown(
        """
        <div style="text-align:center; padding: 10px 0 6px 0;">
          <h2 style="color:#1F4E8A; font-size:1.4rem; margin:0;">🎓 Universidad Demo</h2>
          <p style="color:#555577; font-size:0.85rem; margin:4px 0 0 0;">Asistente de Orientación</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # 2. SELECTOR DE ALUMNO
    students = st.session_state.get("students_list", [])
    opciones = ["Sin identificar"] + [f"{s['id']} — {s['name']}" for s in students]

    current_id = st.session_state.get("selected_student")
    current_index = 0
    if current_id:
        for i, s in enumerate(students, start=1):
            if s["id"] == current_id:
                current_index = i
                break

    seleccion = st.selectbox(
        "Identificarte como alumno",
        opciones,
        index=current_index,
        help="Selecciona tu perfil para recibir orientación personalizada",
    )

    nuevo_id = None if seleccion == "Sin identificar" else seleccion.split(" — ")[0]

    if nuevo_id != st.session_state.get("selected_student"):
        st.session_state.selected_student = nuevo_id
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    # 3. PANEL DE EXPEDIENTE (solo si hay alumno seleccionado)
    if st.session_state.get("selected_student"):
        student = get_student_data(st.session_state.selected_student)
        if student:
            gpa = float(student.get("gpa") or 0.0)
            status = student.get("status", "active")
            credits_completed = int(student.get("credits_completed") or 0)
            credits_total = int(student.get("credits_total") or 240) or 240

            if gpa >= 8.0:
                gpa_color = "#1B5E20"
            elif gpa >= 5.0:
                gpa_color = "#0D47A1"
            else:
                gpa_color = "#BF360C"

            badge_class = {
                "excellent": "badge-excellent",
                "active": "badge-active",
                "at_risk": "badge-at-risk",
            }.get(status, "badge-active")

            badge_labels = {
                "excellent": "Excelente",
                "active": "Activo",
                "at_risk": "En riesgo",
            }
            badge_label = badge_labels.get(status, status)

            progress_pct = round((credits_completed / credits_total) * 100, 1)
            degree_short = (student.get("degree") or "—")

            st.markdown(
                f"""
                <div class="expediente-card">
                  <h4>{student.get('name', '')}</h4>
                  <div class="expediente-stat">
                    <span>Grado</span>
                    <span style="font-size:0.78rem; text-align:right;">{degree_short}</span>
                  </div>
                  <div class="expediente-stat">
                    <span>Curso</span>
                    <span>{student.get('year', '—')}º</span>
                  </div>
                  <div class="expediente-stat">
                    <span>Media (GPA)</span>
                    <span style="color:{gpa_color}; font-weight:700;">{gpa:.2f}</span>
                  </div>
                  <div class="expediente-stat">
                    <span>Estado</span>
                    <span class="{badge_class}">{badge_label}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.progress(credits_completed / credits_total)
            st.caption(
                f"{credits_completed} / {credits_total} créditos completados ({progress_pct}%)"
            )

            if status == "at_risk":
                st.warning("⚠️ Alumno con seguimiento especial")

    # 4. BOTÓN LIMPIAR CONVERSACIÓN
    if st.session_state.get("messages"):
        if st.button("🗑️ Limpiar conversación", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

    # 5. INFORMACIÓN DEL SISTEMA
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size:0.75rem; color:#888; text-align:center; line-height:1.8;">
          🟢 Azure AI Search conectado<br>
          v1.0 — TFG 2025<br>
          94 chunks indexados
        </div>
        """,
        unsafe_allow_html=True,
    )

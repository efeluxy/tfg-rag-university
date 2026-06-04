"""Sidebar con selector de alumno, panel de expediente e info del sistema.

Adapta su contenido segun el rol de la sesion:
  - guest:   solo informacion del sistema, sin selector ni expediente.
  - student: expediente fijo del alumno autenticado, sin selector.
  - admin:   selector completo + expediente del alumno seleccionado.
"""

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


def load_all_students() -> list:
    """Devuelve la lista completa de alumnos desde session_state."""
    return st.session_state.get("students_list", [])


def render_student_header(student: dict | None, role: str) -> None:
    """Renderiza el bloque de cabecera del alumno en la sidebar."""
    if role == "guest":
        st.markdown(
            """
            <div class="student-header">
                <div class="student-header-name">Modo invitado</div>
                <div class="student-header-sub">Acceso sin datos personales</div>
                <div class="student-header-meta">Solo consultas generales</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if not student:
        st.markdown(
            '<div class="student-header-empty">Sin alumno seleccionado</div>',
            unsafe_allow_html=True,
        )
        return

    name = student.get("name", "Sin nombre")
    sid = student.get("id", "")
    degree = student.get("degree", "")
    year = student.get("year", "")
    gpa = student.get("gpa", "")
    status = student.get("status", "")

    status_label = {
        "excellent": "Excelente",
        "active": "Activo",
        "at_risk": "En riesgo",
    }.get(status, status.capitalize() if status else "")

    year_label = f"{year} curso" if year else ""
    gpa_label = f"GPA {gpa}" if gpa not in (None, "") else ""

    line3_parts = [p for p in (year_label, gpa_label, status_label) if p]
    line3 = " - ".join(line3_parts)

    st.markdown(
        f"""
        <div class="student-header">
            <div class="student-header-name">{name}</div>
            <div class="student-header-sub">{sid} - {degree}</div>
            <div class="student-header-meta">{line3}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_expediente_card(student_id: str) -> None:
    """Renderiza el panel del expediente academico para el alumno dado."""
    student = get_student_data(student_id)
    if not student:
        return

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
    degree_short = (student.get("degree") or "---")

    st.markdown(
        f"""
        <div class="expediente-card">
          <div class="expediente-stat">
            <span>Grado</span>
            <span style="font-size:0.78rem; text-align:right;">{degree_short}</span>
          </div>
          <div class="expediente-stat">
            <span>Curso</span>
            <span>{student.get('year', '---')}o</span>
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
        f"{credits_completed} / {credits_total} creditos completados ({progress_pct}%)"
    )

    if status == "at_risk":
        st.warning("Alumno con seguimiento especial")


def render_sidebar():
    """Renderiza el panel izquierdo adaptado al rol de la sesion activa."""

    role = st.session_state.get("role", "guest")

    # 1. CABECERA
    st.markdown(
        """
        <div style="text-align:center; padding: 10px 0 6px 0;">
          <h2 style="color:#1F4E8A; font-size:1.4rem; margin:0;">Universidad Demo</h2>
          <p style="color:#555577; font-size:0.85rem; margin:4px 0 0 0;">Asistente de Orientacion</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # 2. HEADER DEL ALUMNO (adaptado al rol)
    if role == "guest":
        render_student_header(None, "guest")

    elif role == "student":
        auth_id = st.session_state.get("authenticated_user_id")
        if st.session_state.get("selected_student") != auth_id:
            st.session_state.selected_student = auth_id
        student_data = get_student_data(auth_id) if auth_id else None
        render_student_header(student_data, "student")

    elif role == "admin":
        # Inicializar criterio de ordenacion
        if "student_sort" not in st.session_state:
            st.session_state["student_sort"] = "Numero"

        sort_choice = st.radio(
            label="Ordenar por",
            options=["Numero", "Alfabetico"],
            index=0 if st.session_state["student_sort"] == "Numero" else 1,
            horizontal=True,
            key="radio_student_sort",
        )
        st.session_state["student_sort"] = sort_choice

        all_students = load_all_students()

        if sort_choice == "Numero":
            sorted_students = sorted(all_students, key=lambda s: s["id"])
            labels_students = [f"{s['id']} - {s['name']}" for s in sorted_students]
        else:
            sorted_students = sorted(all_students, key=lambda s: s["name"].lower())
            labels_students = [f"{s['name']} ({s['id']})" for s in sorted_students]

        opciones = ["Sin identificar"] + labels_students

        # Mantener seleccion previa si existe
        prev_id = st.session_state.get("selected_student")
        current_index = 0
        if prev_id:
            for i, s in enumerate(sorted_students, start=1):
                if s["id"] == prev_id:
                    current_index = i
                    break

        seleccion = st.selectbox(
            "Consultar como alumno",
            opciones,
            index=current_index,
            key="selectbox_student",
            help="Selecciona un alumno para ver su expediente y personalizar respuestas",
        )

        if seleccion == "Sin identificar":
            nuevo_id = None
        else:
            # Extraer id segun el formato del label
            if sort_choice == "Numero":
                nuevo_id = seleccion.split(" - ")[0]
            else:
                # Formato: "Nombre Apellidos (ALUXXX)"
                nuevo_id = seleccion.split("(")[-1].rstrip(")")

        if nuevo_id != st.session_state.get("selected_student"):
            st.session_state.selected_student = nuevo_id
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

        # Header del alumno seleccionado
        selected_data = get_student_data(nuevo_id) if nuevo_id else None
        render_student_header(selected_data, "admin")

    # 3. PANEL DE EXPEDIENTE (solo alumno y admin con alumno seleccionado)
    target_id = st.session_state.get("selected_student")
    if role in ("student", "admin") and target_id:
        _render_expediente_card(target_id)

    # 4. BOTON LIMPIAR CONVERSACION
    if st.session_state.get("messages"):
        if st.button("Limpiar conversacion", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

    # 5. INFORMACION DEL SISTEMA
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size:0.75rem; color:#888; text-align:center; line-height:1.8;">
          Azure AI Search conectado<br>
          v1.0 -- TFG 2026<br>
          94 chunks indexados
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="font-size:0.70rem; color:#888; text-align:center;
                    line-height:1.5; padding:8px; margin-top:10px;
                    border-top:1px solid #333;">
          <b>Aviso de seguridad:</b><br>
          Si el sistema detecta una situacion de crisis emocional grave,
          se generara un aviso automatico al Servicio de Orientacion
          Psicologica de la Universidad para que puedan contactar contigo
          cuanto antes.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 6. BOTON CERRAR SESION
    st.markdown("---")
    st.markdown(
        '<span id="logout-anchor" style="display:none"></span>',
        unsafe_allow_html=True,
    )
    if st.button("Cerrar sesion", use_container_width=True, key="btn_logout"):
        from app.auth import reset_session

        reset_session(st.session_state)
        st.rerun()

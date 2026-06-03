"""Pantalla de login con 3 modos: alumno, invitado, admin."""

import uuid

import streamlit as st

from app.auth import (
    authenticate_admin,
    authenticate_student,
    log_access,
)


def _start_session(role: str, user_id: str | None) -> None:
    """Inicializa el estado de sesion tras login exitoso."""
    st.session_state.authenticated = True
    st.session_state.role = role
    st.session_state.authenticated_user_id = user_id
    st.session_state.selected_student = user_id  # admin lo podra cambiar
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.pending_message = None
    st.session_state.processing = False
    log_access(role, user_id, True, st.session_state.session_id)


def render_login() -> None:
    """Renderiza la pantalla de bienvenida con 3 tabs."""

    # CABECERA CENTRADA
    st.markdown(
        """
        <div style="text-align:center; padding: 30px 0 15px 0;">
          <h1 style="color:#000000; margin:0;">Universidad Demo</h1>
          <p style="font-size:1rem; margin:8px 0 0 0;">
            Asistente de Orientacion Universitaria
          </p>
          <p style="font-size:0.85rem; margin:4px 0 0 0;">
            Identifica tu modo de acceso para continuar
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    tab_alumno, tab_invitado, tab_admin = st.tabs(
        ["Alumno", "Invitado", "Administrador"]
    )

    # TAB 1: ALUMNO
    with tab_alumno:
        st.markdown(
            "**Acceso para estudiantes matriculados.** "
            "Selecciona tu identidad e introduce la contrasena."
        )
        all_students = st.session_state.get("students_list", [])
        if not all_students:
            st.warning("No hay alumnos cargados en el sistema.")
        else:
            # Selector de ordenacion segmentado
            if "login_student_sort" not in st.session_state:
                st.session_state["login_student_sort"] = "Numero"

            sort_choice = st.segmented_control(
                label="Ordenar alumnos por",
                options=["Numero", "Alfabetico"],
                default=st.session_state.get("login_student_sort", "Numero"),
                key="seg_login_student_sort",
                selection_mode="single",
            )
            # segmented_control puede devolver None si no hay seleccion
            if sort_choice is None:
                sort_choice = "Numero"
            st.session_state["login_student_sort"] = sort_choice

            if sort_choice == "Numero":
                sorted_students = sorted(all_students, key=lambda s: s["id"])
                labels = [f"{s['id']} -- {s['name']}" for s in sorted_students]
            else:
                sorted_students = sorted(all_students, key=lambda s: s["name"].lower())
                labels = [f"{s['name']} ({s['id']})" for s in sorted_students]

            # Mantener seleccion previa entre cambios de orden
            prev_id = st.session_state.get("login_selected_student_id")
            default_idx = 0
            if prev_id:
                for i, s in enumerate(sorted_students):
                    if s["id"] == prev_id:
                        default_idx = i
                        break

            selected_label = st.selectbox(
                "Selecciona tu identidad",
                options=labels,
                index=default_idx,
                key="login_selectbox_student",
            )
            selected_idx = labels.index(selected_label)
            st.session_state["login_selected_student_id"] = sorted_students[selected_idx]["id"]
            uid = sorted_students[selected_idx]["id"]

            password = st.text_input(
                "Contrasena",
                type="password",
                key="login_student_password",
            )
            if st.button(
                "Acceder", key="btn_login_student", use_container_width=True
            ):
                if authenticate_student(uid, password):
                    _start_session("student", uid)
                    st.rerun()
                else:
                    log_access("student", uid, False, None)
                    st.error("Contrasena incorrecta. Intentalo de nuevo.")

    # TAB 2: INVITADO
    with tab_invitado:
        st.markdown(
            "**Acceso publico sin autenticacion.** "
            "Podras consultar informacion general de la universidad "
            "(grados, becas, normativa, plazos administrativos). "
            "No tendras acceso a expedientes ni respuestas personalizadas."
        )
        if st.button(
            "Entrar como invitado", key="btn_login_guest", use_container_width=True
        ):
            _start_session("guest", None)
            st.rerun()

    # TAB 3: ADMINISTRADOR
    with tab_admin:
        st.markdown(
            "**Acceso administrativo.** "
            "Permite consultar el sistema como si fueras cualquier "
            "alumno, para tareas de soporte y verificacion."
        )
        password = st.text_input(
            "Contrasena de administrador",
            type="password",
            key="login_admin_password",
        )
        if st.button(
            "Acceder como administrador",
            key="btn_login_admin",
            use_container_width=True,
        ):
            if authenticate_admin(password):
                _start_session("admin", None)
                st.rerun()
            else:
                log_access("admin", None, False, None)
                st.error("Contrasena incorrecta.")

    # AVISO LEGAL AL PIE
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size:0.75rem; text-align:center;
                    line-height:1.6; padding-top:10px;">
          Sistema de demostracion academica (TFG 2026).
          Las credenciales se almacenan localmente y los datos de
          alumnos son sinteticos.
        </div>
        """,
        unsafe_allow_html=True,
    )

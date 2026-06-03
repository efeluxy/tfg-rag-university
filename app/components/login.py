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
    st.session_state.selected_student = user_id
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.pending_message = None
    st.session_state.processing = False
    log_access(role, user_id, True, st.session_state.session_id)


def render_login() -> None:
    """Renderiza la pantalla de login como card centrada."""

    # Card centrada via columnas + contenedor con borde nativo
    _, col, _ = st.columns([1, 2, 1])

    with col:
      with st.container(border=True):
        # Cabecera
        st.markdown(
            """
            <div class="login-header">
              <div style="font-size:2.5rem; margin-bottom:8px;">🎓</div>
              <div class="login-title">Universidad Demo</div>
              <div class="login-subtitle">
                Asistente de Orientacion Universitaria<br>
                <span style="font-size:12px;">Identifica tu modo de acceso para continuar</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_alumno, tab_invitado, tab_admin = st.tabs(
            ["Alumno", "Invitado", "Administrador"]
        )

        # TAB 1: ALUMNO
        with tab_alumno:
            st.markdown(
                "<p style='color:var(--text-muted);font-size:13px;margin-bottom:12px;'>"
                "Acceso para estudiantes matriculados. "
                "Selecciona tu identidad e introduce la contrasena.</p>",
                unsafe_allow_html=True,
            )
            all_students = st.session_state.get("students_list", [])
            if not all_students:
                st.warning("No hay alumnos cargados en el sistema.")
            else:
                if "login_student_sort" not in st.session_state:
                    st.session_state["login_student_sort"] = "Numero"

                sort_choice = st.segmented_control(
                    label="Ordenar alumnos por",
                    options=["Numero", "Alfabetico"],
                    default=st.session_state.get("login_student_sort", "Numero"),
                    key="seg_login_student_sort",
                    selection_mode="single",
                )
                if sort_choice is None:
                    sort_choice = "Numero"
                st.session_state["login_student_sort"] = sort_choice

                if sort_choice == "Numero":
                    sorted_students = sorted(all_students, key=lambda s: s["id"])
                    labels = [f"{s['id']} — {s['name']}" for s in sorted_students]
                else:
                    sorted_students = sorted(all_students, key=lambda s: s["name"].lower())
                    labels = [f"{s['name']} ({s['id']})" for s in sorted_students]

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
                    "Acceder", key="btn_login_student",
                    use_container_width=True, type="primary"
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
                "<p style='color:var(--text-muted);font-size:13px;margin-bottom:16px;'>"
                "Acceso publico sin autenticacion. Podras consultar informacion general "
                "de la universidad (grados, becas, normativa, plazos administrativos). "
                "No tendras acceso a expedientes ni respuestas personalizadas.</p>",
                unsafe_allow_html=True,
            )
            if st.button(
                "Entrar como invitado", key="btn_login_guest",
                use_container_width=True, type="primary"
            ):
                _start_session("guest", None)
                st.rerun()

        # TAB 3: ADMINISTRADOR
        with tab_admin:
            st.markdown(
                "<p style='color:var(--text-muted);font-size:13px;margin-bottom:12px;'>"
                "Acceso administrativo. Permite consultar el sistema como si fueras "
                "cualquier alumno, para tareas de soporte y verificacion.</p>",
                unsafe_allow_html=True,
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
                type="primary",
            ):
                if authenticate_admin(password):
                    _start_session("admin", None)
                    st.rerun()
                else:
                    log_access("admin", None, False, None)
                    st.error("Contrasena incorrecta.")

        # Pie de página
        st.markdown(
            """
            <div class="login-footer">
              Sistema de demostracion academica (TFG 2026).<br>
              Las credenciales se almacenan localmente y los datos de alumnos son sinteticos.
            </div>
            """,
            unsafe_allow_html=True,
        )

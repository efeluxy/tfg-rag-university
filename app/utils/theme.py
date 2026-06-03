"""
Tema visual SaaS moderno (estilo Microsoft Copilot / Azure Portal).

- inject_theme_css(): inyecta las variables CSS de diseno en cada render.
- render_logout_sidebar(): boton Cerrar sesion al final de la columna izquierda.
"""

import streamlit as st

_PALETTE = {
    # Fondos
    "bg":              "#F8FAFC",
    "card":            "#FFFFFF",
    "bg-input":        "#FFFFFF",
    # Texto
    "text":            "#0F172A",
    "text-muted":      "#64748B",
    # Acciones
    "primary":         "#0078D4",
    "primary-hover":   "#106EBE",
    "secondary":       "#2563EB",
    # Bordes
    "border":          "#E2E8F0",
    "input-border":    "#CBD5E1",
    # Estados
    "success":         "#10B981",
    "warning":         "#F59E0B",
    "error":           "#EF4444",
    "error-hover":     "#DC2626",
    # Info / alerts
    "info-bg":         "#EFF6FF",
    "info-border":     "#0078D4",
    # Surface activa (segmented control)
    "surface-active":  "#E0EEFA",
    # Legacy aliases para componentes que aun usan var(--accent) etc.
    "accent":          "#0078D4",
    "accent-hover":    "#106EBE",
    "danger":          "#EF4444",
    "danger-hover":    "#DC2626",
    "bg-primary":      "#F8FAFC",
    "bg-secondary":    "#FFFFFF",
    "bg-tertiary":     "#F1F5F9",
    "text-primary":    "#0F172A",
    "text-secondary":  "#64748B",
}


def inject_theme_css():
    """Inyecta las variables CSS de diseno como :root vars."""
    css_vars = "\n".join(
        f"  --{k}: {v};" for k, v in _PALETTE.items()
    )
    st.markdown(
        f"<style>\n:root {{\n{css_vars}\n}}\n</style>",
        unsafe_allow_html=True,
    )


def render_logout_sidebar():
    """Boton Cerrar sesion al final de la columna izquierda del chat."""
    if not st.session_state.get("authenticated", False):
        return
    st.markdown(
        '<span id="logout-sidebar-anchor" style="display:none"></span>',
        unsafe_allow_html=True,
    )
    if st.button("Cerrar sesion", key="btn_logout_sidebar",
                 use_container_width=True):
        for k in list(st.session_state.keys()):
            if k not in ("privacy_accepted", "privacy_detailed_logs"):
                del st.session_state[k]
        st.rerun()

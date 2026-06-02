"""
Gestion del tema visual de la aplicacion (claro/oscuro).

Mantiene el tema activo en st.session_state["theme"] y expone:
- init_theme(): inicializa el tema por defecto (oscuro) si no existe.
- get_theme(): devuelve "dark" o "light".
- toggle_theme(): cambia entre claro y oscuro y fuerza rerun.
- inject_theme_css(): inyecta las variables CSS segun el tema activo.
- render_theme_toggle(): renderiza el boton flotante de toggle.
"""

import streamlit as st

THEME_DARK = "dark"
THEME_LIGHT = "light"
DEFAULT_THEME = THEME_DARK

PALETTES = {
    THEME_DARK: {
        "bg_primary": "#0e1117",
        "bg_secondary": "#1a1d24",
        "bg_tertiary": "#262730",
        "text_primary": "#fafafa",
        "text_secondary": "#c4c7cf",
        "text_muted": "#8a8d94",
        "border": "#3a3d44",
        "accent": "#4f8bff",
        "accent_hover": "#3a73e0",
        "danger": "#dc2626",
        "danger_hover": "#991b1b",
        "success": "#16a34a",
        "warning": "#eab308",
        "info_bg": "#1e3a5f",
        "info_border": "#3a73e0",
    },
    THEME_LIGHT: {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f4f6fa",
        "bg_tertiary": "#e7eaf0",
        "text_primary": "#1a1d24",
        "text_secondary": "#3a3d44",
        "text_muted": "#6b6e75",
        "border": "#d0d4dc",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "danger": "#dc2626",
        "danger_hover": "#991b1b",
        "success": "#16a34a",
        "warning": "#ca8a04",
        "info_bg": "#dbeafe",
        "info_border": "#2563eb",
    },
}


def init_theme():
    if "theme" not in st.session_state:
        st.session_state["theme"] = DEFAULT_THEME


def get_theme() -> str:
    init_theme()
    return st.session_state["theme"]


def toggle_theme():
    current = get_theme()
    st.session_state["theme"] = THEME_LIGHT if current == THEME_DARK else THEME_DARK


def inject_theme_css():
    theme = get_theme()
    palette = PALETTES[theme]
    css_vars = "\n".join(
        f"  --{k.replace('_', '-')}: {v};" for k, v in palette.items()
    )

    css = f"""
    <style>
    :root {{
{css_vars}
    }}

    /* App background */
    [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }}
    [data-testid="stHeader"] {{
        background-color: var(--bg-primary);
    }}
    /* Sidebar nativa de Streamlit (por si se usa en algun punto) */
    section[data-testid="stSidebar"] {{
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--text-primary);
    }}
    /* Inputs */
    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stChatInput textarea {{
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
        border-color: var(--border);
    }}
    /* Chat messages */
    [data-testid="stChatMessage"] {{
        background-color: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }}
    /* Markdown text in main area inherits primary text */
    [data-testid="stAppViewContainer"] .stMarkdown {{
        color: var(--text-primary);
    }}

    /* Toggle de tema: posicionado fijo en esquina superior derecha usando :has() */
    div[data-testid="stMarkdown"]:has(> #theme-toggle-anchor) {{
        position: fixed;
        top: 0;
        right: 0;
        height: 0;
        width: 0;
        z-index: 1000;
    }}
    div[data-testid="stMarkdown"]:has(> #theme-toggle-anchor) + div[data-testid="stButton"] {{
        position: fixed;
        top: 0.75rem;
        right: 1rem;
        z-index: 1000;
        width: auto;
    }}
    div[data-testid="stMarkdown"]:has(> #theme-toggle-anchor) + div[data-testid="stButton"] > button {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 999px !important;
        padding: 0.35rem 0.95rem !important;
        font-size: 0.85rem !important;
        cursor: pointer !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }}
    div[data-testid="stMarkdown"]:has(> #theme-toggle-anchor) + div[data-testid="stButton"] > button:hover {{
        background-color: var(--bg-secondary) !important;
    }}

    /* Responsive movil: toggle mas pequeno */
    @media (max-width: 640px) {{
        div[data-testid="stMarkdown"]:has(> #theme-toggle-anchor) + div[data-testid="stButton"] > button {{
            padding: 0.3rem 0.7rem !important;
            font-size: 0.8rem !important;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_theme_toggle():
    theme = get_theme()
    label = "Claro" if theme == THEME_DARK else "Oscuro"
    st.markdown(
        '<span id="theme-toggle-anchor" style="display:none"></span>',
        unsafe_allow_html=True,
    )
    if st.button(label, key="btn_theme_toggle"):
        toggle_theme()
        st.rerun()

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

    /* ============================================================
       FONDO Y CONTENEDORES GLOBALES
       ============================================================ */
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    .main .block-container {{
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }}
    [data-testid="stHeader"] {{
        background-color: var(--bg-primary) !important;
    }}
    [data-testid="stToolbar"] {{
        background-color: var(--bg-primary) !important;
    }}

    /* ============================================================
       SIDEBAR
       ============================================================ */
    section[data-testid="stSidebar"] {{
        background-color: var(--bg-secondary) !important;
        border-right: 1.5px solid var(--border) !important;
    }}
    section[data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-primary) !important;
    }}
    section[data-testid="stSidebar"] .student-header-sub {{
        color: var(--text-secondary) !important;
    }}
    section[data-testid="stSidebar"] .student-header-meta {{
        color: var(--text-muted) !important;
    }}

    /* ============================================================
       TIPOGRAFIA GENERAL EN AREA PRINCIPAL
       ============================================================ */
    .main .block-container,
    .main .block-container p,
    .main .block-container li,
    .main .block-container span,
    .main .block-container label,
    .main .block-container .stMarkdown,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span {{
        color: var(--text-primary) !important;
    }}
    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {{
        color: var(--text-primary) !important;
    }}

    /* ============================================================
       BOTONES
       ============================================================ */
    div[data-testid="stButton"] > button,
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
    }}
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background-color: var(--bg-secondary) !important;
        border-color: var(--accent) !important;
    }}
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {{
        background-color: var(--accent) !important;
        color: #ffffff !important;
        border-color: var(--accent) !important;
    }}
    div[data-testid="stButton"] > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {{
        background-color: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
    }}

    /* ============================================================
       INPUTS DE TEXTO Y CONTRASENA
       ============================================================ */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid var(--border) !important;
    }}
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }}
    [data-testid="stTextInput"] button {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }}

    /* ============================================================
       SELECTBOX Y DROPDOWNS
       ============================================================ */
    div[data-baseweb="select"] > div {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
    }}
    div[data-baseweb="select"] input {{
        color: var(--text-primary) !important;
    }}
    div[data-baseweb="popover"] ul {{
        background-color: var(--bg-secondary) !important;
        border: 1.5px solid var(--border) !important;
    }}
    div[data-baseweb="popover"] li {{
        color: var(--text-primary) !important;
        background-color: var(--bg-secondary) !important;
    }}
    div[data-baseweb="popover"] li:hover {{
        background-color: var(--bg-tertiary) !important;
    }}

    /* ============================================================
       RADIO BUTTONS
       ============================================================ */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] p {{
        color: var(--text-primary) !important;
    }}
    [data-baseweb="radio"] div {{
        background-color: transparent !important;
    }}

    /* ============================================================
       TABS
       ============================================================ */
    [data-baseweb="tab-list"] {{
        background-color: transparent !important;
        border-bottom: 1.5px solid var(--border) !important;
    }}
    [data-baseweb="tab"] {{
        color: var(--text-secondary) !important;
        background-color: transparent !important;
    }}
    [data-baseweb="tab"][aria-selected="true"] {{
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }}
    [data-baseweb="tab"]:hover {{
        color: var(--text-primary) !important;
    }}

    /* ============================================================
       CHAT MESSAGES
       ============================================================ */
    [data-testid="stChatMessage"] {{
        background-color: var(--bg-secondary) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
        color: var(--text-primary) !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] .stMarkdown {{
        color: var(--text-primary) !important;
        background-color: transparent !important;
    }}

    /* ============================================================
       LABELS DE FORMULARIO
       ============================================================ */
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    .stTextInput label,
    .stSelectbox label,
    .stRadio label > div,
    .stSelectbox label > div {{
        color: var(--text-primary) !important;
    }}

    /* ============================================================
       ALERTAS
       ============================================================ */
    [data-testid="stAlert"] {{
        background-color: var(--info-bg) !important;
        border: 1.5px solid var(--info-border) !important;
        color: var(--text-primary) !important;
    }}
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {{
        color: var(--text-primary) !important;
    }}

    /* ============================================================
       SCROLLBARS
       ============================================================ */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--bg-primary);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-muted);
    }}

    /* ============================================================
       MODAL (st.dialog)
       ============================================================ */
    [data-testid="stModal"] > div {{
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid var(--border) !important;
    }}
    [data-testid="stModal"] * {{
        color: var(--text-primary) !important;
    }}
    div[role="dialog"] {{
        background-color: var(--bg-secondary) !important;
    }}
    div[role="dialog"] * {{
        color: var(--text-primary) !important;
    }}

    /* ============================================================
       TOGGLE DE TEMA (esquina superior derecha)
       ============================================================ */
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
        border: 1.5px solid var(--border) !important;
        border-radius: 999px !important;
        padding: 0.35rem 0.95rem !important;
        font-size: 0.85rem !important;
        cursor: pointer !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }}
    div[data-testid="stMarkdown"]:has(> #theme-toggle-anchor) + div[data-testid="stButton"] > button:hover {{
        background-color: var(--bg-secondary) !important;
    }}

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

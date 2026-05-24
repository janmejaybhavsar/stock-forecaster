"""
Dark Fintech Theme — Global CSS and styling for the Stock Forecaster dashboard.
Inspired by TradingView / Robinhood aesthetic.
"""

import html as html_module

import streamlit as st


# Color palette
COLORS = {
    "bg_primary": "#0a0e17",
    "bg_secondary": "#131722",
    "bg_card": "#1c2030",
    "bg_card_hover": "#242938",
    "border": "#2a2e3e",
    "border_accent": "#00d4aa30",
    "text_primary": "#e8eaed",
    "text_secondary": "#8b8fa3",
    "text_muted": "#5d6175",
    "accent": "#00d4aa",
    "accent_glow": "#00d4aa40",
    "green": "#00d4aa",
    "green_soft": "#00d4aa20",
    "red": "#ff4757",
    "red_soft": "#ff475720",
    "yellow": "#ffa726",
    "yellow_soft": "#ffa72620",
    "blue": "#4fc3f7",
    "blue_soft": "#4fc3f720",
    "purple": "#b388ff",
}


def inject_custom_css():
    """Inject the global custom CSS into the Streamlit app."""
    st.markdown(f"""
    <style>
    /* ===== GLOBAL RESET & TYPOGRAPHY ===== */
    .stApp {{
        background-color: {COLORS["bg_primary"]};
    }}

    /* Hide default Streamlit header/footer */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: {COLORS["bg_primary"]};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {COLORS["border"]};
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS["text_muted"]};
    }}

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {{
        background-color: {COLORS["bg_secondary"]};
        border-right: 1px solid {COLORS["border"]};
    }}

    [data-testid="stSidebar"] .stMarkdown p {{
        color: {COLORS["text_secondary"]};
    }}

    /* ===== NAVIGATION (st.navigation) ===== */
    [data-testid="stSidebarNav"] {{
        padding: 0 0 4px 0;
    }}

    /* Navigation group headers */
    [data-testid="stSidebarNav"] span[data-testid="stHeaderActionElements"],
    [data-testid="stSidebarNav"] header {{
        margin-top: 4px !important;
        margin-bottom: 0 !important;
    }}

    /* Navigation links */
    [data-testid="stSidebarNav"] a {{
        color: {COLORS["text_secondary"]} !important;
        border-radius: 6px !important;
        padding: 5px 10px !important;
        margin: 0 !important;
        transition: all 0.15s ease !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        text-decoration: none !important;
    }}

    [data-testid="stSidebarNav"] a:hover {{
        background: {COLORS["bg_card"]} !important;
        color: {COLORS["text_primary"]} !important;
    }}

    [data-testid="stSidebarNav"] a[aria-current="page"],
    [data-testid="stSidebarNav"] a.active {{
        background: {COLORS["accent"]}15 !important;
        color: {COLORS["accent"]} !important;
        font-weight: 600 !important;
    }}

    /* Navigation icons */
    [data-testid="stSidebarNav"] a span[data-testid="stIconMaterial"] {{
        color: inherit !important;
        font-size: 1rem !important;
    }}

    /* Compact sidebar inputs */
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stDateInput label {{
        font-size: 0.8rem !important;
        color: {COLORS["text_secondary"]} !important;
    }}

    /* ===== METRICS ===== */
    [data-testid="stMetric"] {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 16px 20px;
    }}

    [data-testid="stMetricLabel"] {{
        color: {COLORS["text_secondary"]} !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    [data-testid="stMetricValue"] {{
        color: {COLORS["text_primary"]} !important;
        font-weight: 700 !important;
    }}

    /* ===== BUTTONS ===== */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS["accent"]}20, {COLORS["accent"]}10);
        border: 1px solid {COLORS["accent"]}60;
        color: {COLORS["accent"]};
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, {COLORS["accent"]}40, {COLORS["accent"]}20);
        border-color: {COLORS["accent"]};
        box-shadow: 0 0 20px {COLORS["accent_glow"]};
    }}

    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS["accent"]}, #00b894);
        color: #0a0e17;
        border: none;
        font-weight: 700;
    }}

    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 0 30px {COLORS["accent_glow"]};
        transform: translateY(-1px);
    }}

    /* ===== EXPANDERS ===== */
    [data-testid="stExpander"] {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        overflow: hidden;
    }}

    [data-testid="stExpander"] summary {{
        color: {COLORS["text_primary"]};
        font-weight: 600;
    }}

    /* ===== INPUTS ===== */
    .stTextInput > div > div {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        color: {COLORS["text_primary"]};
    }}

    .stTextInput > div > div:focus-within {{
        border-color: {COLORS["accent"]};
        box-shadow: 0 0 0 2px {COLORS["accent_glow"]};
    }}

    .stSelectbox > div > div {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
    }}

    /* ===== DATAFRAMES / TABLES ===== */
    [data-testid="stDataFrame"] {{
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div {{
        background: {COLORS["bg_card"]};
        border-radius: 10px;
    }}

    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {COLORS["accent"]}, #00b894);
        border-radius: 10px;
    }}

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0px;
        background: {COLORS["bg_card"]};
        border-radius: 10px;
        padding: 4px;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        color: {COLORS["text_secondary"]};
        font-weight: 500;
    }}

    .stTabs [aria-selected="true"] {{
        background: {COLORS["accent"]}20;
        color: {COLORS["accent"]} !important;
    }}

    /* ===== CONTAINERS / CARDS ===== */
    [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {{
    }}

    div[data-testid="stContainer"] {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 1rem;
    }}

    /* ===== ALERTS ===== */
    .stAlert {{
        border-radius: 10px;
        border: none;
    }}

    /* ===== DIVIDERS ===== */
    hr {{
        border-color: {COLORS["border"]} !important;
        opacity: 0.5;
    }}

    /* ===== CHAT ===== */
    [data-testid="stChatMessage"] {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 1rem;
    }}

    /* ===== CHECKBOX ===== */
    .stCheckbox label span {{
        color: {COLORS["text_primary"]};
    }}

    /* ===== PAGE LINKS ===== */
    a {{
        color: {COLORS["accent"]} !important;
    }}

    /* ===== PLOTLY CHARTS ===== */
    .js-plotly-plot .plotly .modebar {{
        background: transparent !important;
    }}

    </style>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = "", delta_color: str = "green") -> str:
    """Render a custom metric card as HTML."""
    delta_html = ""
    if delta:
        color = COLORS[delta_color] if delta_color in COLORS else delta_color
        arrow = "↑" if not delta.startswith("-") else "↓"
        delta_html = f'<div style="color:{color}; font-size:0.85rem; margin-top:4px;">{arrow} {delta}</div>'

    return f"""
    <div style="
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 20px 24px;
        text-align: left;
    ">
        <div style="color:{COLORS["text_secondary"]}; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px;">{label}</div>
        <div style="color:{COLORS["text_primary"]}; font-size:1.5rem; font-weight:700;">{value}</div>
        {delta_html}
    </div>
    """


def signal_badge(label: str, color: str, size: str = "large") -> str:
    """Render a signal badge (STRONG BUY, SELL, etc.)."""
    if size == "large":
        font_size = "2rem"
        padding = "16px 32px"
    else:
        font_size = "0.85rem"
        padding = "6px 14px"

    return f"""
    <div style="
        display: inline-block;
        background: {color}15;
        border: 2px solid {color};
        border-radius: 12px;
        padding: {padding};
        text-align: center;
        box-shadow: 0 0 20px {color}20;
    ">
        <span style="color:{color}; font-size:{font_size}; font-weight:800; letter-spacing:1px;">{label}</span>
    </div>
    """


def notification_card(icon: str, message: str, priority: str = "medium") -> str:
    """Render a notification card with priority styling."""
    styles = {
        "high": f"border-left: 4px solid {COLORS['red']}; background: {COLORS['red_soft']};",
        "medium": f"border-left: 4px solid {COLORS['yellow']}; background: {COLORS['yellow_soft']};",
        "low": f"border-left: 4px solid {COLORS['green']}; background: {COLORS['green_soft']};",
    }
    style = styles.get(priority, styles["medium"])
    safe_icon = html_module.escape(icon)
    safe_message = html_module.escape(message)
    return f"""
    <div style="{style} padding: 12px 16px; border-radius: 8px; margin-bottom: 8px;">
        <span style="color:{COLORS['text_primary']};">{safe_icon} {safe_message}</span>
    </div>
    """


def section_header(title: str, subtitle: str = "") -> str:
    """Render a styled section header."""
    sub_html = f'<div style="color:{COLORS["text_muted"]}; font-size:0.85rem; margin-top:4px;">{subtitle}</div>' if subtitle else ""
    return f"""
    <div style="margin: 1.5rem 0 1rem 0;">
        <h3 style="color:{COLORS["text_primary"]}; margin:0; font-weight:700;">{title}</h3>
        {sub_html}
    </div>
    """


def stat_row(items: list[tuple[str, str, str]]) -> str:
    """Render a row of stats. items = [(label, value, color), ...]"""
    cols = ""
    for label, value, color in items:
        cols += f"""
        <div style="flex:1; text-align:center; padding: 12px;">
            <div style="color:{COLORS["text_muted"]}; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.5px;">{label}</div>
            <div style="color:{color}; font-size:1.2rem; font-weight:700; margin-top:4px;">{value}</div>
        </div>
        """
    return f"""
    <div style="display:flex; background:{COLORS["bg_card"]}; border:1px solid {COLORS["border"]}; border-radius:12px; overflow:hidden;">
        {cols}
    </div>
    """

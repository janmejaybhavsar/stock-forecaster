"""
Reusable UI helpers: loading states, error boundaries, responsive layouts.
"""

import streamlit as st
from src.dashboard.components.theme import COLORS


def loading_skeleton(lines: int = 3, height: str = "1.2rem"):
    """Render animated shimmer loading placeholders."""
    shimmer_css = f"""
    <style>
    @keyframes shimmer {{
        0% {{ background-position: -200px 0; }}
        100% {{ background-position: 200px 0; }}
    }}
    .skeleton-line {{
        background: linear-gradient(90deg, {COLORS['bg_card']} 25%, {COLORS['bg_card_hover']} 50%, {COLORS['bg_card']} 75%);
        background-size: 400px 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 6px;
        height: {height};
        margin-bottom: 8px;
    }}
    </style>
    """
    skeleton_html = shimmer_css + "".join(
        f'<div class="skeleton-line" style="width:{90 - i * 10}%;"></div>'
        for i in range(lines)
    )
    st.markdown(skeleton_html, unsafe_allow_html=True)


def loading_card_skeleton(count: int = 4):
    """Render skeleton metric cards."""
    cols = st.columns(count)
    for col in cols:
        with col:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px 24px;
                min-height: 80px;
            ">
                <div class="skeleton-line" style="width:60%; height:0.7rem; margin-bottom:12px;
                    background: linear-gradient(90deg, {COLORS['bg_card']} 25%, {COLORS['bg_card_hover']} 50%, {COLORS['bg_card']} 75%);
                    background-size: 400px 100%; animation: shimmer 1.5s infinite; border-radius: 4px;"></div>
                <div class="skeleton-line" style="width:80%; height:1.5rem;
                    background: linear-gradient(90deg, {COLORS['bg_card']} 25%, {COLORS['bg_card_hover']} 50%, {COLORS['bg_card']} 75%);
                    background-size: 400px 100%; animation: shimmer 1.5s infinite; border-radius: 4px;"></div>
            </div>
            """, unsafe_allow_html=True)


def error_card(title: str, message: str, suggestion: str = ""):
    """Render a styled error card instead of crashing the page."""
    suggestion_html = f'<p style="color:{COLORS["text_muted"]}; font-size:0.8rem; margin-top:8px;">{suggestion}</p>' if suggestion else ""
    st.markdown(f"""
    <div style="
        background: {COLORS['red_soft']};
        border: 1px solid {COLORS['red']}40;
        border-radius: 12px;
        padding: 20px 24px;
    ">
        <div style="color:{COLORS['red']}; font-weight:700; font-size:0.9rem; margin-bottom:6px;">{title}</div>
        <div style="color:{COLORS['text_secondary']}; font-size:0.85rem;">{message}</div>
        {suggestion_html}
    </div>
    """, unsafe_allow_html=True)


def empty_state(icon: str, title: str, subtitle: str = ""):
    """Render a clean empty state placeholder."""
    sub_html = f'<p style="color:{COLORS["text_muted"]}; font-size:0.85rem; margin-top:8px;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 48px;
        text-align: center;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">{icon}</div>
        <p style="color:{COLORS['text_secondary']}; font-size:1.1rem; margin:0;">{title}</p>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def responsive_columns(items: int) -> list:
    """Return columns that adapt: 4 on desktop, 2 on narrow viewports.
    Streamlit doesn't expose viewport width, so we use a balanced approach:
    - 4+ items: use min(items, 4) columns
    - 2-3 items: use exact count
    - 1 item: single column
    """
    if items <= 0:
        return [st.container()]
    count = min(items, 4)
    return st.columns(count)


def status_badge(label: str, color: str) -> str:
    """Return HTML for a small status badge."""
    return f"""
    <span style="
        display: inline-block;
        background: {color}15;
        border: 1px solid {color}40;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        color: {color};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    ">{label}</span>
    """

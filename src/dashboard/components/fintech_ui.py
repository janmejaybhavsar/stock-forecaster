"""
Fintech UX patterns — sparklines, donut charts, animated P&L, toasts, onboarding, keyboard shortcuts.
"""

import math
import time as _time

import streamlit as st
from src.dashboard.components.theme import COLORS


# ─── Sparkline (inline SVG mini-chart) ─────────────────────────────────────

def sparkline_svg(prices: list[float], width: int = 80, height: int = 24, color: str | None = None) -> str:
    """Generate an inline SVG sparkline from a list of prices.

    Args:
        prices: list of price values (at least 2 points)
        width: SVG width in pixels
        height: SVG height in pixels
        color: override color (auto-detects green/red from trend)
    """
    if not prices or len(prices) < 2:
        return ""

    if color is None:
        color = COLORS["green"] if prices[-1] >= prices[0] else COLORS["red"]

    min_p = min(prices)
    max_p = max(prices)
    price_range = max_p - min_p if max_p != min_p else 1

    # Normalize to SVG coords (y is inverted)
    padding = 2
    usable_w = width - padding * 2
    usable_h = height - padding * 2

    points = []
    for i, p in enumerate(prices):
        x = padding + (i / (len(prices) - 1)) * usable_w
        y = padding + (1 - (p - min_p) / price_range) * usable_h
        points.append(f"{x:.1f},{y:.1f}")

    polyline_points = " ".join(points)

    # Gradient fill area
    fill_points = f"{points[0]} {polyline_points} {points[-1].split(',')[0]},{height} {padding},{height}"

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="display:inline-block; vertical-align:middle;">
        <defs>
            <linearGradient id="sg_{id(prices)}" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
            </linearGradient>
        </defs>
        <polygon points="{fill_points}" fill="url(#sg_{id(prices)})"/>
        <polyline points="{polyline_points}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""


# ─── Donut Chart (pure SVG, no Plotly) ──────────────────────────────────────

def donut_chart_svg(
    labels: list[str],
    values: list[float],
    colors: list[str] | None = None,
    size: int = 280,
    center_label: str = "",
    center_value: str = "",
) -> str:
    """Render a donut/ring chart as inline SVG.

    Args:
        labels: slice labels
        values: slice values (proportional)
        colors: optional custom colors per slice
        size: SVG size in pixels
        center_label: text shown in the center (small)
        center_value: large text shown in the center
    """
    if not values or sum(values) == 0:
        return ""

    if colors is None:
        palette = [COLORS["accent"], COLORS["blue"], COLORS["yellow"], COLORS["red"],
                   COLORS["purple"], "#26c6da", "#ff8a65", "#a5d6a7", "#ce93d8", "#80cbc4"]
        colors = [palette[i % len(palette)] for i in range(len(values))]

    total = sum(values)
    cx, cy = size / 2, size / 2
    r_outer = size * 0.42
    r_inner = size * 0.28
    stroke_width = r_outer - r_inner

    paths = []
    legend_items = []
    angle = -90  # Start at top

    for i, (label, value) in enumerate(zip(labels, values)):
        if value <= 0:
            continue
        pct = value / total
        sweep = pct * 360

        # For the arc, use the middle radius
        r_mid = (r_outer + r_inner) / 2
        # Calculate arc
        start_angle_rad = angle * 3.14159 / 180
        end_angle_rad = (angle + sweep) * 3.14159 / 180

        x1 = cx + r_mid * math.cos(start_angle_rad)
        y1 = cy + r_mid * math.sin(start_angle_rad)
        x2 = cx + r_mid * math.cos(end_angle_rad)
        y2 = cy + r_mid * math.sin(end_angle_rad)

        large_arc = 1 if sweep > 180 else 0

        path = f'<path d="M {x1:.2f} {y1:.2f} A {r_mid:.2f} {r_mid:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f}" fill="none" stroke="{colors[i]}" stroke-width="{stroke_width:.1f}" stroke-linecap="butt"/>'
        paths.append(path)

        # Legend
        legend_items.append(f"""
            <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                <div style="width:10px; height:10px; border-radius:50%; background:{colors[i]};"></div>
                <span style="color:{COLORS['text_secondary']}; font-size:0.75rem;">{label}</span>
                <span style="color:{COLORS['text_muted']}; font-size:0.7rem; margin-left:auto;">{pct*100:.1f}%</span>
            </div>
        """)

        angle += sweep

    # Center text
    center_html = ""
    if center_value:
        center_html += f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" fill="{COLORS["text_primary"]}" font-size="1.3rem" font-weight="700">{center_value}</text>'
    if center_label:
        center_html += f'<text x="{cx}" y="{cy + 16}" text-anchor="middle" fill="{COLORS["text_muted"]}" font-size="0.65rem">{center_label}</text>'

    svg = f"""
    <div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap;">
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
            {''.join(paths)}
            {center_html}
        </svg>
        <div style="flex:1; min-width:120px;">
            {''.join(legend_items)}
        </div>
    </div>
    """
    return svg


# ─── Color-coded P&L with animation ────────────────────────────────────────

def animated_pnl(value: float, pct: float | None = None, size: str = "normal") -> str:
    """Render a P&L value with color and subtle pulse animation on load.

    Args:
        value: P&L dollar amount
        pct: optional percentage
        size: 'small', 'normal', or 'large'
    """
    color = COLORS["green"] if value >= 0 else COLORS["red"]
    bg = COLORS["green_soft"] if value >= 0 else COLORS["red_soft"]
    arrow = "▲" if value >= 0 else "▼"

    sizes = {
        "small": ("0.85rem", "4px 8px"),
        "normal": ("1.05rem", "6px 12px"),
        "large": ("1.4rem", "8px 16px"),
    }
    font_size, padding = sizes.get(size, sizes["normal"])

    pct_html = f'<span style="font-size:0.8em; opacity:0.85;"> ({pct:+.1f}%)</span>' if pct is not None else ""

    return f"""
    <span class="pnl-animated" style="
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: {bg};
        color: {color};
        font-weight: 700;
        font-size: {font_size};
        padding: {padding};
        border-radius: 6px;
        animation: pnl-pop 0.4s ease-out;
    ">
        <span style="font-size:0.7em;">{arrow}</span>
        ${abs(value):,.2f}{pct_html}
    </span>
    """


def inject_pnl_animation_css():
    """Inject the CSS keyframes for P&L animation (call once per page)."""
    st.markdown("""
    <style>
    @keyframes pnl-pop {
        0% { transform: scale(0.8); opacity: 0; }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)


# ─── Notification Toasts ──────���─────────────────────────────────────────────

def toast(message: str, type: str = "info", duration: int = 4000):
    """Display a toast notification that auto-dismisses.

    Args:
        message: toast message text
        type: 'success', 'error', 'warning', 'info'
        duration: milliseconds before auto-dismiss
    """
    colors_map = {
        "success": (COLORS["green"], COLORS["green_soft"], "✓"),
        "error": (COLORS["red"], COLORS["red_soft"], "✕"),
        "warning": (COLORS["yellow"], COLORS["yellow_soft"], "⚠"),
        "info": (COLORS["blue"], COLORS["blue_soft"], "ℹ"),
    }
    color, bg, icon = colors_map.get(type, colors_map["info"])

    # Unique ID for this toast
    toast_id = f"toast_{int(_time.time() * 1000)}"

    st.markdown(f"""
    <div id="{toast_id}" style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 999999;
        background: {COLORS['bg_card']};
        border: 1px solid {color}40;
        border-left: 4px solid {color};
        border-radius: 10px;
        padding: 14px 20px;
        min-width: 280px;
        max-width: 400px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        animation: toast-slide-in 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 10px;
    ">
        <span style="color:{color}; font-size:1.1rem;">{icon}</span>
        <span style="color:{COLORS['text_primary']}; font-size:0.88rem; flex:1;">{message}</span>
    </div>
    <style>
    @keyframes toast-slide-in {{
        from {{ transform: translateX(100%); opacity: 0; }}
        to {{ transform: translateX(0); opacity: 1; }}
    }}
    @keyframes toast-slide-out {{
        from {{ transform: translateX(0); opacity: 1; }}
        to {{ transform: translateX(100%); opacity: 0; }}
    }}
    </style>
    <script>
    setTimeout(function() {{
        var el = document.getElementById('{toast_id}');
        if (el) {{
            el.style.animation = 'toast-slide-out 0.3s ease-in forwards';
            setTimeout(function() {{ el.remove(); }}, 300);
        }}
    }}, {duration});
    </script>
    """, unsafe_allow_html=True)


# ─── Onboarding Tour ───────────────────────────────────────────────────────

def onboarding_tour(steps: list[dict], key: str = "onboarding_complete"):
    """Show a first-time user onboarding walkthrough overlay.

    Args:
        steps: list of dicts with 'title', 'description', 'icon' keys
        key: session_state key to track completion
    """
    if st.session_state.get(key, False):
        return

    # Initialize step tracker
    step_key = f"{key}_step"
    if step_key not in st.session_state:
        st.session_state[step_key] = 0

    current_step = st.session_state[step_key]

    if current_step >= len(steps):
        st.session_state[key] = True
        return

    step = steps[current_step]
    total = len(steps)

    # Progress dots
    dots_html = " ".join(
        f'<span style="width:8px; height:8px; border-radius:50%; background:{COLORS["accent"] if i == current_step else COLORS["border"]}; display:inline-block;"></span>'
        for i in range(total)
    )

    st.markdown(f"""
    <div style="
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['accent']}40;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px {COLORS['accent']}10;
    ">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
            <span style="font-size:1.6rem;">{step.get('icon', '👋')}</span>
            <span style="color:{COLORS['text_muted']}; font-size:0.75rem;">Step {current_step + 1} of {total}</span>
        </div>
        <h3 style="color:{COLORS['text_primary']}; margin:0 0 8px 0; font-size:1.15rem;">{step['title']}</h3>
        <p style="color:{COLORS['text_secondary']}; font-size:0.9rem; margin:0 0 16px 0; line-height:1.5;">{step['description']}</p>
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; gap:6px;">{dots_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if current_step > 0:
            if st.button("← Back", key=f"tour_back_{current_step}"):
                st.session_state[step_key] = current_step - 1
                st.rerun()
    with col3:
        if current_step < total - 1:
            if st.button("Next →", key=f"tour_next_{current_step}", type="primary"):
                st.session_state[step_key] = current_step + 1
                st.rerun()
        else:
            if st.button("Get Started!", key=f"tour_done_{current_step}", type="primary"):
                st.session_state[key] = True
                st.rerun()
    with col2:
        if st.button("Skip tour", key=f"tour_skip_{current_step}"):
            st.session_state[key] = True
            st.rerun()


# ─── Keyboard Shortcuts ─────────────────────────────────────────────────────

def inject_keyboard_shortcuts():
    """Inject global keyboard shortcuts via JavaScript.

    Shortcuts:
    - Ctrl+K / Cmd+K: Focus search/ticker input
    - Ctrl+1-9: Navigate to pages
    - Escape: Close modals/expanders
    """
    st.markdown("""
    <style>
    .shortcut-help {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 99998;
        background: """ + COLORS['bg_card'] + """;
        border: 1px solid """ + COLORS['border'] + """;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        display: none;
        min-width: 240px;
    }
    .shortcut-help.visible { display: block; animation: toast-slide-in 0.2s ease-out; }
    .shortcut-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
    }
    .shortcut-row span:first-child {
        color: """ + COLORS['text_secondary'] + """;
        font-size: 0.8rem;
    }
    .kbd {
        background: """ + COLORS['bg_secondary'] + """;
        border: 1px solid """ + COLORS['border'] + """;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 0.7rem;
        color: """ + COLORS['text_primary'] + """;
        font-family: monospace;
    }
    </style>
    <div class="shortcut-help" id="shortcut-help">
        <div style="color:""" + COLORS['text_primary'] + """; font-weight:700; font-size:0.85rem; margin-bottom:8px;">Keyboard Shortcuts</div>
        <div class="shortcut-row"><span>Search ticker</span><span class="kbd">Ctrl+K</span></div>
        <div class="shortcut-row"><span>Show shortcuts</span><span class="kbd">?</span></div>
        <div class="shortcut-row"><span>Close</span><span class="kbd">Esc</span></div>
    </div>
    <script>
    (function() {
        let helpVisible = false;
        document.addEventListener('keydown', function(e) {
            // Ctrl+K or Cmd+K: focus ticker input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const inputs = document.querySelectorAll('input[type="text"]');
                if (inputs.length > 0) inputs[0].focus();
            }
            // ? key: toggle shortcut help
            if (e.key === '?' && !e.ctrlKey && !e.metaKey && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                helpVisible = !helpVisible;
                document.getElementById('shortcut-help').classList.toggle('visible', helpVisible);
            }
            // Escape: close help
            if (e.key === 'Escape') {
                helpVisible = false;
                document.getElementById('shortcut-help').classList.remove('visible');
            }
        });
    })();
    </script>
    """, unsafe_allow_html=True)


# ─── Holdings Table Row with Sparkline ──────────────────────────────────────

def holding_row_html(
    ticker: str,
    shares: float,
    avg_cost: float,
    current_price: float,
    market_value: float,
    pnl: float,
    pnl_pct: float,
    sparkline_prices: list[float] | None = None,
) -> str:
    """Render a single holding row with sparkline and animated P&L."""
    pnl_color = COLORS["green"] if pnl >= 0 else COLORS["red"]
    pnl_bg = COLORS["green_soft"] if pnl >= 0 else COLORS["red_soft"]
    arrow = "▲" if pnl >= 0 else "▼"

    spark_html = ""
    if sparkline_prices:
        spark_html = sparkline_svg(sparkline_prices, width=72, height=28)

    return f"""
    <div style="
        display:flex; align-items:center; justify-content:space-between;
        background:{COLORS['bg_card']}; border:1px solid {COLORS['border']};
        border-radius:10px; padding:16px 20px; margin-bottom:8px;
        transition: border-color 0.2s ease;
    " onmouseover="this.style.borderColor='{COLORS['accent']}40'" onmouseout="this.style.borderColor='{COLORS['border']}'">
        <div style="min-width:100px;">
            <div style="color:{COLORS['text_primary']}; font-weight:700; font-size:1.05rem;">{ticker}</div>
            <div style="color:{COLORS['text_muted']}; font-size:0.78rem;">{shares} shares @ ${avg_cost:.2f}</div>
        </div>
        <div style="flex-shrink:0;">{spark_html}</div>
        <div style="display:flex; align-items:center; gap:24px;">
            <div style="text-align:right;">
                <div style="color:{COLORS['text_primary']}; font-weight:600;">${current_price:,.2f}</div>
                <div style="color:{COLORS['text_muted']}; font-size:0.72rem;">Price</div>
            </div>
            <div style="text-align:right;">
                <div style="color:{COLORS['text_primary']}; font-weight:600;">${market_value:,.2f}</div>
                <div style="color:{COLORS['text_muted']}; font-size:0.72rem;">Value</div>
            </div>
            <div style="text-align:right;">
                <div class="pnl-animated" style="
                    color:{pnl_color}; font-weight:700;
                    background:{pnl_bg}; padding:3px 8px; border-radius:5px;
                    animation: pnl-pop 0.4s ease-out;
                ">
                    {arrow} ${abs(pnl):,.2f}
                </div>
                <div style="color:{pnl_color}; font-size:0.72rem; margin-top:2px;">{pnl_pct:+.1f}%</div>
            </div>
        </div>
    </div>
    """

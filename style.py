import streamlit as st

FONT_LINK = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Lato:wght@300;400;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
"""

COFFEE_CSS = """
<style>
* { box-sizing: border-box; }

html, body {
    font-family: 'Lato', sans-serif !important;
    background: #1a0f07 !important;
}

[class*="css"], .stApp, .main {
    font-family: 'Lato', sans-serif !important;
    background: #1a0f07 !important;
    color: #f0e6d3 !important;
}

.stApp {
    background: #1a0f07 !important;
    background-image:
        radial-gradient(ellipse at 10% 10%, rgba(200,150,62,0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 90%, rgba(111,78,55,0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(160,100,40,0.03) 0%, transparent 70%) !important;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

header,
header[data-testid="stHeader"],
[data-testid="stHeader"],
.stApp > header,
div[class*="stAppHeader"],
div[class*="AppHeader"],
[data-testid="stAppViewContainer"] > header {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border-bottom: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}

header::before, header::after,
[data-testid="stHeader"]::before,
[data-testid="stHeader"]::after {
    background: transparent !important;
    display: none !important;
}

[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stStatusWidget"] {
    background: transparent !important;
    background-color: transparent !important;
}

[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

.block-container {
    padding: 1.5rem 2.5rem 3rem 2.5rem !important;
    max-width: 1440px !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0804 0%, #1a0f07 40%, #120b05 100%) !important;
    border-right: 1px solid rgba(200,150,62,0.18) !important;
    box-shadow: 4px 0 30px rgba(111,78,55,0.12) !important;
}

[data-testid="stSidebarNav"] a {
    border-radius: 6px !important;
    padding: 0.5rem 0.8rem !important;
    font-family: 'Lato', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    color: #8a7060 !important;
    margin: 2px 0 !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
    text-transform: none !important;
}

[data-testid="stSidebarNav"] a:hover {
    background: rgba(200,150,62,0.08) !important;
    color: #C8963E !important;
    border-color: rgba(200,150,62,0.2) !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(90deg, rgba(200,150,62,0.15), rgba(200,150,62,0.04)) !important;
    color: #C8963E !important;
    border-left: 2px solid #C8963E !important;
    box-shadow: 0 0 15px rgba(200,150,62,0.08) !important;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown div {
    color: #8a7060 !important;
    font-family: 'Lato', sans-serif !important;
    font-size: 0.82rem !important;
}

[data-testid="collapsedControl"] { display: flex !important; visibility: visible !important; }

h1, h2, h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    font-family: 'Playfair Display', serif !important;
    letter-spacing: 0.01em !important;
}

h1, [data-testid="stMarkdownContainer"] h1 {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #f0e6d3 !important;
    margin-bottom: 0.25rem !important;
}

h2, [data-testid="stMarkdownContainer"] h2 {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: #d4b896 !important;
}

h3, [data-testid="stMarkdownContainer"] h3 {
    font-size: 1.0rem !important;
    font-weight: 600 !important;
    color: #b8956e !important;
}

p, li { color: #b8956e; line-height: 1.7; }

.coffee-kpi-card {
    background: linear-gradient(135deg, rgba(30,18,10,0.97) 0%, rgba(20,12,6,0.97) 100%);
    border: 1px solid rgba(200,150,62,0.12);
    border-left: 3px solid;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}

.coffee-kpi-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(200,150,62,0.04) 0%, transparent 60%);
    pointer-events: none;
}

.coffee-kpi-card:hover { transform: translateY(-3px); }

.coffee-kpi-icon { font-size: 1.4rem; margin-bottom: 0.5rem; display: block; }

.coffee-kpi-label {
    font-family: 'Lato', sans-serif !important;
    font-size: 0.67rem;
    font-weight: 700;
    color: #6b5040;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.4rem;
    display: block;
}

.coffee-kpi-value {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.55rem;
    font-weight: 700;
    line-height: 1;
    display: block;
}

.coffee-kpi-delta {
    font-family: 'Lato', sans-serif;
    font-size: 0.72rem;
    color: #6b5040;
    margin-top: 0.4rem;
    display: block;
}

.coffee-section-header {
    font-family: 'Lato', sans-serif !important;
    font-size: 0.7rem;
    font-weight: 700;
    color: #C8963E;
    margin: 2rem 0 0.9rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid rgba(200,150,62,0.18);
    letter-spacing: 0.18em;
    text-transform: uppercase;
}

.coffee-chart-label {
    font-family: 'Playfair Display', serif !important;
    font-size: 0.98rem;
    font-weight: 600;
    color: #d4b896;
    margin-bottom: 0.2rem;
    letter-spacing: 0.01em;
}

.coffee-chart-sub {
    font-family: 'Lato', sans-serif;
    font-size: 0.72rem;
    color: #6b5040;
    margin-bottom: 0.5rem;
}

.coffee-insight {
    border-left: 3px solid;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.65rem;
    font-size: 0.875rem;
    line-height: 1.7;
    color: #b8956e;
    backdrop-filter: blur(4px);
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(30,18,10,0.97), rgba(20,12,6,0.97)) !important;
    border: 1px solid rgba(200,150,62,0.12) !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
    transition: transform 0.2s ease !important;
}

[data-testid="stMetric"]:hover { transform: translateY(-2px) !important; }

[data-testid="stMetricLabel"] {
    font-family: 'Lato', sans-serif !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    color: #6b5040 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: #f0e6d3 !important;
}

.stButton > button {
    font-family: 'Lato', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    background: rgba(20,12,6,0.9) !important;
    color: #8a7060 !important;
    border: 1px solid rgba(200,150,62,0.2) !important;
    border-radius: 6px !important;
    font-size: 0.82rem !important;
    padding: 0.45rem 1.1rem !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: rgba(200,150,62,0.10) !important;
    border-color: #C8963E !important;
    color: #C8963E !important;
    box-shadow: 0 0 15px rgba(200,150,62,0.15) !important;
}

.stTextInput > div > div > input,
.stDateInput > div > div > input {
    background: rgba(20,12,6,0.9) !important;
    border: 1px solid rgba(200,150,62,0.18) !important;
    border-radius: 6px !important;
    color: #f0e6d3 !important;
    font-family: 'Lato', sans-serif !important;
    font-size: 0.9rem !important;
}

.stSelectbox > div > div {
    background: rgba(20,12,6,0.9) !important;
    border: 1px solid rgba(200,150,62,0.18) !important;
    border-radius: 6px !important;
    color: #f0e6d3 !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid rgba(200,150,62,0.12) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] {
    background: rgba(20,12,6,0.8) !important;
    border: 1px solid rgba(200,150,62,0.12) !important;
    border-radius: 10px !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(20,12,6,0.9);
    border-radius: 8px;
    padding: 3px;
    gap: 3px;
    border: 1px solid rgba(200,150,62,0.12);
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Lato', sans-serif !important;
    background: transparent !important;
    color: #6b5040 !important;
    border-radius: 6px !important;
    padding: 0.35rem 1rem !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(200,150,62,0.12) !important;
    color: #C8963E !important;
}

.stDownloadButton > button {
    font-family: 'Lato', sans-serif !important;
    font-weight: 700 !important;
    background: rgba(111,78,55,0.15) !important;
    color: #C8963E !important;
    border: 1px solid rgba(200,150,62,0.25) !important;
    border-radius: 6px !important;
}

.stDownloadButton > button:hover {
    background: rgba(200,150,62,0.2) !important;
    border-color: #C8963E !important;
    box-shadow: 0 0 12px rgba(200,150,62,0.2) !important;
}

.stSuccess {
    background: rgba(16,185,129,0.07) !important;
    border: 1px solid rgba(16,185,129,0.2) !important;
    border-radius: 8px !important;
}
.stInfo {
    background: rgba(200,150,62,0.07) !important;
    border: 1px solid rgba(200,150,62,0.18) !important;
    border-radius: 8px !important;
}
.stWarning {
    background: rgba(245,158,11,0.07) !important;
    border: 1px solid rgba(245,158,11,0.18) !important;
    border-radius: 8px !important;
}
.stError {
    background: rgba(239,68,68,0.07) !important;
    border: 1px solid rgba(239,68,68,0.18) !important;
    border-radius: 8px !important;
}

hr {
    border: none !important;
    border-top: 1px solid rgba(200,150,62,0.10) !important;
    margin: 1.5rem 0 !important;
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #1a0f07; }
::-webkit-scrollbar-thumb { background: rgba(200,150,62,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(200,150,62,0.5); }

[data-testid="stFileUploader"] {
    background: rgba(20,12,6,0.8) !important;
    border: 2px dashed rgba(200,150,62,0.25) !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    transition: border-color 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(200,150,62,0.5) !important;
}

[data-testid="stSlider"] [role="slider"] {
    background: #C8963E !important;
    box-shadow: 0 0 8px rgba(200,150,62,0.6) !important;
}

.upload-hero {
    text-align: center;
    padding: 4rem 2rem;
    border: 2px dashed rgba(200,150,62,0.2);
    border-radius: 16px;
    background: rgba(20,12,6,0.6);
    margin: 2rem 0;
}

.upload-hero-icon { font-size: 4rem; margin-bottom: 1rem; }

.upload-hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: #d4b896;
    margin-bottom: 0.5rem;
}

.upload-hero-sub {
    font-family: 'Lato', sans-serif;
    font-size: 0.95rem;
    color: #6b5040;
    margin-bottom: 2rem;
    line-height: 1.6;
}
</style>
"""

COLORS = {
    "caramel":  "#C8963E",
    "espresso": "#6F4E37",
    "cream":    "#F5E6D3",
    "brown":    "#8B5E3C",
    "gold":     "#D4A853",
    "rust":     "#A0522D",
    "mocha":    "#7B5B3A",
    "latte":    "#C9A882",
}
COLOR_SEQ = list(COLORS.values())

COFFEE_PALETTE = [
    "#C8963E", "#6F4E37", "#A0522D", "#D4A853",
    "#8B5E3C", "#7B5B3A", "#C9A882", "#F5E6D3"
]

PLOT_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(26,15,7,0)",
    plot_bgcolor="rgba(26,15,7,0)",
    font=dict(family="'Lato', sans-serif", color="#b8956e", size=13),
    xaxis=dict(
        gridcolor="rgba(200,150,62,0.07)",
        zeroline=False,
        linecolor="rgba(200,150,62,0.10)",
        tickfont=dict(family="Lato, sans-serif", size=12, color="#8a7060"),
    ),
    yaxis=dict(
        gridcolor="rgba(200,150,62,0.07)",
        zeroline=False,
        linecolor="rgba(200,150,62,0.10)",
        tickfont=dict(family="Lato, sans-serif", size=12, color="#8a7060"),
    ),
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(
        bgcolor="rgba(26,15,7,0.85)",
        bordercolor="rgba(200,150,62,0.15)",
        borderwidth=1,
        font=dict(family="Lato, sans-serif", size=12, color="#b8956e"),
    ),
    hoverlabel=dict(
        bgcolor="rgba(20,12,6,0.95)",
        bordercolor="rgba(200,150,62,0.35)",
        font=dict(family="Lato, sans-serif", size=13, color="#f0e6d3"),
    ),
)


def inject_css():
    st.markdown(FONT_LINK, unsafe_allow_html=True)
    st.markdown(COFFEE_CSS, unsafe_allow_html=True)


def sidebar_brand(title="Afficionado Coffee", subtitle="Business Intelligence"):
    st.sidebar.markdown(f"""
        <div style="padding:0.75rem 0 1.5rem 0;">
            <div style="font-size:1.6rem;margin-bottom:0.4rem;">☕</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:700;
                        color:#C8963E;letter-spacing:0.02em;line-height:1.3;">
                {title}
            </div>
            <div style="font-family:'Lato',sans-serif;font-size:0.65rem;
                        color:#4a3020;margin-top:5px;letter-spacing:0.18em;
                        text-transform:uppercase;">
                {subtitle}
            </div>
        </div>
        <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(200,150,62,0.3),transparent);margin-bottom:1rem;"></div>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    icon_html = f'<span style="margin-right:0.5rem;">{icon}</span>' if icon else ""
    st.markdown(f"""
        <div style="margin-bottom:1.75rem;padding-bottom:1rem;
                    border-bottom:1px solid rgba(200,150,62,0.12);">
            <div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;
                        color:#f0e6d3;letter-spacing:0.01em;line-height:1.2;">
                {icon_html}{title}
            </div>
            {"<div style='font-family:Lato,sans-serif;color:#6b5040;font-size:0.82rem;margin-top:0.4rem;letter-spacing:0.12em;text-transform:uppercase;'>" + subtitle + "</div>" if subtitle else ""}
        </div>
    """, unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(f'<div class="coffee-section-header">{title}</div>', unsafe_allow_html=True)


def chart_label(title: str, sub: str = ""):
    st.markdown(
        f'<div class="coffee-chart-label">{title}</div>'
        + (f'<div class="coffee-chart-sub">{sub}</div>' if sub else ""),
        unsafe_allow_html=True,
    )


def kpi_card(col, title: str, value: str, icon: str = "", delta: str = "", color: str = "#C8963E"):
    COLOR_MAP = {
        "red":    "#E07070",
        "blue":   "#6BA3D4",
        "green":  "#6BBF8E",
        "orange": "#C8963E",
        "purple": "#9F7FBE",
        "teal":   "#5BBFB5",
        "cyan":   "#5BB8C8",
        "gold":   "#D4A853",
        "rust":   "#A0522D",
    }
    c = COLOR_MAP.get(color, color)
    with col:
        st.markdown(f"""
            <div class="coffee-kpi-card" style="border-color:{c};
                 box-shadow:0 0 24px {c}16,0 4px 20px rgba(0,0,0,0.5);">
                <span class="coffee-kpi-icon">{icon}</span>
                <span class="coffee-kpi-label">{title}</span>
                <span class="coffee-kpi-value" style="color:{c};">{value}</span>
                {"<span class='coffee-kpi-delta'>" + delta + "</span>" if delta else ""}
            </div>
        """, unsafe_allow_html=True)


def insight_card(text: str, kind: str = "info"):
    palettes = {
        "success": ("#6BBF8E", "rgba(107,191,142,0.07)"),
        "warning": ("#C8963E", "rgba(200,150,62,0.07)"),
        "error":   ("#E07070", "rgba(224,112,112,0.07)"),
        "info":    ("#6BA3D4", "rgba(107,163,212,0.07)"),
        "cyan":    ("#5BB8C8", "rgba(91,184,200,0.07)"),
    }
    bc, bg = palettes.get(kind, palettes["info"])
    st.markdown(
        f'<div class="coffee-insight" style="border-color:{bc};background:{bg};">{text}</div>',
        unsafe_allow_html=True
    )


def chart_note(text: str):
    st.markdown(f"""
        <div style="font-family:'Lato',sans-serif;
                    font-size:0.76rem;
                    color:#8a7060;
                    margin-top:-0.1rem;
                    margin-bottom:0.9rem;
                    line-height:1.6;
                    padding:0.45rem 0.75rem;
                    border-left:2px solid rgba(200,150,62,0.22);
                    background:rgba(200,150,62,0.03);
                    border-radius:0 4px 4px 0;">
            {text}
        </div>
    """, unsafe_allow_html=True)


def apply_plot_layout(fig, height: int = 380):
    fig.update_layout(height=height, **PLOT_LAYOUT)
    return fig


def footer():
    st.markdown("""
        <div style="margin-top:3.5rem;padding-top:1rem;
                    border-top:1px solid rgba(200,150,62,0.10);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-family:'Playfair Display',serif;font-size:0.65rem;
                            color:#3a2515;letter-spacing:0.1em;">
                    ☕ Afficionado Coffee Roasters
                </div>
                <div style="font-family:'Lato',sans-serif;font-size:0.6rem;
                            color:#3a2515;letter-spacing:0.18em;text-transform:uppercase;">
                    Business Intelligence Platform
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def no_data_warning():
    st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;border:2px dashed rgba(200,150,62,0.2);
                    border-radius:16px;background:rgba(20,12,6,0.5);margin:2rem 0;">
            <div style="font-size:3rem;margin-bottom:1rem;">☕</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.4rem;color:#d4b896;margin-bottom:0.5rem;">
                No Dataset Loaded
            </div>
            <div style="font-family:'Lato',sans-serif;font-size:0.9rem;color:#6b5040;line-height:1.6;">
                Please go to the <strong style="color:#C8963E;">Home page</strong> and upload your coffee shop CSV dataset to get started.
            </div>
        </div>
    """, unsafe_allow_html=True)

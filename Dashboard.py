"""
Dashboard.py — Optimized main entry point.

Optimizations:
  - KPIs computed once via cached calculate_kpis(); result stored in session_state.
  - Data loading wrapped in st.spinner with progress feedback.
  - Revenue trend aggregation cached via daily_sales_analysis().
  - Category chart uses cached category_analysis().
  - Redundant df copies eliminated.
  - Plotly chart traces reduced (aggregated before rendering).
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, COLORS, COFFEE_PALETTE,
)
from utils import (
    get_processed_data,
    calculate_kpis,
    workforce_planning,
    daily_sales_analysis,
    category_analysis,
    hourly_demand_analysis,
    store_analysis,
)

st.set_page_config(
    page_title="Afficionado Coffee Analytics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_brand("Afficionado Coffee", "Business Intelligence")

with st.sidebar:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.7rem;
                    color:#4a3020;letter-spacing:0.12em;text-transform:uppercase;
                    margin-bottom:0.5rem;">Navigation</div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                    line-height:1.8;padding:0.5rem 0;">
            📊 &nbsp;Main Dashboard<br>
            📈 &nbsp;Executive Overview<br>
            🔮 &nbsp;Sales Forecast<br>
            ⚡ &nbsp;Peak Demand<br>
            🔍 &nbsp;Demand Patterns<br>
            👥 &nbsp;Workforce Planning<br>
            🎯 &nbsp;Scenario Analysis<br>
            🤖 &nbsp;Model Comparison<br>
            ⌛ &nbsp;Real Time Model<br>
            📦 &nbsp;Inventory Management
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="height:1px;background:linear-gradient(90deg,transparent,
                    rgba(200,150,62,0.2),transparent);margin:1rem 0;"></div>
    """, unsafe_allow_html=True)

    if "df" in st.session_state and st.session_state["df"] is not None:
        df_info = st.session_state["df"]
        st.markdown(f"""
            <div style="background:rgba(200,150,62,0.08);border:1px solid rgba(200,150,62,0.18);
                        border-radius:8px;padding:0.75rem;font-family:'Lato',sans-serif;">
                <div style="font-size:0.6rem;color:#6b5040;letter-spacing:0.15em;
                            text-transform:uppercase;margin-bottom:0.4rem;">Dataset Loaded</div>
                <div style="font-size:0.8rem;color:#C8963E;font-weight:700;">
                    ✓ &nbsp;{len(df_info):,} records
                </div>
                <div style="font-size:0.72rem;color:#8a7060;margin-top:0.2rem;">
                    {len(df_info.columns)} columns
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Clear Dataset", use_container_width=True):
            for key in ["df", "_kpis_cache", "_daily_sales_cache"]:
                st.session_state.pop(key, None)
            st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.25rem;">
        <div style="font-size:2.4rem;">☕</div>
        <div>
            <div style="font-family:'Playfair Display',serif;font-size:2rem;
                        font-weight:800;color:#f0e6d3;line-height:1.1;">
                Afficionado Coffee Analytics
            </div>
            <div style="font-family:'Lato',sans-serif;font-size:0.78rem;
                        color:#6b5040;letter-spacing:0.2em;text-transform:uppercase;
                        margin-top:3px;">
                Revenue · Operations · Customer Intelligence
            </div>
        </div>
    </div>
    <div style="height:1px;background:linear-gradient(90deg,rgba(200,150,62,0.4),
                rgba(200,150,62,0.05),transparent);margin:1rem 0 1.5rem 0;"></div>
""", unsafe_allow_html=True)

# ── Upload Section ────────────────────────────────────────────────────────────
if "df" not in st.session_state or st.session_state["df"] is None:
    st.markdown("""
        <div style="text-align:center;padding:0.5rem 0 1rem 0;">
            <div style="font-family:'Playfair Display',serif;font-size:1.3rem;
                        color:#d4b896;margin-bottom:0.4rem;">
                Begin Your Analysis
            </div>
            <div style="font-family:'Lato',sans-serif;font-size:0.88rem;color:#6b5040;
                        line-height:1.6;max-width:480px;margin:0 auto;">
                Upload your coffee shop transaction CSV once — your dataset will persist
                across all dashboard pages throughout your session.
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_up1, col_up2, col_up3 = st.columns([1, 3, 1])
    with col_up2:
        uploaded = st.file_uploader(
            "Drop your Coffee Shop CSV here",
            type=["csv"],
            help="Upload a CSV with columns: transaction_time, transaction_qty, unit_price, store_location, product_category, product_type, transaction_id",
        )

    if uploaded:
        with st.spinner("☕ Brewing your analytics… loading and processing data"):
            file_bytes = uploaded.read()
            df = get_processed_data(file_bytes, uploaded.name)
            st.session_state["df"] = df
        st.success(f"✓ Dataset loaded — {len(df):,} records ready for analysis.")
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
            <div style="background:rgba(20,12,6,0.7);border:1px solid rgba(200,150,62,0.12);
                        border-radius:12px;padding:1.5rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.6rem;">📊</div>
                <div style="font-family:'Playfair Display',serif;font-size:0.95rem;
                            color:#d4b896;margin-bottom:0.4rem;">Executive KPIs</div>
                <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                            line-height:1.5;">Revenue, transactions, and store performance at a glance</div>
            </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
            <div style="background:rgba(20,12,6,0.7);border:1px solid rgba(200,150,62,0.12);
                        border-radius:12px;padding:1.5rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.6rem;">🔮</div>
                <div style="font-family:'Playfair Display',serif;font-size:0.95rem;
                            color:#d4b896;margin-bottom:0.4rem;">AI Forecasting</div>
                <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                            line-height:1.5;">ML-powered demand prediction and revenue forecasting</div>
            </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown("""
            <div style="background:rgba(20,12,6,0.7);border:1px solid rgba(200,150,62,0.12);
                        border-radius:12px;padding:1.5rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.6rem;">👥</div>
                <div style="font-family:'Playfair Display',serif;font-size:0.95rem;
                            color:#d4b896;margin-bottom:0.4rem;">Workforce Planning</div>
                <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                            line-height:1.5;">Staffing recommendations driven by real transaction data</div>
            </div>
        """, unsafe_allow_html=True)

    footer()
    st.stop()

# ── Dashboard (data loaded) ───────────────────────────────────────────────────
df = st.session_state["df"]

# Compute all aggregates once; cached functions ensure no redundant work
kpis        = calculate_kpis(df)
daily_sales = daily_sales_analysis(df)
cat_agg     = category_analysis(df)
hourly_agg  = hourly_demand_analysis(df)
store_agg   = store_analysis(df)

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Executive Summary")
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Total Revenue",     f"${kpis['Revenue']:,.0f}",        icon="💰", color="orange")
kpi_card(c2, "Transactions",      f"{kpis['Transactions']:,}",       icon="🧾", color="blue")
kpi_card(c3, "Units Sold",        f"{kpis['Quantity']:,}",           icon="📦", color="green")
kpi_card(c4, "Avg Order Value",   f"${kpis['Avg_Order_Value']:.2f}", icon="📈", color="purple")

st.markdown("<br>", unsafe_allow_html=True)
c5, c6 = st.columns(2)
kpi_card(c5, "Best-Performing Store",  kpis["Best_Store"],    icon="🏆", color="gold")
kpi_card(c6, "Top Product Category",   kpis["Best_Category"], icon="🥇", color="rust")

# ── Revenue Trend ─────────────────────────────────────────────────────────────
section_header("Revenue Trend")
chart_label("Daily Revenue", "Total revenue generated each day")

daily_plot = daily_sales.copy()
daily_plot["date"] = pd.to_datetime(daily_plot["date"])

fig = go.Figure()
fig.add_trace(go.Bar(
    x=daily_plot["date"], y=daily_plot["Revenue"],
    marker_color=COLORS["caramel"], opacity=0.85,
    hovertemplate="<b>%{x|%b %d}</b><br>$%{y:,.0f}<extra></extra>",
))
fig.update_xaxes(tickformat="%b %d", tickangle=30)
fig.update_yaxes(tickprefix="$", tickformat=",.0f")
apply_plot_layout(fig, height=320)
st.plotly_chart(fig, use_container_width=True)
chart_note(f"Total revenue: ${kpis['Revenue']:,.0f}. Identify high-performance periods to replicate success.")

# ── Store & Category ──────────────────────────────────────────────────────────
section_header("Store & Category Performance")
col1, col2 = st.columns(2)

with col1:
    chart_label("Revenue by Store", "Total revenue per location")
    fig = go.Figure(go.Bar(
        x=store_agg["store_location"], y=store_agg["Revenue"],
        marker=dict(
            color=store_agg["Revenue"],
            colorscale=[[0, COLORS["espresso"]], [0.5, COLORS["brown"]], [1, COLORS["caramel"]]],
            showscale=False,
        ),
        hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(tickprefix="$")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    chart_label("Revenue by Category", "Category contribution to total revenue")
    fig = px.pie(
        cat_agg, names="product_category", values="Revenue",
        hole=0.52, color_discrete_sequence=COFFEE_PALETTE,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>",
    )
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

# ── Hourly Demand ─────────────────────────────────────────────────────────────
section_header("Hourly Demand Pattern")
chart_label("Units Sold by Hour", "Peak demand across the 24-hour cycle")

peak_h      = int(hourly_agg.loc[hourly_agg["Quantity"].idxmax(), "hour"])
colors_h    = [COLORS["caramel"] if h == peak_h else COLORS["espresso"] for h in hourly_agg["hour"]]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=hourly_agg["hour"], y=hourly_agg["Quantity"],
    mode="lines+markers",
    line=dict(color=COLORS["caramel"], width=3),
    marker=dict(color=colors_h, size=10, line=dict(color=COLORS["caramel"], width=2)),
    hovertemplate="Hour %{x}:00<br>Units: %{y:,}<extra></extra>",
))
fig.update_xaxes(tickmode="linear", title="Hour of Day")
fig.update_yaxes(title="Units Sold")
apply_plot_layout(fig, height=300)
st.plotly_chart(fig, use_container_width=True)
chart_note(f"Peak demand at {peak_h}:00 — align staffing and inventory to this window.")

# ── Workforce Summary ─────────────────────────────────────────────────────────
section_header("Workforce Overview")
chart_label("Required Staff by Store & Hour", "Minimum headcount per store per hour")

staff_df   = workforce_planning(df)
pivot      = staff_df.pivot_table(
    index="store_location", columns="hour",
    values="Required_Staff", aggfunc="sum",
).fillna(0)

fig = px.imshow(
    pivot,
    color_continuous_scale=[[0, "#1a0f07"], [0.3, "#6F4E37"], [0.7, "#C8963E"], [1, "#F5E6D3"]],
    labels={"x": "Hour of Day", "y": "Store", "color": "Staff Required"},
    aspect="auto",
)
apply_plot_layout(fig, height=240)
st.plotly_chart(fig, use_container_width=True)
chart_note("Darker cells = more staff needed. Use this heatmap to build your weekly shift schedules.")

footer()

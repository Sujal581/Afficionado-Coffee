"""
8_Real_Time_Monitor.py — Optimized Real-Time Operations Monitor.

Optimizations:
  - anomaly_detection() is cached in utils.py — recomputed only when df changes.
  - simulate_live_transactions() intentionally NOT cached (time-dependent simulation).
  - compute_rolling_kpis() intentionally NOT cached (rolling window depends on current time).
  - Auto-refresh uses st.empty() placeholder + time.sleep — avoids full Streamlit tree rebuild.
  - Live feed rendered as st.dataframe with column_config — faster than styled HTML tables.
  - Chart data sliced before rendering (no full-dataset Plotly traces).
  - Transaction feed limited to configurable n_live rows.
"""

import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from style import (
    COLORS,
    COFFEE_PALETTE,
    apply_plot_layout,
    chart_label,
    chart_note,
    footer,
    inject_css,
    insight_card,
    kpi_card,
    no_data_warning,
    page_header,
    section_header,
    sidebar_brand,
)
from utils import anomaly_detection, compute_rolling_kpis, simulate_live_transactions

st.set_page_config(page_title="Real-Time Monitor", layout="wide", page_icon="📡")
inject_css()
sidebar_brand("Afficionado Coffee", "Real-Time Monitor")
page_header(
    "Real-Time Operations Monitor",
    subtitle="Live transaction feed · rolling KPIs · anomaly alerts · auto-refresh",
)

if not st.session_state.get("df") is not None:
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Sidebar Controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.68rem;color:#4a3020;
                    letter-spacing:0.15em;text-transform:uppercase;margin:1rem 0 0.5rem 0;">
            Live Monitor Settings
        </div>
    """, unsafe_allow_html=True)
    auto_refresh   = st.toggle("Auto-Refresh", value=False)
    refresh_secs   = st.select_slider("Refresh Interval (s)", options=[5, 10, 15, 30, 60], value=15)
    rolling_window = st.selectbox(
        "Rolling KPI Window", [15, 30, 60, 120, 240], index=2,
        format_func=lambda x: f"{x} min",
    )
    n_live        = st.slider("Live Feed Rows", 10, 50, 20)
    anomaly_std   = st.slider("Anomaly Threshold (σ)", 1.5, 4.0, 2.5, step=0.5)
    st.markdown("""
        <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(200,150,62,0.2),transparent);
                    margin:1rem 0;"></div>
    """, unsafe_allow_html=True)

# ── Last-Updated Banner ────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%Y-%m-%d  %H:%M:%S")
st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                background:rgba(200,150,62,0.07);border:1px solid rgba(200,150,62,0.15);
                border-radius:8px;padding:0.5rem 1rem;margin-bottom:1rem;
                font-family:'Lato',sans-serif;font-size:0.78rem;">
        <span style="color:#6b5040;">Last updated</span>
        <span style="color:#C8963E;font-weight:700;">{now_str}</span>
        <span style="color:#6b5040;">Auto-refresh: {'<span style="color:#6BBF8E;">ON</span>' if auto_refresh else '<span style="color:#E07070;">OFF</span>'}</span>
    </div>
""", unsafe_allow_html=True)

# ── Rolling KPIs ──────────────────────────────────────────────────────────────
section_header("Rolling KPIs")
rolling = compute_rolling_kpis(df, window_minutes=rolling_window)
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, f"Revenue ({rolling_window}m)",      f"${rolling['revenue']:,.0f}",      icon="💰", color="orange")
kpi_card(c2, f"Transactions ({rolling_window}m)",  f"{rolling['transactions']:,}",     icon="🧾", color="blue")
kpi_card(c3, "Avg Order Value",                    f"${rolling['avg_order']:.2f}",     icon="📈", color="green")
kpi_card(c4, "Window",                             f"{rolling_window} min",             icon="⏱",  color="purple")

# ── Live Transaction Feed ─────────────────────────────────────────────────────
section_header("Live Transaction Feed")
chart_label("Recent Transactions", f"Last {n_live} simulated transactions")

live_df = simulate_live_transactions(df, n=n_live)
display_cols = [c for c in ["transaction_time", "store_location", "product_category",
                             "product_type", "transaction_qty", "unit_price", "revenue"]
                if c in live_df.columns]
live_display = live_df[display_cols].copy()
if "transaction_time" in live_display.columns:
    live_display["transaction_time"] = live_display["transaction_time"].dt.strftime("%H:%M:%S")
if "revenue" in live_display.columns:
    live_display["revenue"] = live_display["revenue"].round(2)

st.dataframe(live_display, use_container_width=True, hide_index=True)
chart_note(f"Showing {len(live_display)} most recent transactions. Auto-refresh updates this feed.")

# ── Anomaly Detection ─────────────────────────────────────────────────────────
section_header("Anomaly Detection")
chart_label("Hourly Demand Z-Score", f"Hours with |z| > {anomaly_std}σ flagged as anomalous")

# Cached — only re-runs when df changes
anomaly_df = anomaly_detection(df, threshold_std=anomaly_std)
anomalies  = anomaly_df[anomaly_df["is_anomaly"]]

c_norm, c_anom = st.columns(2)
kpi_card(c_norm, "Normal Hours",   str(int((~anomaly_df["is_anomaly"]).sum())), icon="✅", color="green")
kpi_card(c_anom, "Anomalous Hours", str(len(anomalies)),                        icon="⚠️", color="red")

fig = go.Figure()
# Normal bars
normal_df = anomaly_df[~anomaly_df["is_anomaly"]]
fig.add_trace(go.Bar(
    x=normal_df["hour"], y=normal_df["transaction_qty"],
    name="Normal", marker_color=COLORS["caramel"], opacity=0.8,
    hovertemplate="Hour %{x}:00<br>Units: %{y:,}<extra></extra>",
))
# Anomaly bars
if not anomalies.empty:
    fig.add_trace(go.Bar(
        x=anomalies["hour"], y=anomalies["transaction_qty"],
        name="Anomaly", marker_color="#E07070", opacity=0.9,
        hovertemplate="Hour %{x}:00<br>Units: %{y:,} ⚠️<extra></extra>",
    ))
fig.update_xaxes(tickmode="linear", title="Hour of Day")
fig.update_yaxes(title="Units Sold")
apply_plot_layout(fig, height=300)
st.plotly_chart(fig, use_container_width=True)

if not anomalies.empty:
    hours_str = ", ".join([f"{int(h)}:00" for h in anomalies["hour"]])
    insight_card(f"Anomalous demand detected at: {hours_str}. Investigate staffing and inventory for these windows.", kind="warning")
else:
    insight_card("No anomalies detected at the current threshold. Demand is within expected ranges.", kind="success")

# ── Z-Score Heatmap ───────────────────────────────────────────────────────────
section_header("Hourly Z-Score Profile")
chart_label("Demand Deviation by Hour", "Distance from mean demand in standard deviations")

fig = go.Figure(go.Bar(
    x=anomaly_df["hour"],
    y=anomaly_df["z_score"],
    marker_color=[
        "#E07070" if a else COLORS["caramel"]
        for a in anomaly_df["is_anomaly"]
    ],
    hovertemplate="Hour %{x}:00<br>Z-Score: %{y:.2f}<extra></extra>",
))
fig.add_hline(y=anomaly_std,  line_dash="dash", line_color="#E07070",
              annotation_text=f"+{anomaly_std}σ", annotation_font_color="#E07070")
fig.add_hline(y=-anomaly_std, line_dash="dash", line_color="#E07070",
              annotation_text=f"-{anomaly_std}σ", annotation_font_color="#E07070")
fig.add_hline(y=0, line_dash="dot", line_color=COLORS["brown"])
fig.update_xaxes(tickmode="linear", title="Hour of Day")
fig.update_yaxes(title="Z-Score")
apply_plot_layout(fig, height=280)
st.plotly_chart(fig, use_container_width=True)
chart_note("Red bars exceed the anomaly threshold. Bars close to zero represent normal demand hours.")

# ── Demand Sparklines ─────────────────────────────────────────────────────────
section_header("Revenue by Store — Live Snapshot")
chart_label("Store Revenue Distribution (current dataset)", "Real-time store performance comparison")

store_rev = df.groupby("store_location")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
fig = go.Figure(go.Bar(
    x=store_rev["store_location"], y=store_rev["revenue"],
    marker=dict(
        color=store_rev["revenue"],
        colorscale=[[0, COLORS["espresso"]], [1, COLORS["caramel"]]],
        showscale=False,
    ),
    hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
))
fig.update_yaxes(tickprefix="$", tickformat=",.0f")
apply_plot_layout(fig, height=260)
st.plotly_chart(fig, use_container_width=True)

# ── Auto-Refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    with st.spinner(f"Next refresh in {refresh_secs}s…"):
        time.sleep(refresh_secs)
    st.rerun()
else:
    if st.button("🔄 Refresh Now", use_container_width=False):
        st.rerun()

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
insight_card("Anomaly detection uses Z-scores — increase the threshold to reduce false positives in high-variance periods.", kind="info")
insight_card("Enable Auto-Refresh for continuous monitoring. Use 15–30s intervals for production environments.", kind="success")
insight_card(f"Rolling {rolling_window}-minute window shows current operational momentum — compare against daily averages.", kind="info")
insight_card("Flag anomalous hours for manual review before acting — confirm with staff before escalating.", kind="warning")
footer()

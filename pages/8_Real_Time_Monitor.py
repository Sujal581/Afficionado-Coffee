import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import time
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, no_data_warning, COLORS, COFFEE_PALETTE,
)
from utils import simulate_live_transactions, compute_rolling_kpis, anomaly_detection

st.set_page_config(page_title="Real-Time Monitor", layout="wide", page_icon="📡")
inject_css()
sidebar_brand("Afficionado Coffee", "Real-Time Monitor")
page_header("Real-Time Operations Monitor",
            subtitle="Live transaction feed · rolling KPIs · anomaly alerts · auto-refresh")

if not (st.session_state.get("df") is not None):
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
    rolling_window = st.selectbox("Rolling KPI Window", [15, 30, 60, 120, 240], index=2,
                                  format_func=lambda x: f"{x} min")
    n_live         = st.slider("Live Feed Rows", 10, 50, 20)
    anomaly_std    = st.slider("Anomaly Threshold (σ)", 1.5, 4.0, 2.5, step=0.5)
    st.markdown("""
        <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(200,150,62,0.2),transparent);
                    margin:1rem 0;"></div>
    """, unsafe_allow_html=True)

# ── Last-Updated Banner ────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%Y-%m-%d  %H:%M:%S")
st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                background:rgba(200,150,62,0.07);border:1px solid rgba(200,150,62,0.18);
                border-radius:8px;padding:0.55rem 1.1rem;margin-bottom:1rem;">
        <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#C8963E;">
            📡 &nbsp;<strong>Live Dashboard</strong>
        </div>
        <div style="font-family:'Lato',sans-serif;font-size:0.72rem;color:#6b5040;">
            Last updated: <strong style="color:#b8956e;">{now_str}</strong>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Rolling KPIs ──────────────────────────────────────────────────────────────
section_header("Rolling KPIs")

rolling = compute_rolling_kpis(df, window_minutes=rolling_window)

c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, f"Revenue ({rolling_window}min window)", f"${rolling['revenue']:,.0f}",       icon="💰", color="orange")
kpi_card(c2, f"Transactions ({rolling_window}min)",    f"{rolling['transactions']:,}",      icon="🧾", color="blue")
kpi_card(c3, "Avg Order Value",                        f"${rolling['avg_order']:.2f}",      icon="📈", color="green")
kpi_card(c4, "Monitor Status",                         "🟢 Live" if auto_refresh else "⏸ Paused",
         icon="📡", color="teal" if auto_refresh else "purple")

# ── Live Transaction Feed ──────────────────────────────────────────────────────
section_header("Live Transaction Feed")
chart_label("Most Recent Transactions", f"Last {n_live} simulated transactions (newest first)")

live_df = simulate_live_transactions(df, n=n_live)
display_cols = [c for c in ["transaction_time", "store_location", "product_category",
                             "product_type", "transaction_qty", "unit_price", "revenue"]
                if c in live_df.columns]
live_show = live_df[display_cols].copy()
if "transaction_time" in live_show.columns:
    live_show["transaction_time"] = live_show["transaction_time"].dt.strftime("%H:%M:%S")
if "revenue" in live_show.columns:
    live_show["revenue"] = live_show["revenue"].apply(lambda x: f"${x:.2f}")
if "unit_price" in live_show.columns:
    live_show["unit_price"] = live_show["unit_price"].apply(lambda x: f"${x:.2f}")

st.dataframe(live_show, use_container_width=True, hide_index=True)
chart_note("This feed simulates real-time transactions drawn from your dataset. In production, connect to your POS system API.")

# ── Live Revenue Sparkline ─────────────────────────────────────────────────────
section_header("Live Revenue Trend")
chart_label("Revenue by Hour (Last 24 Hours)", "Rolling revenue trend — refreshes with each update")

df_c = df.copy()
df_c["transaction_time"] = pd.to_datetime(df_c["transaction_time"], errors="coerce")
hourly_rev = (
    df_c.groupby(df_c["transaction_time"].dt.hour)["revenue"]
    .sum()
    .reset_index()
)
hourly_rev.columns = ["hour", "revenue"]

noise = np.random.default_rng(int(pd.Timestamp.now().timestamp()) % 10000)
hourly_rev["revenue_live"] = hourly_rev["revenue"] * noise.uniform(0.92, 1.08, len(hourly_rev))

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=hourly_rev["hour"], y=hourly_rev["revenue"],
    mode="lines", name="Baseline",
    line=dict(color=COLORS["espresso"], width=2, dash="dot"),
    hovertemplate="Hour %{x}:00<br>Baseline: $%{y:,.0f}<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=hourly_rev["hour"], y=hourly_rev["revenue_live"],
    mode="lines+markers", name="Live",
    line=dict(color=COLORS["caramel"], width=3),
    marker=dict(size=6, color=COLORS["caramel"]),
    fill="tozeroy", fillcolor="rgba(200,150,62,0.06)",
    hovertemplate="Hour %{x}:00<br>Live: $%{y:,.0f}<extra></extra>",
))
fig.update_xaxes(title="Hour of Day", tickmode="linear")
fig.update_yaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
apply_plot_layout(fig, height=320)
st.plotly_chart(fig, use_container_width=True)
chart_note("Gold line = live revenue. Dotted line = historical baseline. Deviations highlight unexpected demand shifts.")

# ── Anomaly Detection ──────────────────────────────────────────────────────────
section_header("Anomaly Detection")
chart_label("Demand Anomalies by Hour",
            f"Hours with z-score > {anomaly_std}σ flagged as anomalous")

anomaly_df = anomaly_detection(df, threshold_std=anomaly_std)
n_anomalies = anomaly_df["is_anomaly"].sum()

col_a1, col_a2, col_a3 = st.columns(3)
kpi_card(col_a1, "Anomalous Hours",  str(int(n_anomalies)),          icon="⚠️", color="red")
kpi_card(col_a2, "Threshold",        f"{anomaly_std}σ",              icon="📏", color="orange")
kpi_card(col_a3, "Hours Monitored",  str(len(anomaly_df)),           icon="👁", color="blue")

colors_anomaly = [
    COLORS["caramel"] if not a else "#E07070"
    for a in anomaly_df["is_anomaly"]
]
fig = go.Figure()
fig.add_trace(go.Bar(
    x=anomaly_df["hour"], y=anomaly_df["transaction_qty"],
    marker_color=colors_anomaly,
    hovertemplate="Hour %{x}:00<br>Units: %{y:,}<br>Z-score: %{customdata:.2f}<extra></extra>",
    customdata=anomaly_df["z_score"],
    name="Demand",
))
fig.add_hline(
    y=anomaly_df["transaction_qty"].mean() + anomaly_std * anomaly_df["transaction_qty"].std(),
    line_dash="dash", line_color="#E07070",
    annotation_text=f"+{anomaly_std}σ threshold",
    annotation_font_color="#E07070",
)
fig.update_xaxes(title="Hour of Day", tickmode="linear")
fig.update_yaxes(title="Units Sold", tickformat=",")
apply_plot_layout(fig, height=300)
st.plotly_chart(fig, use_container_width=True)
chart_note("Red bars exceed the anomaly threshold. Investigate root causes: promotions, events, or data quality issues.")

if n_anomalies > 0:
    anomaly_hours = anomaly_df[anomaly_df["is_anomaly"]]["hour"].tolist()
    insight_card(
        f"⚠️ {int(n_anomalies)} anomalous hour(s) detected at {[f'{h}:00' for h in anomaly_hours]}. "
        f"Verify staffing and inventory for these windows.",
        kind="error" if n_anomalies >= 3 else "warning",
    )

# ── Store Activity Map ─────────────────────────────────────────────────────────
section_header("Live Store Activity")
chart_label("Real-Time Revenue Distribution by Store",
            "Simulated live revenue share across all locations")

if "store_location" in df.columns:
    store_live = (
        df.groupby("store_location")["revenue"]
        .sum()
        .reset_index()
    )
    rng2 = np.random.default_rng(int(pd.Timestamp.now().second))
    store_live["revenue_live"] = store_live["revenue"] * rng2.uniform(0.90, 1.10, len(store_live))
    store_live = store_live.sort_values("revenue_live", ascending=False)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        fig = px.pie(
            store_live, names="store_location", values="revenue_live",
            hole=0.52, color_discrete_sequence=COFFEE_PALETTE,
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>Live Rev: $%{value:,.0f}<extra></extra>",
        )
        apply_plot_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col_s2:
        fig = go.Figure(go.Bar(
            x=store_live["revenue_live"], y=store_live["store_location"],
            orientation="h",
            marker=dict(
                color=store_live["revenue_live"],
                colorscale=[[0, COLORS["espresso"]], [1, COLORS["caramel"]]],
                showscale=False,
            ),
            hovertemplate="%{y}<br>Live Revenue: $%{x:,.0f}<extra></extra>",
        ))
        fig.update_xaxes(tickprefix="$", tickformat=",.0f", title="Live Revenue")
        apply_plot_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)
    chart_note(f"Top performer: {store_live.iloc[0]['store_location']} — ${store_live.iloc[0]['revenue_live']:,.0f}")

# ── Alerts Panel ──────────────────────────────────────────────────────────────
section_header("Operational Alerts")

peak_hour = int(df.groupby("hour")["transaction_qty"].sum().idxmax())
current_hour = pd.Timestamp.now().hour
hours_to_peak = (peak_hour - current_hour) % 24

if hours_to_peak <= 2:
    insight_card(f"🔴 Peak demand at {peak_hour}:00 is {hours_to_peak}h away — begin staffing scale-up now.", kind="error")
elif hours_to_peak <= 4:
    insight_card(f"🟡 Peak at {peak_hour}:00 is approaching ({hours_to_peak}h). Pre-stock and confirm staffing schedules.", kind="warning")
else:
    insight_card(f"🟢 Peak demand at {peak_hour}:00 is {hours_to_peak}h away. Operations are within normal parameters.", kind="success")

if n_anomalies >= 3:
    insight_card("Multiple demand anomalies detected. Review POS data integrity and check for promotional activity.", kind="error")
elif n_anomalies > 0:
    insight_card(f"{int(n_anomalies)} demand anomaly detected. Monitor the flagged hour(s) and prepare contingency coverage.", kind="warning")
else:
    insight_card("No demand anomalies detected this cycle. All hours are within expected variance.", kind="success")

insight_card("Connect this dashboard to your live POS system API to replace the simulated feed with real transaction data.", kind="info")

# ── Auto-Refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    st.markdown(f"""
        <div style="text-align:center;font-family:'Lato',sans-serif;font-size:0.72rem;
                    color:#4a3020;padding:0.5rem 0;">
            Auto-refreshing every <strong style="color:#C8963E;">{refresh_secs}s</strong>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(refresh_secs)
    st.rerun()

footer()

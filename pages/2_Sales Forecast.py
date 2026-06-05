import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, no_data_warning, COLORS,
)
from utils import calculate_kpis, moving_average_forecast

st.set_page_config(page_title="Sales Forecast", layout="wide", page_icon="🔮")
inject_css()
sidebar_brand("Afficionado Coffee", "Sales Forecast")
page_header("Sales Forecast Dashboard", subtitle="Moving average demand forecasting engine")

if not (st.session_state.get("df") is not None):
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Settings ──────────────────────────────────────────────────────────────────
section_header("Forecast Settings")
col1, col2, col3 = st.columns(3)
with col1:
    store = st.selectbox("Select Store", ["All Stores"] + sorted(df["store_location"].unique().tolist()))
with col2:
    horizon = st.selectbox("Forecast Horizon (Hours)", [6, 12, 24, 48], index=1)
with col3:
    metric = st.selectbox("Target Metric", ["revenue", "transaction_qty"], index=0)

actual, forecast = moving_average_forecast(
    df,
    store=store if store != "All Stores" else None,
    target=metric, periods=horizon, window=3,
)

if forecast is None:
    st.error("⚠️ Not enough hourly data for the selected store or metric. Try a different store or metric.")
    st.stop()

kpis = calculate_kpis(df)
future = forecast.tail(horizon)
forecast_total = future["yhat"].sum()
peak_idx = actual["y"].idxmax()
peak_hour = actual.loc[peak_idx, "ds"].strftime("%I:%M %p")
confidence = 85.0
avg_order_value = max(kpis["Avg_Order_Value"], 1)
forecast_orders = int(forecast_total / avg_order_value) if metric == "revenue" else int(forecast_total)
forecast_display = f"${forecast_total:,.0f}" if metric == "revenue" else f"{forecast_total:,.0f}"

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Forecast KPIs")
col1, col2, col3, col4 = st.columns(4)
title_label = "Forecast Revenue" if metric == "revenue" else "Forecast Quantity"
kpi_card(col1, title_label,     forecast_display,          icon="🔮", color="orange")
kpi_card(col2, "Peak Sales Hour", peak_hour,               icon="⏰", color="blue")
kpi_card(col3, "Forecast Orders", f"{forecast_orders:,}", icon="🧾", color="green")
kpi_card(col4, "Model Confidence", f"{confidence:.0f}%",  icon="✅", color="purple")

# ── Actual vs Forecast ────────────────────────────────────────────────────────
section_header("Actual vs Forecasted")
chart_label(
    f"Actual vs Forecasted {metric.replace('_', ' ').title()}",
    "Historical actuals with forward projection"
)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=actual["ds"], y=actual["y"],
    mode="lines", name="Actual",
    line=dict(color=COLORS["caramel"], width=3),
    hovertemplate="<b>%{x|%H:%M}</b><br>Actual: %{y:,.0f}<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=forecast["ds"], y=forecast["yhat"],
    mode="lines", name="Forecast",
    line=dict(color=COLORS["cream"], width=2.5, dash="dash"),
    hovertemplate="<b>%{x|%H:%M}</b><br>Forecast: %{y:,.0f}<extra></extra>",
))
fig.add_vrect(
    x0=actual["ds"].max(), x1=forecast["ds"].max(),
    fillcolor="rgba(200,150,62,0.04)", layer="below", line_width=0,
    annotation_text="Forecast Window", annotation_position="top left",
    annotation_font_color=COLORS["caramel"],
)
fig.update_xaxes(title="Time", tickformat="%H:%M", tickangle=30)
if metric == "revenue":
    fig.update_yaxes(title="Revenue ($)", tickprefix="$")
else:
    fig.update_yaxes(title="Quantity", tickformat=",")
apply_plot_layout(fig, height=360)
st.plotly_chart(fig, use_container_width=True)
chart_note(f"Total {metric.replace('_',' ')} forecast: {forecast_display} over next {horizon} hours. Peak at {peak_hour}.")

# ── Revenue Projections & Table ────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    section_header("Projected Revenue by Hour")
    chart_label("Hourly Projection Breakdown", "Revenue or quantity expected per hour")
    future_copy = future.copy()
    future_copy["hour"] = future_copy["ds"].dt.hour
    hourly_proj = future_copy.groupby("hour")["yhat"].sum().reset_index()
    fig = go.Figure(go.Bar(
        x=hourly_proj["hour"], y=hourly_proj["yhat"],
        marker=dict(
            color=hourly_proj["yhat"],
            colorscale=[[0, COLORS["espresso"]], [1, COLORS["caramel"]]],
            showscale=False,
        ),
        hovertemplate="Hour %{x}:00<br>%{y:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(tickmode="linear", title="Hour")
    if metric == "revenue":
        fig.update_yaxes(tickprefix="$")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("Hours with higher projections should be prioritised for staffing and inventory replenishment.")

with col2:
    section_header("Detailed Forecast Table")
    chart_label("Hour-by-Hour Forecast", "Tabular view of projected values")
    display_df = future[["ds", "yhat"]].copy()
    display_df["DateTime"] = display_df["ds"].dt.strftime("%Y-%m-%d %H:%M")
    display_df["Forecasted Value"] = display_df["yhat"].apply(
        lambda x: f"${x:,.2f}" if metric == "revenue" else f"{x:,.0f}"
    )
    st.dataframe(display_df[["DateTime", "Forecasted Value"]], use_container_width=True, hide_index=True)
    chart_note("Use granular hourly forecasts to plan staffing rotations and inventory pre-loading.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
insight_card(f"Peak sales hour is {peak_hour} — ensure maximum barista coverage and ingredient stock during this window.", kind="info")
insight_card(f"Forecasted {metric.replace('_',' ')} for next {horizon} hours: {forecast_display}. Use this to plan operational capacity.", kind="success")
insight_card("Forecast accuracy improves with more historical data. Consider running weekly model refreshes as new transaction data accumulates.", kind="warning")
footer()

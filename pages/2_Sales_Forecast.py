import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, no_data_warning, COLORS,
)
from utils import calculate_kpis, moving_average_forecast, prophet_forecast, arima_forecast

st.set_page_config(page_title="Sales Forecast", layout="wide", page_icon="🔮")
inject_css()
sidebar_brand("Afficionado Coffee", "Sales Forecast")
page_header("Sales Forecast Dashboard", subtitle="Moving average · Prophet · ARIMA time-series forecasting")

if not (st.session_state.get("df") is not None):
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Settings ──────────────────────────────────────────────────────────────────
section_header("Forecast Settings")
col1, col2, col3, col4 = st.columns(4)
with col1:
    store = st.selectbox("Select Store", ["All Stores"] + sorted(df["store_location"].unique().tolist()))
with col2:
    horizon = st.selectbox("Forecast Horizon (Hours — MA)", [6, 12, 24, 48], index=1)
with col3:
    metric = st.selectbox("Target Metric", ["revenue", "transaction_qty"], index=0)
with col4:
    model_choice = st.selectbox("Forecast Model", ["Moving Average", "Prophet", "ARIMA", "All Models"])

store_filter = store if store != "All Stores" else None
kpis = calculate_kpis(df)
avg_order_value = max(kpis["Avg_Order_Value"], 1)

# ── Moving Average ─────────────────────────────────────────────────────────────
section_header("Moving Average Forecast")
actual_ma, forecast_ma = moving_average_forecast(
    df, store=store_filter, target=metric, periods=horizon, window=3,
)

if forecast_ma is None:
    st.error("⚠️ Not enough hourly data for Moving Average. Try a different store.")
else:
    future_ma = forecast_ma.tail(horizon)
    forecast_total_ma = future_ma["yhat"].sum()
    peak_idx = actual_ma["y"].idxmax()
    peak_hour = actual_ma.loc[peak_idx, "ds"].strftime("%I:%M %p")
    forecast_orders_ma = int(forecast_total_ma / avg_order_value) if metric == "revenue" else int(forecast_total_ma)
    display_ma = f"${forecast_total_ma:,.0f}" if metric == "revenue" else f"{forecast_total_ma:,.0f}"

    c1, c2, c3, c4 = st.columns(4)
    label_ma = "Forecast Revenue" if metric == "revenue" else "Forecast Quantity"
    kpi_card(c1, label_ma,          display_ma,                    icon="🔮", color="orange")
    kpi_card(c2, "Peak Sales Hour", peak_hour,                     icon="⏰", color="blue")
    kpi_card(c3, "Forecast Orders", f"{forecast_orders_ma:,}",    icon="🧾", color="green")
    kpi_card(c4, "Model",           "Moving Average (3-period)",   icon="📐", color="purple")

    if model_choice in ("Moving Average", "All Models"):
        chart_label("Actual vs Forecasted (Moving Average)",
                    "Historical actuals with moving-average forward projection")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=actual_ma["ds"], y=actual_ma["y"], mode="lines", name="Actual",
            line=dict(color=COLORS["caramel"], width=3),
            hovertemplate="<b>%{x|%H:%M}</b><br>Actual: %{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=forecast_ma["ds"], y=forecast_ma["yhat"], mode="lines", name="MA Forecast",
            line=dict(color=COLORS["cream"], width=2.5, dash="dash"),
            hovertemplate="<b>%{x|%H:%M}</b><br>MA Forecast: %{y:,.0f}<extra></extra>",
        ))
        fig.add_vrect(
            x0=actual_ma["ds"].max(), x1=forecast_ma["ds"].max(),
            fillcolor="rgba(200,150,62,0.04)", layer="below", line_width=0,
            annotation_text="Forecast Window", annotation_position="top left",
            annotation_font_color=COLORS["caramel"],
        )
        fig.update_xaxes(title="Time", tickformat="%H:%M", tickangle=30)
        if metric == "revenue":
            fig.update_yaxes(title="Revenue ($)", tickprefix="$")
        else:
            fig.update_yaxes(title="Quantity", tickformat=",")
        apply_plot_layout(fig, height=340)
        st.plotly_chart(fig, use_container_width=True)
        chart_note(f"Moving average forecast: {display_ma} over next {horizon} hours. Peak at {peak_hour}.")

# ── Prophet Forecast ──────────────────────────────────────────────────────────
if model_choice in ("Prophet", "All Models"):
    section_header("Prophet Time-Series Forecast")
    chart_label("Prophet Forecast with Confidence Intervals",
                "Facebook Prophet captures trend, seasonality and uncertainty bands")

    prophet_periods = st.slider("Prophet Horizon (days)", 7, 90, 30, key="prophet_slider")

    with st.spinner("☕ Fitting Prophet model…"):
        ts_prophet, fc_prophet = prophet_forecast(
            df, store=store_filter, target=metric, periods=prophet_periods, freq="D"
        )

    if fc_prophet is None:
        insight_card("Prophet requires at least 7 days of data. Ensure your dataset covers multiple days.", kind="warning")
    else:
        fig = go.Figure()
        hist_len = len(ts_prophet)
        fc_hist  = fc_prophet.iloc[:hist_len]
        fc_future = fc_prophet.iloc[hist_len:]

        fig.add_trace(go.Scatter(
            x=ts_prophet["ds"], y=ts_prophet["y"], mode="lines+markers", name="Actual",
            line=dict(color=COLORS["caramel"], width=2.5),
            marker=dict(size=4),
            hovertemplate="<b>%{x|%b %d}</b><br>Actual: $%{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=fc_future["ds"], y=fc_future["yhat"], mode="lines", name="Forecast",
            line=dict(color=COLORS["gold"], width=2.5, dash="dash"),
            hovertemplate="<b>%{x|%b %d}</b><br>Forecast: $%{y:,.0f}<extra></extra>",
        ))
        if "yhat_upper" in fc_future.columns and "yhat_lower" in fc_future.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([fc_future["ds"], fc_future["ds"][::-1]]),
                y=pd.concat([fc_future["yhat_upper"], fc_future["yhat_lower"][::-1]]),
                fill="toself", fillcolor="rgba(212,168,83,0.10)",
                line=dict(color="rgba(0,0,0,0)"), name="95% CI",
                hoverinfo="skip",
            ))
        fig.update_xaxes(title="Date", tickformat="%b %d")
        if metric == "revenue":
            fig.update_yaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
        else:
            fig.update_yaxes(title="Quantity", tickformat=",")
        apply_plot_layout(fig, height=380)
        st.plotly_chart(fig, use_container_width=True)

        fc_total_p = fc_future["yhat"].sum()
        display_p  = f"${fc_total_p:,.0f}" if metric == "revenue" else f"{fc_total_p:,.0f}"
        chart_note(f"Prophet {prophet_periods}-day forecast: {display_p}. Shaded band = 95% confidence interval.")

        col_pa, col_pb = st.columns(2)
        with col_pa:
            kpi_card(col_pa, "Prophet Forecast Total", display_p,               icon="🔮", color="gold")
        with col_pb:
            daily_avg_p = fc_future["yhat"].mean()
            display_daily = f"${daily_avg_p:,.0f}" if metric == "revenue" else f"{daily_avg_p:,.0f}"
            kpi_card(col_pb, "Avg Daily Forecast", display_daily,               icon="📅", color="orange")

# ── ARIMA Forecast ─────────────────────────────────────────────────────────────
if model_choice in ("ARIMA", "All Models"):
    section_header("ARIMA Time-Series Forecast")
    chart_label("ARIMA(2,1,2) Forecast",
                "Classical statistical forecasting using autoregressive integrated moving average")

    arima_periods = st.slider("ARIMA Horizon (days)", 7, 60, 14, key="arima_slider")

    with st.spinner("☕ Fitting ARIMA model…"):
        ts_arima, fc_arima = arima_forecast(
            df, store=store_filter, target=metric, periods=arima_periods
        )

    if fc_arima is None:
        insight_card("ARIMA requires statsmodels and at least 14 days of data. Check your dataset.", kind="warning")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts_arima["ds"], y=ts_arima["y"], mode="lines", name="Actual",
            line=dict(color=COLORS["caramel"], width=2.5),
            hovertemplate="<b>%{x|%b %d}</b><br>Actual: $%{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=fc_arima["ds"], y=fc_arima["yhat"], mode="lines+markers", name="ARIMA Forecast",
            line=dict(color="#5BB8C8", width=2.5, dash="dot"),
            marker=dict(size=6, color="#5BB8C8"),
            hovertemplate="<b>%{x|%b %d}</b><br>Forecast: $%{y:,.0f}<extra></extra>",
        ))
        fig.add_vrect(
            x0=ts_arima["ds"].max(), x1=fc_arima["ds"].max(),
            fillcolor="rgba(91,184,200,0.05)", layer="below", line_width=0,
            annotation_text="ARIMA Forecast", annotation_position="top left",
            annotation_font_color="#5BB8C8",
        )
        fig.update_xaxes(title="Date", tickformat="%b %d")
        if metric == "revenue":
            fig.update_yaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
        else:
            fig.update_yaxes(title="Quantity", tickformat=",")
        apply_plot_layout(fig, height=360)
        st.plotly_chart(fig, use_container_width=True)

        fc_total_a = fc_arima["yhat"].sum()
        display_a  = f"${fc_total_a:,.0f}" if metric == "revenue" else f"{fc_total_a:,.0f}"
        chart_note(f"ARIMA {arima_periods}-day forecast total: {display_a}. Use for short-range operational planning.")

# ── Model Comparison (All Models) ─────────────────────────────────────────────
if model_choice == "All Models":
    section_header("Model Comparison — Forecast Totals")
    chart_label("Projected Totals by Forecast Method",
                "Side-by-side output of all three forecasting approaches")
    rows = []
    if forecast_ma is not None:
        rows.append({"Model": "Moving Average", "Forecast Total": forecast_ma["yhat"].sum(), "Horizon": f"{horizon}h"})
    if fc_prophet is not None:
        rows.append({"Model": "Prophet",        "Forecast Total": fc_future["yhat"].sum(),   "Horizon": f"{prophet_periods}d"})
    if fc_arima is not None:
        rows.append({"Model": "ARIMA",          "Forecast Total": fc_arima["yhat"].sum(),    "Horizon": f"{arima_periods}d"})
    if rows:
        cmp_df = pd.DataFrame(rows)
        fig = go.Figure(go.Bar(
            x=cmp_df["Model"], y=cmp_df["Forecast Total"],
            marker_color=[COLORS["caramel"], COLORS["gold"], "#5BB8C8"][:len(rows)],
            text=cmp_df["Forecast Total"].apply(lambda x: f"${x:,.0f}" if metric == "revenue" else f"{x:,.0f}"),
            textposition="outside",
        ))
        if metric == "revenue":
            fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        apply_plot_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)
        chart_note("Compare outputs across models. Divergence signals forecast uncertainty — plan conservatively.")

# ── Hourly Breakdown ──────────────────────────────────────────────────────────
if forecast_ma is not None:
    col1, col2 = st.columns(2)
    with col1:
        section_header("Projected Revenue by Hour (MA)")
        chart_label("Hourly Projection Breakdown", "Revenue or quantity expected per hour")
        future_copy = future_ma.copy() if forecast_ma is not None else forecast_ma
        if future_copy is not None:
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
            chart_note("Higher-projected hours should be prioritised for staffing and inventory replenishment.")

    with col2:
        section_header("Detailed Forecast Table")
        chart_label("Hour-by-Hour MA Forecast", "Tabular view of projected values")
        display_df = future_ma[["ds", "yhat"]].copy()
        display_df["DateTime"] = display_df["ds"].dt.strftime("%Y-%m-%d %H:%M")
        display_df["Forecasted Value"] = display_df["yhat"].apply(
            lambda x: f"${x:,.2f}" if metric == "revenue" else f"{x:,.0f}"
        )
        st.dataframe(display_df[["DateTime", "Forecasted Value"]], use_container_width=True, hide_index=True)
        chart_note("Use granular hourly forecasts to plan staffing rotations and inventory pre-loading.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
insight_card("Prophet captures seasonality and trend automatically — best for multi-week operational planning.", kind="success")
insight_card("ARIMA is suited to stationary short-range series. Run both and compare totals before committing resources.", kind="info")
insight_card("Moving Average is fast and transparent — use it as a baseline sanity check for the advanced models.", kind="info")
insight_card("Forecast accuracy improves with more historical data. Re-train models weekly as new transactions accumulate.", kind="warning")
footer()

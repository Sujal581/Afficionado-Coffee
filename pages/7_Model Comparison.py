import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, no_data_warning, COLORS,
)
from utils import train_xgboost, train_random_forest, train_linear_regression

st.set_page_config(page_title="Model Comparison", layout="wide", page_icon="🤖")
inject_css()
sidebar_brand("Afficionado Coffee", "Model Comparison")
page_header("Model Comparison Dashboard", subtitle="Head-to-head evaluation across XGBoost, Random Forest & Linear Regression")

if not (st.session_state.get("df") is not None):
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Train Models ──────────────────────────────────────────────────────────────
with st.spinner("☕ Training all three models — this takes a moment..."):
    xgb = train_xgboost(df)
    rf  = train_random_forest(df)
    lr  = train_linear_regression(df)

comparison = pd.DataFrame({
    "Model": ["XGBoost", "Random Forest", "Linear Regression"],
    "Accuracy (%)": [xgb["accuracy"]*100, rf["accuracy"]*100, lr["accuracy"]*100],
    "MAE":          [xgb["mae"],      rf["mae"],      lr["mae"]],
    "RMSE":         [xgb["rmse"],     rf["rmse"],     lr["rmse"]],
    "R² Score":     [xgb["r2"],       rf["r2"],       lr["r2"]],
    "Recommended Staff": [xgb["staff"], rf["staff"],  lr["staff"]],
    "Peak Demand":  [xgb["peak_demand"], rf["peak_demand"], lr["peak_demand"]],
})

best_model   = max([("XGBoost", xgb["accuracy"]), ("Random Forest", rf["accuracy"]), ("Linear Regression", lr["accuracy"])], key=lambda x: x[1])
best_mae_row = comparison.loc[comparison["MAE"].idxmin()]
best_rmse_row= comparison.loc[comparison["RMSE"].idxmin()]
best_r2_row  = comparison.loc[comparison["R² Score"].idxmax()]

# ── Summary KPIs ──────────────────────────────────────────────────────────────
section_header("Model Performance Summary")
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Best Model",       best_model[0],                                    icon="👑", color="orange")
kpi_card(c2, "Best Accuracy",    f"{best_model[1]:.2f}%",                          icon="💯", color="green")
kpi_card(c3, "Highest Peak Demand", f"{max(xgb['peak_demand'], rf['peak_demand'], lr['peak_demand']):.0f}", icon="⚡", color="blue")
kpi_card(c4, "Max Staff Required",  f"{max(xgb['staff'], rf['staff'], lr['staff'])}", icon="👥", color="purple")

st.markdown("<br>", unsafe_allow_html=True)
c5, c6, c7 = st.columns(3)
kpi_card(c5, "Lowest MAE",  f"{best_mae_row['MAE']:.2f} ({best_mae_row['Model']})",   icon="📉", color="blue")
kpi_card(c6, "Lowest RMSE", f"{best_rmse_row['RMSE']:.2f} ({best_rmse_row['Model']})", icon="📊", color="gold")
kpi_card(c7, "Best R² Score", f"{best_r2_row['R² Score']:.3f} ({best_r2_row['Model']})", icon="📈", color="green")

# ── Comparison Table ───────────────────────────────────────────────────────────
section_header("Performance Comparison Table")
chart_label("All Metrics Side-by-Side", "Accuracy, MAE, RMSE, R², staffing, and peak demand")
st.dataframe(
    comparison.style
    .format({"Accuracy (%)": "{:.2f}%", "MAE": "{:.2f}", "RMSE": "{:.2f}", "R² Score": "{:.4f}"})
    .background_gradient(subset=["Accuracy (%)"], cmap="YlOrBr")
    .background_gradient(subset=["MAE", "RMSE"], cmap="YlOrBr_r")
    .background_gradient(subset=["R² Score"], cmap="YlOrBr"),
    use_container_width=True, hide_index=True,
)
chart_note("Warmer shading = better performance. For error metrics (MAE/RMSE), lower is better.")

# ── Chart Grid ────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    section_header("Accuracy Comparison")
    chart_label("Model Accuracy (%)", "Higher is better")
    model_colors = [COLORS["caramel"], COLORS["brown"], COLORS["gold"]]
    fig = go.Figure(go.Bar(
        x=comparison["Model"], y=comparison["Accuracy (%)"],
        marker_color=model_colors,
        text=comparison["Accuracy (%)"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        hovertemplate="%{x}<br>Accuracy: %{y:.2f}%<extra></extra>",
    ))
    fig.update_yaxes(range=[0, 115], title="Accuracy (%)")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("The highest bar represents the most reliable model for production demand forecasting.")

with col2:
    section_header("Error Metric Comparison")
    chart_label("MAE vs RMSE", "Lower values indicate better prediction precision")
    melted = comparison.melt(id_vars="Model", value_vars=["MAE", "RMSE"], var_name="Metric", value_name="Value")
    fig = px.bar(
        melted, x="Model", y="Value", color="Metric", barmode="group",
        color_discrete_map={"MAE": COLORS["caramel"], "RMSE": COLORS["espresso"]},
    )
    fig.update_yaxes(title="Error Value")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("MAE measures average magnitude; RMSE penalises large errors more heavily.")

col3, col4 = st.columns(2)

with col3:
    section_header("R² Score Comparison")
    chart_label("Variance Explained", "Closer to 1.0 is better")
    fig = go.Figure(go.Bar(
        x=comparison["Model"], y=comparison["R² Score"],
        marker_color=[COLORS["caramel"], COLORS["gold"], COLORS["brown"]],
        text=comparison["R² Score"].apply(lambda x: f"{x:.3f}"),
        textposition="outside",
        hovertemplate="%{x}<br>R²: %{y:.4f}<extra></extra>",
    ))
    fig.update_yaxes(range=[0, 0.01], title="R² Score")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("An R² of 1.0 means the model perfectly explains demand variance.")

with col4:
    section_header("Staffing Recommendations")
    chart_label("Peak Staff Count by Model", "Recommended headcount for peak hour")
    fig = go.Figure(go.Bar(
        x=comparison["Model"], y=comparison["Recommended Staff"],
        marker=dict(
            color=comparison["Recommended Staff"],
            colorscale=[[0, COLORS["espresso"]], [1, COLORS["caramel"]]],
            showscale=False,
        ),
        text=comparison["Recommended Staff"].astype(int),
        textposition="outside",
        hovertemplate="%{x}<br>Staff: %{y}<extra></extra>",
    ))
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("Staff count = peak predicted demand ÷ 50 transactions per staff member.")

# ── Radar Chart ───────────────────────────────────────────────────────────────
section_header("Radar Chart — Multi-Metric Overview")
chart_label("Normalised Model Performance", "All metrics scaled 0–1 for fair comparison")

norm = comparison.copy()
for col in ["Accuracy (%)", "R² Score"]:
    norm[col] = norm[col] / norm[col].max()
for col in ["MAE", "RMSE"]:
    norm[col] = 1 - (norm[col] / norm[col].max())

categories = ["Accuracy", "R² Score", "Low MAE", "Low RMSE"]
radar_colors = [COLORS["caramel"], COLORS["gold"], COLORS["brown"]]
fig = go.Figure()
for i, row in norm.iterrows():
    vals = [row["Accuracy (%)"], row["R² Score"], row["MAE"], row["RMSE"]]
    vals += vals[:1]
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=categories + [categories[0]],
        fill="toself", name=row["Model"],
        line_color=radar_colors[i % 3],
        fillcolor=f"rgba({','.join(str(int(c, 16)) for c in [radar_colors[i % 3][1:3], radar_colors[i % 3][3:5], radar_colors[i % 3][5:7]])},0.08)",
    ))
fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
apply_plot_layout(fig, height=420)
st.plotly_chart(fig, use_container_width=True)
chart_note("A larger polygon area = overall better performance across all metrics.")

# ── Peak Demand ────────────────────────────────────────────────────────────────
section_header("Peak Demand Comparison")
chart_label("Maximum Predicted Demand by Model", "Upper bound each model forecasts")
fig = go.Figure(go.Bar(
    x=comparison["Model"], y=comparison["Peak Demand"],
    marker_color=[COLORS["caramel"], COLORS["gold"], COLORS["brown"]],
    text=comparison["Peak Demand"].apply(lambda x: f"{x:.0f}"),
    textposition="outside",
    hovertemplate="%{x}<br>Peak: %{y:.0f} units<extra></extra>",
))
apply_plot_layout(fig, height=320)
st.plotly_chart(fig, use_container_width=True)
chart_note("Variance in peak demand across models reflects forecasting uncertainty — plan conservatively.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
insight_card(f"{best_model[0]} achieves the highest accuracy at {best_model[1]:.2f}% — recommended for production demand forecasting.", kind="success")
insight_card(f"{best_mae_row['Model']} delivers the lowest MAE of {best_mae_row['MAE']:.2f} units — ideal for minimising average prediction error.", kind="info")
insight_card("Linear Regression may underperform on complex seasonal patterns — use it as a baseline benchmark rather than a production model.", kind="warning")
insight_card("Ensemble models (XGBoost, Random Forest) capture non-linear demand patterns better and are preferred for operational decisions.", kind="success")
insight_card("Retrain models monthly as new transaction data accumulates to maintain forecast accuracy over time.", kind="warning")
insight_card("For critical planning periods (holidays, promotions), prefer the model with lowest RMSE to avoid large staffing errors.", kind="info")
footer()

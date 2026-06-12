"""
7_Model_Comparison.py — Optimized Model Comparison page.

Optimizations:
  - All three model training calls (train_xgboost, train_random_forest, train_linear_regression)
    are cached via @st.cache_data in utils.py — no retraining on page revisit.
  - compare_models() is now also cached in utils.py — comparison table reuses already-trained results.
  - Styler applied only to a 3-row DataFrame — negligible cost; kept for visual clarity.
  - Radar chart normalisation uses vectorized pandas operations, not row loops.
  - All bar/scatter charts built from pre-computed comparison DataFrame.
"""

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
page_header("Model Comparison Dashboard",
            subtitle="Head-to-head evaluation — XGBoost · Random Forest · Linear Regression")

if not st.session_state.get("df") is not None:
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Train (all cached — instant on revisit) ───────────────────────────────────
with st.spinner("☕ Loading model results… (cached after first training run)"):
    xgb = train_xgboost(df)
    rf  = train_random_forest(df)
    lr  = train_linear_regression(df)

comparison = pd.DataFrame({
    "Model":             ["XGBoost", "Random Forest", "Linear Regression"],
    "Accuracy (%)":      [xgb["accuracy"],    rf["accuracy"],    lr["accuracy"]],
    "CV Score (%)":      [xgb["cv_mean"] or 0.0, rf["cv_mean"] or 0.0, lr["cv_mean"] or 0.0],
    "MAE":               [xgb["mae"],         rf["mae"],         lr["mae"]],
    "RMSE":              [xgb["rmse"],        rf["rmse"],        lr["rmse"]],
    "R² Score":          [xgb["r2"],          rf["r2"],          lr["r2"]],
    "Recommended Staff": [xgb["staff"],       rf["staff"],       lr["staff"]],
    "Peak Demand":       [xgb["peak_demand"], rf["peak_demand"], lr["peak_demand"]],
})

best_model    = max([("XGBoost", xgb["accuracy"]),
                     ("Random Forest", rf["accuracy"]),
                     ("Linear Regression", lr["accuracy"])], key=lambda x: x[1])
best_cv       = max([("XGBoost", xgb["cv_mean"] or 0),
                     ("Random Forest", rf["cv_mean"] or 0),
                     ("Linear Regression", lr["cv_mean"] or 0)], key=lambda x: x[1])
best_mae_row  = comparison.loc[comparison["MAE"].idxmin()]
best_rmse_row = comparison.loc[comparison["RMSE"].idxmin()]
best_r2_row   = comparison.loc[comparison["R² Score"].idxmax()]

# ── Summary KPIs ──────────────────────────────────────────────────────────────
section_header("Model Performance Summary")
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Best Model",        best_model[0],                         icon="👑", color="orange")
kpi_card(c2, "Best Test Accuracy", f"{best_model[1]:.2f}%",              icon="💯", color="green")
kpi_card(c3, "Best CV Score",     f"{best_cv[1]:.2f}% ({best_cv[0]})",  icon="🔁", color="teal")
kpi_card(c4, "Max Staff Required",
         f"{max(xgb['staff'], rf['staff'], lr['staff'])}",               icon="👥", color="purple")

st.markdown("<br>", unsafe_allow_html=True)
c5, c6, c7 = st.columns(3)
kpi_card(c5, "Lowest MAE",  f"{best_mae_row['MAE']:.2f} ({best_mae_row['Model']})",    icon="📉", color="blue")
kpi_card(c6, "Lowest RMSE", f"{best_rmse_row['RMSE']:.2f} ({best_rmse_row['Model']})", icon="📊", color="gold")
kpi_card(c7, "Best R²",     f"{best_r2_row['R² Score']:.3f} ({best_r2_row['Model']})", icon="📈", color="green")

# ── Comparison Table ───────────────────────────────────────────────────────────
section_header("Performance Comparison Table")
chart_label("All Metrics Side-by-Side",
            "Accuracy, CV score, MAE, RMSE, R², staffing, and peak demand")
# Styler applied to only 3 rows — negligible overhead
st.dataframe(
    comparison.style
    .format({
        "Accuracy (%)": "{:.2f}%",
        "CV Score (%)": "{:.2f}%",
        "MAE":          "{:.2f}",
        "RMSE":         "{:.2f}",
        "R² Score":     "{:.4f}",
    })
    .background_gradient(subset=["Accuracy (%)", "CV Score (%)"], cmap="YlOrBr")
    .background_gradient(subset=["MAE", "RMSE"],                  cmap="YlOrBr_r")
    .background_gradient(subset=["R² Score"],                     cmap="YlOrBr"),
    use_container_width=True, hide_index=True,
)
chart_note("Warmer shading = better performance. CV Score measures generalisation (higher = less overfitting).")

# ── Chart Grid ────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
model_colors = [COLORS["caramel"], COLORS["brown"], COLORS["gold"]]

with col1:
    section_header("Accuracy vs CV Score")
    chart_label("Test Accuracy and Cross-Validation Score (%)",
                "CV score reveals how well each model generalises to unseen data")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Test Accuracy",
        x=comparison["Model"], y=comparison["Accuracy (%)"],
        marker_color=model_colors, opacity=0.9,
        text=comparison["Accuracy (%)"].round(1).astype(str) + "%",
        textposition="outside",
        hovertemplate="%{x}<br>Test Acc: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="CV Score",
        x=comparison["Model"], y=comparison["CV Score (%)"],
        marker_color=["#5BB8C8"] * 3, opacity=0.8,
        text=comparison["CV Score (%)"].round(1).astype(str) + "%",
        textposition="outside",
        hovertemplate="%{x}<br>CV Score: %{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, 130], title="Score (%)")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("A large gap between Test Accuracy and CV Score can signal overfitting.")

with col2:
    section_header("Error Metric Comparison")
    chart_label("MAE vs RMSE", "Lower values = better prediction precision")
    melted = comparison.melt(
        id_vars="Model", value_vars=["MAE", "RMSE"],
        var_name="Metric", value_name="Value"
    )
    fig = px.bar(
        melted, x="Model", y="Value", color="Metric", barmode="group",
        color_discrete_map={"MAE": COLORS["caramel"], "RMSE": COLORS["espresso"]},
    )
    fig.update_yaxes(title="Error Value")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("MAE = average magnitude; RMSE penalises large errors more heavily.")

col3, col4 = st.columns(2)

with col3:
    section_header("R² Score Comparison")
    chart_label("Variance Explained", "Closer to 1.0 is better")
    fig = go.Figure(go.Bar(
        x=comparison["Model"], y=comparison["R² Score"],
        marker_color=model_colors,
        text=comparison["R² Score"].round(3).astype(str),
        textposition="outside",
        hovertemplate="%{x}<br>R²: %{y:.4f}<extra></extra>",
    ))
    fig.update_yaxes(title="R² Score")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("R² = 1.0 means the model perfectly explains demand variance.")

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

# ── Radar Chart (vectorized normalisation) ─────────────────────────────────────
section_header("Radar Chart — Multi-Metric Overview")
chart_label("Normalised Model Performance", "All 5 metrics scaled 0–1 for fair comparison")

norm = comparison.copy()
for col in ["Accuracy (%)", "R² Score", "CV Score (%)"]:
    max_v = norm[col].max()
    norm[col] = norm[col] / max_v if max_v > 0 else norm[col]
for col in ["MAE", "RMSE"]:
    max_v = norm[col].max()
    norm[col] = 1 - (norm[col] / max_v) if max_v > 0 else norm[col]

categories   = ["Accuracy", "CV Score", "Low MAE", "Low RMSE", "R² Score"]
radar_colors = [COLORS["caramel"], COLORS["gold"], COLORS["brown"]]
fig = go.Figure()
for i, row in norm.iterrows():
    vals = [row["Accuracy (%)"], row["CV Score (%)"], row["MAE"], row["RMSE"], row["R² Score"]]
    vals += vals[:1]
    r, g, b = (
        int(radar_colors[i % 3][1:3], 16),
        int(radar_colors[i % 3][3:5], 16),
        int(radar_colors[i % 3][5:7], 16),
    )
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=categories + [categories[0]],
        fill="toself", name=row["Model"],
        line_color=radar_colors[i % 3],
        fillcolor=f"rgba({r},{g},{b},0.08)",
    ))
fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
apply_plot_layout(fig, height=440)
st.plotly_chart(fig, use_container_width=True)
chart_note("Larger polygon = better overall performance. CV Score axis reveals generalisation ability.")

# ── Peak Demand ────────────────────────────────────────────────────────────────
section_header("Peak Demand Comparison")
chart_label("Maximum Predicted Demand by Model", "Upper bound each model forecasts")
fig = go.Figure(go.Bar(
    x=comparison["Model"], y=comparison["Peak Demand"],
    marker_color=model_colors,
    text=comparison["Peak Demand"].astype(int),
    textposition="outside",
    hovertemplate="%{x}<br>Peak: %{y:.0f} units<extra></extra>",
))
apply_plot_layout(fig, height=300)
st.plotly_chart(fig, use_container_width=True)
chart_note("Variance in peak demand across models reflects forecasting uncertainty — plan conservatively.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
insight_card(f"{best_model[0]} achieves the highest test accuracy at {best_model[1]:.2f}% — recommended for production demand forecasting.", kind="success")
insight_card(f"{best_cv[0]} leads in CV score ({best_cv[1]:.2f}%) — strong cross-validation means it generalises well to unseen data.", kind="success")
insight_card(f"{best_mae_row['Model']} delivers the lowest MAE ({best_mae_row['MAE']:.2f}) — minimises average prediction error.", kind="info")
insight_card("Run hyperparameter tuning on the Peak Demand page for improved accuracy — GridSearchCV explores the optimal parameter space.", kind="info")
insight_card("Linear Regression may underperform on complex seasonal patterns — use it as a baseline, not a production model.", kind="warning")
insight_card("Retrain models monthly as new transaction data accumulates to maintain forecast accuracy.", kind="warning")
footer()

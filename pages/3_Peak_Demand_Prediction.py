"""
3_Peak_Demand_Prediction.py — Optimized Peak Demand Prediction page.

Optimizations:
  - train_xgboost / train_random_forest / train_linear_regression are cached in utils.py.
    Re-visiting this page (or toggling unrelated widgets) no longer retrains models.
  - tune=False path is cached separately from tune=True, so the fast path stays fast.
  - Feature importance arrays read directly from the already-trained model — no extra pass.
  - render_model_tab() builds DataFrames once per call, no repeated re-computation.
  - Plotly figures use head(20) / head(50) slices — not full prediction arrays.
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

st.set_page_config(page_title="Peak Demand Prediction", layout="wide", page_icon="⚡")
inject_css()
sidebar_brand("Afficionado Coffee", "Peak Demand")
page_header("Peak Demand Prediction", subtitle="ML demand forecasting with optional hyperparameter tuning")

if not st.session_state.get("df") is not None:
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Model Configuration ────────────────────────────────────────────────────────
section_header("Model Configuration")
col_cfg1, col_cfg2 = st.columns([2, 1])
with col_cfg1:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.83rem;color:#b8956e;line-height:1.7;padding:0.6rem 0;">
            Enable <strong style="color:#C8963E;">hyperparameter tuning</strong> to run GridSearchCV (3-fold CV)
            across parameter grids for XGBoost and Random Forest.
            This finds optimal settings automatically but takes longer to train.
            Results are <strong>cached</strong> — tuning only runs once per dataset.
        </div>
    """, unsafe_allow_html=True)
with col_cfg2:
    tune = st.toggle("Enable Hyperparameter Tuning", value=False)

if tune:
    insight_card("Hyperparameter tuning active — GridSearchCV (3-fold) will run. Results are cached after the first run.", kind="warning")

section_header("Dashboard Overview")
col1, col2, col3, col4 = st.columns(4)
kpi_card(col1, "Peak Demand Prediction", "Predict peak periods",    icon="⚡", color="orange")
kpi_card(col2, "Model Accuracy",         "ML evaluation metrics",  icon="✅", color="green")
kpi_card(col3, "Staffing Intelligence",  "Data-driven headcount",  icon="👥", color="blue")
kpi_card(col4, "Hyperparameter Tuning",  "On" if tune else "Off",  icon="🔧", color="purple" if tune else "orange")

st.markdown("---")


def render_model_tab(result: dict, model_name: str) -> pd.DataFrame:
    """Render metrics, charts and insights for a single trained model."""
    # actual/predictions are now plain lists (not Series/ndarray) — convert for DataFrame use
    actual_arr = np.array(result["actual"])
    pred_arr   = np.array(result["predictions"])
    plot_df = pd.DataFrame({
        "Actual":    result["actual"].values,
        "Predicted": result["predictions"].round(1),
        "Actual":    actual_arr,
        "Predicted": pred_arr.round(1),
    })
    plot_df["Error"] = plot_df["Actual"] - plot_df["Predicted"]

    section_header("Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Accuracy (%)",  f"{result['accuracy']:.2f}%",    icon="✅", color="green")
    kpi_card(c2, "MAE",           f"{result['mae']:.2f}",          icon="📉", color="red")
    kpi_card(c3, "Peak Demand",   f"{result['peak_demand']:.0f}",  icon="⚡", color="orange")
    kpi_card(c4, "Staff Needed",  f"{result['staff']:.0f}",        icon="👥", color="blue")

    if result.get("cv_mean") is not None:
        c5, c6 = st.columns(2)
        kpi_card(c5, "CV Score (5-fold)", f"{result['cv_mean']:.2f}%", icon="🔁", color="teal")
        kpi_card(c6, "CV Std Dev",        f"±{result['cv_std']:.2f}%", icon="📊", color="gold")

    if result.get("best_params"):
        params_html = " &nbsp;|&nbsp; ".join(
            [f"<code style='color:#d4b896'>{k}</code> = <strong>{v}</strong>"
             for k, v in result["best_params"].items()]
        )
        st.markdown(f"""
            <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#C8963E;
                        background:rgba(200,150,62,0.07);border:1px solid rgba(200,150,62,0.2);
                        border-radius:8px;padding:0.7rem 1rem;margin:0.75rem 0;">
                <strong>Best hyperparameters found by GridSearchCV:</strong><br>
                {params_html}
            </div>
        """, unsafe_allow_html=True)

    # Actual vs Predicted (first 20 samples)
    section_header("Actual vs Predicted Demand")
    chart_label(f"{model_name} — Prediction Comparison", "Ground truth vs model output (first 20 samples)")
    compare_df = plot_df.head(20).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Actual", x=compare_df.index, y=compare_df["Actual"],
        marker_color=COLORS["caramel"], opacity=0.85,
        hovertemplate="Sample %{x}<br>Actual: %{y:,.1f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Predicted", x=compare_df.index, y=compare_df["Predicted"],
        marker_color=COLORS["cream"], opacity=0.75,
        hovertemplate="Sample %{x}<br>Predicted: %{y:,.1f}<extra></extra>",
    ))
    fig.update_layout(barmode="group")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note(f"{model_name}: accuracy {result['accuracy']:.2f}%, MAE {result['mae']:.2f}. Peak ≈ {result['peak_demand']:.0f} units.")

    # Prediction Timeline (first 50 samples)
    section_header("Prediction Timeline")
    chart_label("Actual vs Predicted Over Time", "First 50 samples with trend overlay")
    tdf = plot_df.head(50)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tdf.index, y=tdf["Actual"], mode="lines+markers", name="Actual",
        line=dict(color=COLORS["caramel"], width=2.5), marker=dict(size=5),
        hovertemplate="Sample %{x}<br>Actual: %{y:,.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=tdf.index, y=tdf["Predicted"], mode="lines+markers", name="Predicted",
        line=dict(color=COLORS["cream"], width=2, dash="dash"), marker=dict(size=5),
        hovertemplate="Sample %{x}<br>Predicted: %{y:,.1f}<extra></extra>",
    ))
    fig.update_yaxes(title="Demand (Units)")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

    col_err, col_res = st.columns(2)
    with col_err:
        section_header("Error Distribution")
        fig = px.histogram(plot_df, x="Error", nbins=30, color_discrete_sequence=[COLORS["caramel"]])
        fig.update_xaxes(title="Prediction Error (Actual − Predicted)")
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
        chart_note("A distribution centred near zero = low bias.")

    with col_res:
        section_header("Residual Analysis")
        fig = px.scatter(plot_df, x="Predicted", y="Error",
                         color_discrete_sequence=[COLORS["brown"]], opacity=0.7)
        fig.add_hline(y=0, line_color=COLORS["caramel"], line_dash="dash")
        fig.update_xaxes(title="Predicted Value")
        fig.update_yaxes(title="Residual")
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
        chart_note("Points clustered around the zero line confirm unbiased predictions.")

    return plot_df


tab1, tab2, tab3 = st.tabs(["🚀 XGBoost", "🌲 Random Forest", "📈 Linear Regression"])

with tab1:
    with st.spinner("☕ Training XGBoost" + (" with hyperparameter tuning…" if tune else "… (cached after first run)")):
        result_xgb = train_xgboost(df, tune=tune)
    plot_df = render_model_tab(result_xgb, "XGBoost")

    feature_importance = pd.DataFrame({
        "Feature":    ["hour", "month", "day", "weekday_num"],
        "Importance": result_xgb["model"].feature_importances_,
    }).sort_values("Importance", ascending=False)

    col3, col4 = st.columns(2)
    with col3:
        section_header("Demand Distribution")
        fig = px.box(
            pd.DataFrame({"Predicted Demand": result_xgb["predictions"]}),
            y="Predicted Demand", color_discrete_sequence=[COLORS["caramel"]],
        )
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        section_header("Feature Importance")
        fig = go.Figure(go.Bar(
            x=feature_importance["Importance"], y=feature_importance["Feature"],
            orientation="h",
            marker=dict(
                color=feature_importance["Importance"],
                colorscale=[[0, COLORS["espresso"]], [1, COLORS["caramel"]]],
                showscale=False,
            ),
        ))
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    section_header("Insights & Recommendations")
    insight_card(f"XGBoost accuracy {result_xgb['accuracy']:.2f}%, MAE {result_xgb['mae']:.2f}.", kind="success")
    insight_card(f"Peak demand ≈ {result_xgb['peak_demand']:.0f} units — allocate {result_xgb['staff']:.0f} staff during peak.", kind="info")
    if result_xgb.get("cv_mean"):
        insight_card(f"Cross-validation score: {result_xgb['cv_mean']:.2f}% ± {result_xgb['cv_std']:.2f}% — confirms generalisation.", kind="success")
    insight_card(f"{feature_importance.iloc[0]['Feature'].title()} is the most influential forecasting feature.", kind="warning")

with tab2:
    with st.spinner("☕ Training Random Forest" + (" with hyperparameter tuning…" if tune else "… (cached after first run)")):
        result_rf = train_random_forest(df, tune=tune)
    plot_df = render_model_tab(result_rf, "Random Forest")

    importance_df = pd.DataFrame({
        "Feature":    ["hour", "month", "day", "weekday_num"],
        "Importance": result_rf["model"].feature_importances_,
    }).sort_values("Importance", ascending=False)

    col3, col4 = st.columns(2)
    with col3:
        section_header("Demand Distribution")
        fig = px.box(
            pd.DataFrame({"Predicted Demand": result_rf["predictions"]}),
            y="Predicted Demand", color_discrete_sequence=[COLORS["brown"]],
        )
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        section_header("Feature Importance")
        fig = go.Figure(go.Bar(
            x=importance_df["Importance"], y=importance_df["Feature"],
            orientation="h",
            marker=dict(
                color=importance_df["Importance"],
                colorscale=[[0, COLORS["espresso"]], [1, COLORS["gold"]]],
                showscale=False,
            ),
        ))
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    section_header("Insights & Recommendations")
    insight_card(f"Random Forest accuracy {result_rf['accuracy']:.2f}%, RMSE {result_rf['rmse']:.2f}.", kind="success")
    insight_card(f"Peak demand ≈ {result_rf['peak_demand']:.0f} units — maintain {result_rf['staff']:.0f} staff at peak.", kind="info")
    if result_rf.get("cv_mean"):
        insight_card(f"CV score: {result_rf['cv_mean']:.2f}% ± {result_rf['cv_std']:.2f}% — ensemble averaging reduces variance well.", kind="success")
    insight_card(f"{importance_df.iloc[0]['Feature'].title()} drives demand predictions most strongly.", kind="warning")

with tab3:
    with st.spinner("☕ Training Linear Regression… (cached after first run)"):
        result_lr = train_linear_regression(df)
    plot_df = render_model_tab(result_lr, "Linear Regression")

    coef_df = pd.DataFrame({
        "Feature":     ["hour", "month", "day", "weekday_num"],
        "Coefficient": result_lr["model"].coef_,
    }).sort_values("Coefficient", ascending=False)

    col3, col4 = st.columns(2)
    with col3:
        section_header("Demand Distribution")
        dist_df = pd.concat([
            pd.DataFrame({"Value": plot_df["Actual"],    "Type": "Actual"}),
            pd.DataFrame({"Value": plot_df["Predicted"], "Type": "Predicted"}),
        ])
        fig = px.box(dist_df, x="Type", y="Value", color="Type",
                     color_discrete_map={"Actual": COLORS["caramel"], "Predicted": COLORS["cream"]})
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        section_header("Feature Coefficients")
        fig = go.Figure(go.Bar(
            x=coef_df["Coefficient"], y=coef_df["Feature"],
            orientation="h", marker_color="#6BA3D4",
        ))
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    section_header("Insights & Recommendations")
    insight_card(f"Linear Regression accuracy {result_lr['accuracy']:.2f}%, R² {result_lr['r2']:.3f}.", kind="success")
    insight_card(f"Peak demand ≈ {result_lr['peak_demand']:.0f} units — ensure {result_lr['staff']:.0f} staff coverage.", kind="info")
    if result_lr.get("cv_mean"):
        insight_card(f"CV score: {result_lr['cv_mean']:.2f}% — use as a baseline benchmark against ensemble models.", kind="info")
    insight_card(f"{coef_df.iloc[0]['Feature'].title()} has the strongest coefficient — monitor closely.", kind="warning")

footer()

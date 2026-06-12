"""
6_Scenario_Analysis.py — Optimized Scenario Analysis page.

Optimizations:
  - calculate_kpis() cached — base KPIs computed once per dataset.
  - All scenario math is pure Python scalars — no DataFrame operations on rerun.
  - Sensitivity curves built with numpy arrays (vectorized) instead of list comprehensions.
  - Store breakdown aggregation cached at page level via st.session_state.
  - Plotly figures use pre-built DataFrames — no inline groupby.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, no_data_warning, COLORS,
)
from utils import calculate_kpis

st.set_page_config(page_title="Scenario Analysis", layout="wide", page_icon="🎯")
inject_css()
sidebar_brand("Afficionado Coffee", "Scenario Analysis")

with st.sidebar:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.68rem;color:#4a3020;
                    letter-spacing:0.15em;text-transform:uppercase;margin:1rem 0 0.5rem 0;">
            Scenario Parameters
        </div>
    """, unsafe_allow_html=True)
    demand_change = st.slider("Demand Change (%)",         -50, 100,  20, step=5)
    price_change  = st.slider("Price Change (%)",          -30,  50,  10, step=5)
    cost_change   = st.slider("Operating Cost Change (%)", -20,  50,   5, step=5)
    new_stores    = st.slider("New Stores to Open",          0,   5,   1)

page_header("Scenario Analysis Dashboard", subtitle="What-if modelling for revenue, profit, and expansion planning")

if not st.session_state.get("df") is not None:
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Cached base KPIs ──────────────────────────────────────────────────────────
kpis              = calculate_kpis(df)
base_revenue      = kpis["Revenue"]
base_transactions = kpis["Transactions"]
base_avg_order    = kpis["Avg_Order_Value"]
num_stores        = df["store_location"].nunique() if "store_location" in df.columns else 1
revenue_per_store = base_revenue / max(num_stores, 1)

# ── Scenario Math (scalar ops — instant on every slider change) ───────────────
scenario_revenue      = (
    base_revenue * (1 + demand_change / 100) * (1 + price_change / 100)
    + new_stores * revenue_per_store * (1 + demand_change / 100)
)
scenario_transactions = base_transactions * (1 + demand_change / 100)
scenario_avg_order    = base_avg_order * (1 + price_change / 100)
assumed_cost_base     = base_revenue * 0.6
base_profit           = base_revenue - assumed_cost_base
scenario_cost         = assumed_cost_base * (1 + cost_change / 100) + (new_stores * assumed_cost_base / num_stores)
scenario_profit       = scenario_revenue - scenario_cost
revenue_delta         = scenario_revenue - base_revenue
profit_delta          = scenario_profit - base_profit

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Scenario Key Metrics")
col1, col2, col3, col4 = st.columns(4)
kpi_card(col1, "Projected Revenue",
         f"${scenario_revenue:,.0f}",
         icon="💰", color="green" if revenue_delta >= 0 else "red")
kpi_card(col2, "Revenue Change",
         f"{'+'  if revenue_delta >= 0 else ''}{revenue_delta:,.0f}",
         icon="📈" if revenue_delta >= 0 else "📉",
         color="green" if revenue_delta >= 0 else "red")
kpi_card(col3, "Projected Profit",
         f"${scenario_profit:,.0f}",
         icon="💵", color="green" if profit_delta >= 0 else "red")
kpi_card(col4, "Profit Change",
         f"{'+'  if profit_delta >= 0 else ''}{profit_delta:,.0f}",
         icon="✅" if profit_delta >= 0 else "⚠️",
         color="green" if profit_delta >= 0 else "orange")

st.markdown("<br>", unsafe_allow_html=True)

# ── Baseline vs Scenario ───────────────────────────────────────────────────────
section_header("Scenario vs Baseline Comparison")
chart_label("Key Metrics: Baseline vs Scenario", "Side-by-side impact of your scenario settings")

compare_data = pd.DataFrame({
    "Metric":   ["Revenue", "Transactions", "Avg Order Value", "Profit"],
    "Baseline": [base_revenue, base_transactions, base_avg_order, base_profit],
    "Scenario": [scenario_revenue, scenario_transactions, scenario_avg_order, scenario_profit],
})
compare_data["Change (%)"] = (
    (compare_data["Scenario"] - compare_data["Baseline"]) / compare_data["Baseline"].abs() * 100
).round(1)

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Baseline", x=compare_data["Metric"], y=compare_data["Baseline"],
    marker_color=COLORS["espresso"],
    text=compare_data["Baseline"].apply(lambda x: f"${x:,.0f}" if x > 100 else f"{x:.1f}"),
    textposition="outside",
    hovertemplate="%{x}<br>Baseline: $%{y:,.0f}<extra></extra>",
))
fig.add_trace(go.Bar(
    name="Scenario", x=compare_data["Metric"], y=compare_data["Scenario"],
    marker_color=COLORS["caramel"] if revenue_delta >= 0 else "#E07070",
    text=compare_data["Scenario"].apply(lambda x: f"${x:,.0f}" if x > 100 else f"{x:.1f}"),
    textposition="outside",
    hovertemplate="%{x}<br>Scenario: $%{y:,.0f}<extra></extra>",
))
fig.update_layout(barmode="group")
apply_plot_layout(fig, height=360)
st.plotly_chart(fig, use_container_width=True)
chart_note("Gold bars above dark bars indicate a positive scenario impact.")

# ── Sensitivity Analysis (vectorized numpy) ────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    section_header("Revenue Sensitivity — Demand")
    chart_label("Revenue vs Demand Change (%)", "How revenue responds across a range of demand shifts")
    demand_arr    = np.arange(-50, 101, 10)
    rev_sens      = (
        base_revenue * (1 + demand_arr / 100) * (1 + price_change / 100)
        + new_stores * revenue_per_store * (1 + demand_arr / 100)
    )
    sens_df = pd.DataFrame({"Demand Change (%)": demand_arr, "Revenue": rev_sens})
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sens_df["Demand Change (%)"], y=sens_df["Revenue"],
        mode="lines+markers",
        line=dict(color=COLORS["caramel"], width=3),
        marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(200,150,62,0.07)",
        hovertemplate="Demand %{x}%<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_vline(x=demand_change, line_dash="dash", line_color=COLORS["brown"],
                  annotation_text=f"Current: {demand_change}%",
                  annotation_font_color=COLORS["brown"])
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("The dashed line marks your current setting. Slide left to model downturns, right for growth.")

with col2:
    section_header("Revenue Sensitivity — Price")
    chart_label("Revenue vs Price Change (%)", "Revenue impact across a range of price adjustments")
    price_arr   = np.arange(-30, 51, 5)
    price_sens  = (
        base_revenue * (1 + demand_change / 100) * (1 + price_arr / 100)
        + new_stores * revenue_per_store
    )
    price_df = pd.DataFrame({"Price Change (%)": price_arr, "Revenue": price_sens})
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=price_df["Price Change (%)"], y=price_df["Revenue"],
        mode="lines+markers",
        line=dict(color=COLORS["gold"], width=3),
        marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(212,168,83,0.07)",
        hovertemplate="Price %{x}%<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_vline(x=price_change, line_dash="dash", line_color=COLORS["brown"],
                  annotation_text=f"Current: {price_change}%",
                  annotation_font_color=COLORS["brown"])
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("The dashed line marks your current price setting. Steeper slopes = higher price elasticity.")

# ── Profit Sensitivity ────────────────────────────────────────────────────────
section_header("Profit Sensitivity — Operating Cost")
chart_label("Profit vs Cost Change (%)", "How operating cost shifts affect bottom-line profit")

cost_arr   = np.arange(-20, 51, 5)
profit_arr = scenario_revenue - (assumed_cost_base * (1 + cost_arr / 100) + new_stores * assumed_cost_base / num_stores)
cost_df    = pd.DataFrame({"Cost Change (%)": cost_arr, "Profit": profit_arr})

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=cost_df["Cost Change (%)"], y=cost_df["Profit"],
    mode="lines+markers",
    line=dict(color="#6BBF8E", width=3),
    marker=dict(size=7),
    fill="tozeroy", fillcolor="rgba(107,191,142,0.07)",
    hovertemplate="Cost %{x}%<br>Profit: $%{y:,.0f}<extra></extra>",
))
fig.add_vline(x=cost_change, line_dash="dash", line_color=COLORS["brown"],
              annotation_text=f"Current: {cost_change}%",
              annotation_font_color=COLORS["brown"])
fig.add_hline(y=0, line_dash="dot", line_color="#E07070",
              annotation_text="Break-even", annotation_font_color="#E07070")
fig.update_yaxes(tickprefix="$", tickformat=",.0f")
apply_plot_layout(fig)
st.plotly_chart(fig, use_container_width=True)
chart_note("Red dotted line = break-even. Keep costs below this threshold to maintain profitability.")

# ── Store Expansion ────────────────────────────────────────────────────────────
if new_stores > 0:
    section_header("Store Expansion Impact")
    chart_label(f"Projected Revenue with {new_stores} New Store(s)", "Incremental revenue from expansion")
    expansion_arr = np.arange(0, 6)
    exp_rev       = base_revenue * (1 + demand_change / 100) * (1 + price_change / 100) + expansion_arr * revenue_per_store
    exp_df        = pd.DataFrame({"New Stores": expansion_arr, "Revenue": exp_rev})
    exp_df["label"] = "$" + (exp_df["Revenue"] / 1000).round(0).astype(int).astype(str) + "k"
    fig = go.Figure(go.Bar(
        x=exp_df["New Stores"], y=exp_df["Revenue"],
        marker=dict(
            color=exp_df["Revenue"],
            colorscale=[[0, COLORS["espresso"]], [1, COLORS["caramel"]]],
            showscale=False,
        ),
        text=exp_df["label"],
        textposition="outside",
        hovertemplate="%{x} new stores<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(title="Number of New Stores", tickmode="linear")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note(f"Each new store adds ~${revenue_per_store:,.0f} in baseline revenue. Expansion ROI depends on capital costs.")

# ── Summary Table ─────────────────────────────────────────────────────────────
section_header("Scenario Summary")
summary_df = pd.DataFrame({
    "Metric":   ["Revenue", "Transactions", "Avg Order Value", "Profit", "Change (%)"],
    "Baseline": [
        f"${base_revenue:,.0f}", f"{base_transactions:,}", f"${base_avg_order:.2f}",
        f"${base_profit:,.0f}", "—",
    ],
    "Scenario": [
        f"${scenario_revenue:,.0f}", f"{scenario_transactions:,.0f}", f"${scenario_avg_order:.2f}",
        f"${scenario_profit:,.0f}",
        f"{'+'  if revenue_delta >= 0 else ''}{(revenue_delta / base_revenue * 100):.1f}%",
    ],
})
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
if revenue_delta > 0:
    insight_card(f"This scenario projects a ${revenue_delta:,.0f} revenue increase (+{revenue_delta/base_revenue*100:.1f}%). Ensure supply chain and staffing are scaled accordingly.", kind="success")
else:
    insight_card(f"This scenario projects a ${abs(revenue_delta):,.0f} revenue decline. Consider mitigating with targeted promotions or cost reduction.", kind="warning")
if profit_delta > 0:
    insight_card(f"Profit improves by ${profit_delta:,.0f} under this scenario — strong case for execution.", kind="success")
else:
    insight_card(f"Profit contracts by ${abs(profit_delta):,.0f} — review the cost structure before proceeding.", kind="warning")
if new_stores > 0:
    insight_card(f"Opening {new_stores} new store(s) adds ~${new_stores * revenue_per_store:,.0f} in projected revenue — validate with detailed site analysis.", kind="info")
insight_card("Run multiple scenarios (optimistic, base, pessimistic) to bracket your planning range before making capital commitments.", kind="info")
footer()

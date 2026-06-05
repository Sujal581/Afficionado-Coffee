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

if not (st.session_state.get("df") is not None):
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Calculations ──────────────────────────────────────────────────────────────
kpis = calculate_kpis(df)
base_revenue     = kpis["Revenue"]
base_transactions= kpis["Transactions"]
base_avg_order   = kpis["Avg_Order_Value"]
num_stores       = df["store_location"].nunique() if "store_location" in df.columns else 1
revenue_per_store= base_revenue / max(num_stores, 1)

scenario_revenue = (
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
kpi_card(col1, "Projected Revenue",  f"${scenario_revenue:,.0f}",
         icon="💰", color="green" if revenue_delta >= 0 else "red")
kpi_card(col2, "Revenue Change",
         f"{'+'  if revenue_delta >= 0 else ''}{revenue_delta:,.0f}",
         icon="📈" if revenue_delta >= 0 else "📉",
         color="green" if revenue_delta >= 0 else "red")
kpi_card(col3, "Projected Profit",   f"${scenario_profit:,.0f}",
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

# ── Sensitivity Analysis ───────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    section_header("Revenue Sensitivity — Demand")
    chart_label("Revenue vs Demand Change (%)", "How revenue responds across a range of demand shifts")
    demand_range = list(range(-50, 101, 10))
    rev_sensitivity = [
        base_revenue * (1 + d / 100) * (1 + price_change / 100)
        + new_stores * revenue_per_store * (1 + d / 100)
        for d in demand_range
    ]
    sens_df = pd.DataFrame({"Demand Change (%)": demand_range, "Revenue": rev_sensitivity})
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
    price_range = list(range(-30, 51, 5))
    price_sensitivity = [
        base_revenue * (1 + demand_change / 100) * (1 + p / 100)
        + new_stores * revenue_per_store
        for p in price_range
    ]
    price_df = pd.DataFrame({"Price Change (%)": price_range, "Revenue": price_sensitivity})
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
    chart_note("Price increases boost revenue only if demand doesn't drop proportionally — watch elasticity.")

# ── Store Expansion ────────────────────────────────────────────────────────────
section_header("Store Expansion Impact")
chart_label("Revenue by Number of New Store Openings", "Projected revenue for 0 to 5 new stores")

expansion_data = []
for n in range(0, 6):
    base_proj = base_revenue * (1 + demand_change / 100) * (1 + price_change / 100)
    incr = n * revenue_per_store * (1 + demand_change / 100)
    expansion_data.append({"New Stores": n, "Base Revenue": base_proj, "Expansion Revenue": incr})
exp_df = pd.DataFrame(expansion_data)

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Base Scenario Revenue", x=exp_df["New Stores"], y=exp_df["Base Revenue"],
    marker_color=COLORS["espresso"],
    hovertemplate="New Stores: %{x}<br>Base: $%{y:,.0f}<extra></extra>",
))
fig.add_trace(go.Bar(
    name="Expansion Revenue", x=exp_df["New Stores"], y=exp_df["Expansion Revenue"],
    marker_color=COLORS["caramel"],
    hovertemplate="New Stores: %{x}<br>Expansion: $%{y:,.0f}<extra></extra>",
))
fig.update_layout(barmode="stack")
fig.update_xaxes(title="Number of New Stores", tickmode="linear")
fig.update_yaxes(tickprefix="$", tickformat=",.0f")
apply_plot_layout(fig, height=320)
st.plotly_chart(fig, use_container_width=True)
chart_note(f"Opening {new_stores} new store(s) adds ≈ ${new_stores * revenue_per_store * (1 + demand_change/100):,.0f} in projected revenue.")

# ── Break-Even & Scenario Table ────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    section_header("Break-Even Analysis")
    chart_label("Profit vs Revenue Range", "Find the revenue level where costs are covered")
    rev_range = np.linspace(base_revenue * 0.5, base_revenue * 2, 60)
    profit_line = rev_range - scenario_cost

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rev_range, y=profit_line,
        mode="lines", name="Profit",
        line=dict(color=COLORS["caramel"], width=3),
        fill="tozeroy", fillcolor="rgba(200,150,62,0.07)",
        hovertemplate="Revenue: $%{x:,.0f}<br>Profit: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=COLORS["brown"], line_dash="dash",
                  annotation_text="Break-Even", annotation_font_color=COLORS["brown"])
    fig.add_vline(x=scenario_revenue, line_color=COLORS["gold"], line_dash="dot",
                  annotation_text="Projected", annotation_font_color=COLORS["gold"])
    fig.update_xaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(title="Profit ($)", tickprefix="$", tickformat=",.0f")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("Your projected revenue vertical vs the break-even line shows your profit/loss position.")

with col4:
    section_header("Three-Scenario Summary")
    chart_label("Conservative · Base · Optimistic", "Full planning range for risk-adjusted decisions")
    scenarios = pd.DataFrame({
        "Scenario":      ["Conservative", "Base Case", "Optimistic"],
        "Demand Change": [f"{demand_change-15:+.0f}%", f"{demand_change:+.0f}%", f"{demand_change+15:+.0f}%"],
        "Revenue": [
            f"${base_revenue * (1+(demand_change-15)/100) * (1+price_change/100):,.0f}",
            f"${scenario_revenue:,.0f}",
            f"${base_revenue * (1+(demand_change+15)/100) * (1+price_change/100) + new_stores*revenue_per_store:,.0f}",
        ],
        "Profit": [
            f"${base_revenue*(1+(demand_change-15)/100)*(1+price_change/100)-scenario_cost:,.0f}",
            f"${scenario_profit:,.0f}",
            f"${base_revenue*(1+(demand_change+15)/100)*(1+price_change/100)+new_stores*revenue_per_store-scenario_cost:,.0f}",
        ],
    })
    st.dataframe(scenarios, use_container_width=True, hide_index=True)
    chart_note("Use Conservative for financial commitments and Optimistic for growth ambition planning.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
delta_pct = (scenario_revenue - base_revenue) / base_revenue * 100
insight_card(
    f"Under your current scenario (demand {demand_change:+}%, price {price_change:+}%), projected revenue is ${scenario_revenue:,.0f} — a {delta_pct:+.1f}% change from baseline.",
    kind="success" if revenue_delta >= 0 else "warning",
)
insight_card(
    f"Projected profit: ${scenario_profit:,.0f}, a change of {'+' if profit_delta>=0 else ''}{profit_delta:,.0f} vs baseline. {'Margin is improving.' if profit_delta>=0 else 'Review cost controls before proceeding.'}",
    kind="info",
)
if new_stores > 0:
    insight_card(f"Opening {new_stores} new store(s) adds ≈ ${new_stores*revenue_per_store:,.0f} in annual revenue based on average per-store performance.", kind="success")
insight_card("Price increases above 15–20% risk demand elasticity effects — validate with a small-scale pilot before rolling out chain-wide.", kind="warning")
insight_card("Use the Conservative scenario as your floor for financial planning and inventory commitment.", kind="success")
insight_card("Re-run scenario analysis quarterly as market conditions, competitor pricing, and customer behaviour evolve.", kind="warning")
footer()

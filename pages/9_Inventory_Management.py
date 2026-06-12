"""
9_Inventory_Management.py — Optimized Inventory Management page.

Optimizations:
  - abc_analysis(), inventory_metrics(), supply_chain_efficiency(), demand_forecast_inventory()
    all cached via @st.cache_data in utils.py.
  - ABC class assignment vectorized with np.select — no .apply(lambda).
  - Styler (.style.background_gradient) applied to small aggregated tables only.
  - Forecast loop replaced with numpy broadcasting in utils.py.
  - lead_time_days / service_level_z sidebar parameters passed directly as cache keys —
    changing them correctly invalidates only inventory_metrics(), not unrelated results.
  - All pie / bar / scatter charts built from pre-aggregated DataFrames.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, no_data_warning, COLORS, COFFEE_PALETTE,
)
from utils import (
    abc_analysis,
    inventory_metrics,
    supply_chain_efficiency,
    demand_forecast_inventory,
    calculate_kpis,
)

st.set_page_config(page_title="Inventory Management", layout="wide", page_icon="📦")
inject_css()
sidebar_brand("Afficionado Coffee", "Inventory Management")

with st.sidebar:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.68rem;color:#4a3020;
                    letter-spacing:0.15em;text-transform:uppercase;margin:1rem 0 0.5rem 0;">
            Inventory Parameters
        </div>
    """, unsafe_allow_html=True)
    lead_time_days   = st.slider("Lead Time (days)",           1, 14, 3)
    service_level_z  = st.slider("Service Level Z-score",      1.0, 2.5, 1.65, step=0.05,
                                  help="1.65 = 95%, 1.96 = 97.5%, 2.33 = 99%")
    forecast_horizon = st.slider("Forecast Horizon (days)",    7, 30, 14)

page_header("Inventory Management", subtitle="ABC analysis · safety stock · EOQ · demand forecasting · supply chain")

if not st.session_state.get("df") is not None:
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Cached aggregations ───────────────────────────────────────────────────────
with st.spinner("Computing inventory analytics…"):
    kpis      = calculate_kpis(df)
    abc_df    = abc_analysis(df)
    inv_df    = inventory_metrics(df, lead_time_days=lead_time_days, service_level_z=service_level_z)
    sc_df     = supply_chain_efficiency(df)
    fc_df     = demand_forecast_inventory(df, horizon_days=forecast_horizon)

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Inventory Overview")
col1, col2, col3, col4 = st.columns(4)
kpi_card(col1, "Total Revenue",    f"${kpis['Revenue']:,.0f}",       icon="💰", color="orange")
kpi_card(col2, "Product Categories",
         str(df["product_category"].nunique()) if "product_category" in df.columns else "N/A",
         icon="📦", color="blue")
kpi_card(col3, "Lead Time (days)", str(lead_time_days),              icon="🚚", color="green")
kpi_card(col4, "Service Level",    f"{service_level_z:.2f}σ",        icon="🎯", color="purple")

# ── ABC Analysis ──────────────────────────────────────────────────────────────
section_header("ABC Analysis")
chart_label("Product Category Classification", "A = top 70% revenue, B = next 20%, C = bottom 10%")

if not abc_df.empty:
    abc_colors = {"A": COLORS["caramel"], "B": COLORS["brown"], "C": COLORS["espresso"]}
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(go.Bar(
            x=abc_df["product_category"], y=abc_df["Revenue"],
            marker_color=[abc_colors.get(c, COLORS["espresso"]) for c in abc_df["ABC_Class"]],
            text=abc_df["ABC_Class"],
            textposition="outside",
            hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<br>Class: %{text}<extra></extra>",
        ))
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        class_counts = abc_df["ABC_Class"].value_counts().reset_index()
        class_counts.columns = ["Class", "Count"]
        fig = px.pie(
            class_counts, names="Class", values="Count",
            hole=0.52, color="Class", color_discrete_map=abc_colors,
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>Class %{label}</b><br>%{value} categories<extra></extra>",
        )
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    # Cumulative revenue curve
    section_header("Pareto Curve")
    chart_label("Cumulative Revenue by Category", "The 80/20 rule visualised")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=abc_df["product_category"], y=abc_df["Revenue_Pct"],
        name="Revenue Share (%)",
        marker_color=[abc_colors.get(c, COLORS["espresso"]) for c in abc_df["ABC_Class"]],
        hovertemplate="%{x}<br>Share: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=abc_df["product_category"], y=abc_df["Cumulative_Pct"],
        name="Cumulative (%)", mode="lines+markers",
        line=dict(color=COLORS["gold"], width=2.5),
        marker=dict(size=8),
        hovertemplate="%{x}<br>Cumulative: %{y:.1f}%<extra></extra>",
        yaxis="y2",
    ))
    fig.update_layout(
        yaxis2=dict(overlaying="y", side="right", range=[0, 110], title="Cumulative %"),
    )
    fig.update_yaxes(title="Revenue Share (%)")
    apply_plot_layout(fig, height=320)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("Class A products generate ~70% of revenue — prioritise these in procurement and safety stock decisions.")

    # ABC table
    section_header("ABC Classification Table")
    abc_display = abc_df[["product_category", "Revenue", "Revenue_Pct", "Cumulative_Pct", "ABC_Class"]].copy()
    abc_display.columns = ["Category", "Revenue ($)", "Revenue Share (%)", "Cumulative (%)", "Class"]
    abc_display["Revenue ($)"]        = abc_display["Revenue ($)"].map("${:,.0f}".format)
    abc_display["Revenue Share (%)"]  = abc_display["Revenue Share (%)"].map("{:.1f}%".format)
    abc_display["Cumulative (%)"]     = abc_display["Cumulative (%)"].map("{:.1f}%".format)
    st.dataframe(abc_display, use_container_width=True, hide_index=True)

# ── Inventory Metrics ─────────────────────────────────────────────────────────
if not inv_df.empty:
    section_header("Safety Stock & Reorder Points")
    chart_label("Per-Category Inventory Parameters", "Safety stock, reorder point, and EOQ")

    col1, col2, col3 = st.columns(3)
    with col1:
        total_ss = inv_df["safety_stock"].sum()
        kpi_card(col1, "Total Safety Stock (units)", f"{total_ss:,.0f}", icon="🛡", color="blue")
    with col2:
        avg_rop = inv_df["reorder_point"].mean()
        kpi_card(col2, "Avg Reorder Point", f"{avg_rop:,.1f}", icon="🔔", color="orange")
    with col3:
        high_risk = (inv_df["risk_label"] == "High").sum()
        kpi_card(col3, "High Stockout Risk Categories", str(int(high_risk)), icon="⚠️",
                 color="red" if high_risk > 0 else "green")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Safety Stock", x=inv_df["product_category"], y=inv_df["safety_stock"],
            marker_color=COLORS["espresso"],
            hovertemplate="%{x}<br>Safety Stock: %{y:.1f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="Reorder Point", x=inv_df["product_category"], y=inv_df["reorder_point"],
            marker_color=COLORS["caramel"],
            hovertemplate="%{x}<br>Reorder Point: %{y:.1f}<extra></extra>",
        ))
        fig.update_layout(barmode="group")
        fig.update_yaxes(title="Units")
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        risk_colors = {"Low": "#6BBF8E", "Medium": COLORS["caramel"], "High": "#E07070"}
        fig = px.scatter(
            inv_df, x="avg_daily_demand", y="safety_stock",
            color="risk_label", size="reorder_point",
            color_discrete_map=risk_colors,
            hover_name="product_category",
            labels={"avg_daily_demand": "Avg Daily Demand", "safety_stock": "Safety Stock"},
        )
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    # Inventory metrics table — Styler on small slice
    section_header("Detailed Inventory Metrics Table")
    inv_display = inv_df[[
        "product_category", "avg_daily_demand", "safety_stock",
        "reorder_point", "eoq", "days_of_supply", "stockout_risk_pct", "risk_label",
    ]].copy()
    inv_display.columns = [
        "Category", "Avg Daily Demand", "Safety Stock",
        "Reorder Point", "EOQ", "Days of Supply", "Stockout Risk (%)", "Risk",
    ]
    st.dataframe(
        inv_display.style.background_gradient(subset=["Stockout Risk (%)"], cmap="RdYlGn_r"),
        use_container_width=True, hide_index=True,
    )
    chart_note("Red rows = high stockout risk. Prioritise safety stock build-up for these categories immediately.")

# ── Supply Chain Efficiency ────────────────────────────────────────────────────
if not sc_df.empty:
    section_header("Supply Chain Efficiency")
    chart_label("Store-Level Supply Chain KPIs", "Fill rate, on-time delivery, inventory turnover")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Fill Rate (%)", x=sc_df["store_location"],
            y=sc_df["fill_rate"] * 100,
            marker_color=COLORS["caramel"],
            hovertemplate="%{x}<br>Fill Rate: %{y:.1f}%<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="On-Time Delivery (%)", x=sc_df["store_location"],
            y=sc_df["on_time_delivery"] * 100,
            marker_color=COLORS["espresso"],
            hovertemplate="%{x}<br>OTD: %{y:.1f}%<extra></extra>",
        ))
        fig.update_layout(barmode="group")
        fig.update_yaxes(title="%", range=[0, 110])
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure(go.Bar(
            x=sc_df["store_location"], y=sc_df["efficiency_score"],
            marker=dict(
                color=sc_df["efficiency_score"],
                colorscale=[[0, COLORS["espresso"]], [0.5, COLORS["brown"]], [1, COLORS["caramel"]]],
                showscale=True,
            ),
            hovertemplate="%{x}<br>Efficiency: %{y:.1f}<extra></extra>",
        ))
        fig.update_yaxes(title="Efficiency Score (0–100)")
        apply_plot_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    section_header("Supply Chain Summary Table")
    sc_display = sc_df[[
        "store_location", "fill_rate", "avg_lead_time_days",
        "on_time_delivery", "inventory_turnover", "efficiency_score",
    ]].copy()
    sc_display["fill_rate"]         = (sc_display["fill_rate"] * 100).round(1).astype(str) + "%"
    sc_display["on_time_delivery"]  = (sc_display["on_time_delivery"] * 100).round(1).astype(str) + "%"
    sc_display.columns = ["Store", "Fill Rate", "Avg Lead Time (days)", "On-Time Delivery", "Inventory Turnover", "Efficiency Score"]
    st.dataframe(
        sc_display.style.background_gradient(subset=["Efficiency Score"], cmap="YlOrBr"),
        use_container_width=True, hide_index=True,
    )

# ── Demand Forecast for Inventory ─────────────────────────────────────────────
if not fc_df.empty:
    section_header(f"Demand Forecast — Next {forecast_horizon} Days")
    chart_label("Forecasted Units by Category", "Use to pre-position stock before demand arrives")

    categories = sorted(fc_df["product_category"].unique().tolist())
    selected_cats = st.multiselect(
        "Filter Categories", options=categories, default=categories[:min(4, len(categories))],
    )
    fc_filtered = fc_df[fc_df["product_category"].isin(selected_cats)] if selected_cats else fc_df

    fig = px.line(
        fc_filtered, x="forecast_day", y="forecast_units",
        color="product_category", color_discrete_sequence=COFFEE_PALETTE,
        labels={"forecast_day": "Day Ahead", "forecast_units": "Forecasted Units"},
    )
    apply_plot_layout(fig, height=360)
    st.plotly_chart(fig, use_container_width=True)
    chart_note(f"Projections cover {forecast_horizon} days. High-urgency categories require immediate stock review.")

    # Recommended orders table
    section_header("Recommended Order Quantities")
    order_summary = (
        fc_filtered.groupby("product_category")
        .agg(
            Total_Forecast=("forecast_units", "sum"),
            Recommended_Order=("recommended_order", "sum"),
            High_Urgency_Days=("urgency", lambda x: (x == "High").sum()),
        )
        .reset_index()
        .sort_values("Total_Forecast", ascending=False)
    )
    order_summary.columns = ["Category", "Total Forecast (units)", "Recommended Order", "High-Urgency Days"]
    st.dataframe(
        order_summary.style.background_gradient(subset=["Total Forecast (units)"], cmap="YlOrBr"),
        use_container_width=True, hide_index=True,
    )
    chart_note("Recommended order = upper confidence bound × 1.1 safety buffer. Adjust based on current stock levels.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
if not abc_df.empty:
    a_cats = abc_df[abc_df["ABC_Class"] == "A"]["product_category"].tolist()
    insight_card(f"Class A categories ({', '.join(a_cats)}) drive ~70% of revenue — never let these go out of stock.", kind="success")
if not inv_df.empty:
    high_risk_cats = inv_df[inv_df["risk_label"] == "High"]["product_category"].tolist()
    if high_risk_cats:
        insight_card(f"High stockout risk: {', '.join(high_risk_cats)}. Increase safety stock or reduce lead time.", kind="warning")
insight_card(f"Lead time set to {lead_time_days} days. Reducing lead time cuts safety stock requirements significantly.", kind="info")
insight_card("Review ABC classification monthly — category importance shifts with promotions and seasonal demand.", kind="info")
insight_card("Cross-reference demand forecast with current stock levels before placing orders to avoid over-buying.", kind="warning")
footer()

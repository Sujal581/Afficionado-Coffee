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
    abc_analysis, inventory_metrics, supply_chain_efficiency,
    demand_forecast_inventory, calculate_kpis,
)

st.set_page_config(page_title="Inventory Management", layout="wide", page_icon="📦")
inject_css()
sidebar_brand("Afficionado Coffee", "Inventory & Supply Chain")
page_header("Inventory Management & Supply Chain",
            subtitle="ABC analysis · reorder points · safety stock · supply chain efficiency")

if not (st.session_state.get("df") is not None):
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Sidebar Parameters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.68rem;color:#4a3020;
                    letter-spacing:0.15em;text-transform:uppercase;margin:1rem 0 0.5rem 0;">
            Inventory Parameters
        </div>
    """, unsafe_allow_html=True)
    lead_time = st.slider("Supplier Lead Time (days)", 1, 14, 3)
    service_z = st.select_slider(
        "Service Level",
        options=[1.28, 1.65, 1.96, 2.33],
        value=1.65,
        format_func=lambda x: {1.28: "90%", 1.65: "95%", 1.96: "97.5%", 2.33: "99%"}[x],
    )
    horizon_inv = st.slider("Demand Forecast Horizon (days)", 7, 30, 14)
    st.markdown("""
        <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(200,150,62,0.2),transparent);
                    margin:1rem 0;"></div>
    """, unsafe_allow_html=True)

# ── Compute ───────────────────────────────────────────────────────────────────
abc_df     = abc_analysis(df)
inv_df     = inventory_metrics(df, lead_time_days=lead_time, service_level_z=service_z)
sc_df      = supply_chain_efficiency(df)
fc_inv_df  = demand_forecast_inventory(df, horizon_days=horizon_inv)
kpis       = calculate_kpis(df)

# ── Summary KPIs ──────────────────────────────────────────────────────────────
section_header("Inventory Overview")

n_categories = len(abc_df) if not abc_df.empty else 0
n_class_a    = int((abc_df["ABC_Class"] == "A").sum()) if not abc_df.empty else 0
high_risk    = int((inv_df["risk_label"] == "High").sum()) if not inv_df.empty else 0
avg_score    = round(sc_df["efficiency_score"].mean(), 1) if not sc_df.empty else 0

c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Product Categories",   str(n_categories),           icon="📦", color="orange")
kpi_card(c2, "Class-A SKUs",         str(n_class_a),              icon="⭐", color="gold")
kpi_card(c3, "High Stockout Risk",   str(high_risk),              icon="⚠️", color="red")
kpi_card(c4, "Avg Supply Chain Score", f"{avg_score}/100",        icon="🏭", color="green")

# ── ABC ANALYSIS ──────────────────────────────────────────────────────────────
section_header("ABC Inventory Analysis")
chart_label("Revenue-Based ABC Classification",
            "A = top 70% revenue · B = next 20% · C = remaining 10%")

if not abc_df.empty:
    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        abc_colors = {"A": COLORS["caramel"], "B": COLORS["brown"], "C": COLORS["espresso"]}
        fig = px.bar(
            abc_df.head(15), x="product_category", y="Revenue",
            color="ABC_Class", color_discrete_map=abc_colors,
            text="ABC_Class",
        )
        fig.update_traces(textposition="outside")
        fig.update_xaxes(title="Product Category", tickangle=30)
        fig.update_yaxes(tickprefix="$", tickformat=",.0f", title="Revenue")
        apply_plot_layout(fig, height=340)
        st.plotly_chart(fig, use_container_width=True)

    with col_a2:
        class_counts = abc_df["ABC_Class"].value_counts().reset_index()
        class_counts.columns = ["Class", "Count"]
        fig = px.pie(
            class_counts, names="Class", values="Count",
            hole=0.55,
            color="Class", color_discrete_map=abc_colors,
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>Class %{label}</b><br>%{value} categories<extra></extra>",
        )
        apply_plot_layout(fig, height=340)
        st.plotly_chart(fig, use_container_width=True)

    chart_note("Class A: tight control, frequent reorders. Class B: moderate review. Class C: bulk ordering, minimal oversight.")

    abc_show = abc_df[["product_category", "Revenue", "Revenue_Pct", "Cumulative_Pct", "ABC_Class"]].copy()
    abc_show["Revenue"]        = abc_show["Revenue"].apply(lambda x: f"${x:,.0f}")
    abc_show["Revenue_Pct"]    = abc_show["Revenue_Pct"].apply(lambda x: f"{x:.1f}%")
    abc_show["Cumulative_Pct"] = abc_show["Cumulative_Pct"].apply(lambda x: f"{x:.1f}%")
    abc_show.columns = ["Category", "Revenue", "Revenue %", "Cumulative %", "Class"]
    st.dataframe(abc_show, use_container_width=True, hide_index=True)

# ── REORDER POINTS & SAFETY STOCK ─────────────────────────────────────────────
section_header("Reorder Points & Safety Stock")
chart_label("Safety Stock and Reorder Point by Category",
            f"Lead time = {lead_time} days · Service level = {int({1.28:90,1.65:95,1.96:97.5,2.33:99}[service_z])}%")

if not inv_df.empty:
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Safety Stock",
            x=inv_df["product_category"], y=inv_df["safety_stock"],
            marker_color=COLORS["espresso"],
            hovertemplate="%{x}<br>Safety Stock: %{y:.1f} units<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="Reorder Point",
            x=inv_df["product_category"], y=inv_df["reorder_point"],
            marker_color=COLORS["caramel"],
            hovertemplate="%{x}<br>Reorder Point: %{y:.1f} units<extra></extra>",
        ))
        fig.update_layout(barmode="group")
        fig.update_xaxes(tickangle=30, title="Category")
        fig.update_yaxes(title="Units")
        apply_plot_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)
        chart_note("Trigger a reorder when on-hand stock drops to or below the Reorder Point.")

    with col_r2:
        fig = go.Figure(go.Bar(
            x=inv_df["product_category"], y=inv_df["days_of_supply"],
            marker=dict(
                color=inv_df["days_of_supply"],
                colorscale=[[0, "#E07070"], [0.4, COLORS["espresso"]], [1, COLORS["caramel"]]],
                showscale=True,
                colorbar=dict(title="Days"),
            ),
            text=inv_df["days_of_supply"].apply(lambda x: f"{x:.0f}d"),
            textposition="outside",
            hovertemplate="%{x}<br>Days of Supply: %{y:.1f}<extra></extra>",
        ))
        fig.update_xaxes(tickangle=30, title="Category")
        fig.update_yaxes(title="Days of Supply")
        apply_plot_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)
        chart_note("Red bars = critically low days of supply. Prioritise reorders for these categories.")

    section_header("Inventory Metrics Table")
    chart_label("Full Inventory Parameters", "All categories with safety stock, reorder, EOQ and risk rating")
    inv_show = inv_df[[
        "product_category", "avg_daily_demand", "std_daily_demand",
        "safety_stock", "reorder_point", "eoq",
        "days_of_supply", "stockout_risk_pct", "risk_label",
    ]].copy()
    inv_show.columns = [
        "Category", "Avg Daily Demand", "Demand Std Dev",
        "Safety Stock", "Reorder Point", "EOQ",
        "Days of Supply", "Stockout Risk %", "Risk",
    ]
    for col in ["Avg Daily Demand", "Demand Std Dev", "Safety Stock", "Reorder Point", "EOQ"]:
        inv_show[col] = inv_show[col].apply(lambda x: round(x, 1))
    st.dataframe(
        inv_show.style.applymap(
            lambda v: "background-color: rgba(224,112,112,0.15);" if v == "High"
            else ("background-color: rgba(200,150,62,0.10);" if v == "Medium" else ""),
            subset=["Risk"],
        ),
        use_container_width=True,
        hide_index=True,
    )
    chart_note("EOQ = Economic Order Quantity. Stockout Risk % = coefficient of variation of daily demand.")

# ── SUPPLY CHAIN EFFICIENCY ────────────────────────────────────────────────────
section_header("Supply Chain Efficiency")
chart_label("Store-Level Supply Chain Scorecard",
            "Fill rate · on-time delivery · inventory turnover · overall efficiency")

if not sc_df.empty:
    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        fig = go.Figure(go.Bar(
            x=sc_df["store_location"], y=sc_df["efficiency_score"],
            marker=dict(
                color=sc_df["efficiency_score"],
                colorscale=[[0, COLORS["espresso"]], [0.5, COLORS["brown"]], [1, COLORS["caramel"]]],
                showscale=True,
                colorbar=dict(title="Score"),
            ),
            text=sc_df["efficiency_score"].apply(lambda x: f"{x:.1f}"),
            textposition="outside",
            hovertemplate="%{x}<br>Efficiency Score: %{y:.1f}<extra></extra>",
        ))
        fig.update_xaxes(title="Store", tickangle=15)
        fig.update_yaxes(title="Efficiency Score (0–100)", range=[0, 110])
        apply_plot_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)
        chart_note("Score = 40% fill rate + 40% on-time delivery + 20% demand stability.")

    with col_sc2:
        col_metrics = ["fill_rate", "on_time_delivery", "inventory_turnover"]
        melted_sc = sc_df.melt(id_vars="store_location", value_vars=col_metrics,
                               var_name="Metric", value_name="Value")
        label_map = {
            "fill_rate":         "Fill Rate",
            "on_time_delivery":  "On-Time Delivery",
            "inventory_turnover":"Inventory Turnover",
        }
        melted_sc["Metric"] = melted_sc["Metric"].map(label_map)
        fig = px.bar(
            melted_sc, x="store_location", y="Value", color="Metric",
            barmode="group",
            color_discrete_sequence=[COLORS["caramel"], COLORS["brown"], COLORS["gold"]],
        )
        fig.update_xaxes(title="Store", tickangle=15)
        fig.update_yaxes(title="Value")
        apply_plot_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)
        chart_note("Fill rate and on-time delivery should both be > 95% for excellent supply chain health.")

    section_header("Supply Chain Scorecard Table")
    sc_show = sc_df[[
        "store_location", "avg_daily_units", "fill_rate",
        "avg_lead_time_days", "on_time_delivery",
        "inventory_turnover", "efficiency_score",
    ]].copy()
    sc_show["fill_rate"]         = (sc_show["fill_rate"] * 100).apply(lambda x: f"{x:.1f}%")
    sc_show["on_time_delivery"]  = (sc_show["on_time_delivery"] * 100).apply(lambda x: f"{x:.1f}%")
    sc_show["avg_daily_units"]   = sc_show["avg_daily_units"].apply(lambda x: round(x, 1))
    sc_show["inventory_turnover"]= sc_show["inventory_turnover"].apply(lambda x: round(x, 1))
    sc_show["efficiency_score"]  = sc_show["efficiency_score"].apply(lambda x: round(x, 1))
    sc_show.columns = [
        "Store", "Avg Daily Units", "Fill Rate",
        "Lead Time (days)", "On-Time Delivery",
        "Inventory Turnover", "Efficiency Score",
    ]
    st.dataframe(sc_show, use_container_width=True, hide_index=True)

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Inventory Insights & Recommendations")

if not abc_df.empty:
    a_cats = abc_df[abc_df["ABC_Class"] == "A"]["product_category"].tolist()
    insight_card(
        f"Class A categories ({', '.join(a_cats[:3])}{'…' if len(a_cats) > 3 else ''}) "
        f"drive 70%+ of revenue — implement continuous review policies and tighter reorder controls.",
        kind="success",
    )

if not inv_df.empty and high_risk > 0:
    risky = inv_df[inv_df["risk_label"] == "High"]["product_category"].tolist()
    insight_card(
        f"High stockout risk detected in: {', '.join(risky[:4])}. "
        f"Increase safety stock or negotiate shorter lead times with suppliers.",
        kind="error" if high_risk >= 3 else "warning",
    )

insight_card(
    f"With a {lead_time}-day lead time, ensure reorders are placed when stock falls to the Reorder Point "
    f"to avoid stockouts under 95%+ service level.",
    kind="info",
)

if not sc_df.empty:
    low_eff = sc_df[sc_df["efficiency_score"] < 80]["store_location"].tolist()
    if low_eff:
        insight_card(
            f"Stores with efficiency below 80: {', '.join(low_eff)}. "
            f"Audit supplier performance and reorder cycles for these locations.",
            kind="warning",
        )
    else:
        insight_card("All stores are operating above the 80-point efficiency threshold.", kind="success")

insight_card(
    "Use the demand forecast chart to pre-position stock before projected demand surges, "
    "reducing last-minute reorders and premium freight costs.",
    kind="success",
)
insight_card(
    "Implement automated reorder alerts in your POS system using the Reorder Point values from this dashboard.",
    kind="info",
)
footer()

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
from utils import workforce_planning, calculate_kpis

st.set_page_config(page_title="Workforce Planning", layout="wide", page_icon="👥")
inject_css()
sidebar_brand("Afficionado Coffee", "Workforce Planning")

with st.sidebar:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.68rem;color:#4a3020;
                    letter-spacing:0.15em;text-transform:uppercase;margin:1rem 0 0.5rem 0;">
            Staffing Parameters
        </div>
    """, unsafe_allow_html=True)
    txn_per_staff = st.number_input(
        "Transactions per Staff Member",
        min_value=1, value=30, step=1,
        help="How many transactions one staff member can handle per hour",
    )

page_header("Workforce Planning Dashboard", subtitle="Data-driven staffing recommendations by store, hour, and day")

if not (st.session_state.get("df") is not None):
    no_data_warning()
    footer()
    st.stop()

df = st.session_state["df"]

# ── Compute ───────────────────────────────────────────────────────────────────
kpis = calculate_kpis(df)
staff_df = workforce_planning(df)
staff_df["Required Staff"] = np.ceil(staff_df["Transactions"] / txn_per_staff).astype(int)

total_staff_hours = int(staff_df["Required Staff"].sum())
peak_staff        = int(staff_df["Required Staff"].max())
avg_staff         = round(staff_df["Required Staff"].mean(), 1)
peak_row          = staff_df.loc[staff_df["Required Staff"].idxmax()]

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Staffing Overview")
col1, col2, col3, col4 = st.columns(4)
kpi_card(col1, "Total Staff-Hours Required", f"{total_staff_hours:,}",     icon="⏱",  color="blue")
kpi_card(col2, "Peak Staff Count",           f"{peak_staff}",              icon="🔝",  color="red")
kpi_card(col3, "Avg Staff per Time Slot",    f"{avg_staff}",               icon="📈",  color="green")
kpi_card(col4, "Peak Location",              peak_row["store_location"],   icon="📍",  color="purple")

# ── Staffing Heatmap ──────────────────────────────────────────────────────────
section_header("Staffing Heatmap — Store × Hour")
chart_label("Required Staff per Store per Hour", "Darker = more staff needed")

pivot = staff_df.pivot_table(
    index="store_location", columns="hour",
    values="Required Staff", aggfunc="sum",
).fillna(0)

fig = px.imshow(
    pivot,
    color_continuous_scale=[[0, "#1a0f07"], [0.3, "#6F4E37"], [0.7, "#C8963E"], [1, "#F5E6D3"]],
    labels={"x": "Hour of Day", "y": "Store", "color": "Staff Required"},
    aspect="auto", text_auto=True,
)
apply_plot_layout(fig, height=260)
st.plotly_chart(fig, use_container_width=True)
chart_note("Use this heatmap to build weekly shift schedules — each cell shows minimum headcount for that store–hour slot.")

# ── Charts ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    section_header("Staff Requirement by Hour")
    chart_label("Total Staff Needed Across All Stores", "Aggregate staffing demand by hour of day")
    hourly_staff = staff_df.groupby("hour")["Required Staff"].sum().reset_index()
    peak_hr = int(hourly_staff.loc[hourly_staff["Required Staff"].idxmax(), "hour"])
    bar_colors = [COLORS["caramel"] if h == peak_hr else COLORS["espresso"] for h in hourly_staff["hour"]]
    fig = go.Figure(go.Bar(
        x=hourly_staff["hour"], y=hourly_staff["Required Staff"],
        marker_color=bar_colors,
        hovertemplate="Hour %{x}:00<br>Staff Required: %{y}<extra></extra>",
    ))
    fig.update_xaxes(tickmode="linear", title="Hour of Day")
    fig.update_yaxes(title="Staff Required")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note(f"Peak staffing at {peak_hr}:00 — plan shift handovers 15 minutes before this window.")

with col2:
    section_header("Staff Requirements by Store")
    chart_label("Peak Staff Needed per Location", "Which stores require the most staff at peak")
    store_staff = staff_df.groupby("store_location")["Required Staff"].max().reset_index()
    busiest_store = store_staff.loc[store_staff["Required Staff"].idxmax(), "store_location"]
    bar_colors_s = [COLORS["caramel"] if s == busiest_store else COLORS["espresso"] for s in store_staff["store_location"]]
    fig = go.Figure(go.Bar(
        x=store_staff["store_location"], y=store_staff["Required Staff"],
        marker_color=bar_colors_s,
        text=store_staff["Required Staff"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Peak Staff: %{y}<extra></extra>",
    ))
    fig.update_yaxes(title="Staff Required")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note(f"Busiest store: {busiest_store}. Allocate experienced staff leads and ensure backup coverage.")

# ── Weekly Staffing ────────────────────────────────────────────────────────────
section_header("Weekly Staffing Pattern")
chart_label("Required Staff by Day of Week", "Plan your weekly roster from this demand pattern")

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekly_staff = df.groupby("weekday")["transaction_qty"].sum().reset_index()
weekly_staff["Required Staff"] = np.ceil(weekly_staff["transaction_qty"] / txn_per_staff).astype(int)
weekly_staff["weekday"] = pd.Categorical(weekly_staff["weekday"], categories=weekday_order, ordered=True)
weekly_staff = weekly_staff.sort_values("weekday")
avg_line = weekly_staff["Required Staff"].mean()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly_staff["weekday"], y=weekly_staff["Required Staff"],
    mode="lines+markers",
    line=dict(color=COLORS["caramel"], width=3),
    marker=dict(size=10, color=COLORS["caramel"]),
    fill="tozeroy", fillcolor="rgba(200,150,62,0.08)",
    hovertemplate="<b>%{x}</b><br>Staff: %{y}<extra></extra>",
))
fig.add_hline(y=avg_line, line_dash="dash", line_color=COLORS["brown"],
              annotation_text=f"Average: {avg_line:.0f}", annotation_font_color=COLORS["brown"])
apply_plot_layout(fig, height=300)
st.plotly_chart(fig, use_container_width=True)
chart_note("Days above the dashed average need extra coverage. Days below are candidates for reduced shifts or cross-deployment.")

# ── Shift Classification & Store Comparison ────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    section_header("Shift Schedule Recommendation")
    chart_label("Suggested Shift Blocks", "Based on demand clustering across all hours")
    hourly_s = staff_df.groupby("hour")["Required Staff"].sum().reset_index()
    max_s = hourly_s["Required Staff"].max()
    bins = [0, max_s * 0.33, max_s * 0.67, max_s + 1]
    labels = ["Skeleton Crew", "Standard Shift", "Peak Shift"]
    hourly_s["Shift"] = pd.cut(hourly_s["Required Staff"], bins=bins, labels=labels)
    shift_color = {
        "Skeleton Crew": COLORS["espresso"],
        "Standard Shift": COLORS["brown"],
        "Peak Shift": COLORS["caramel"],
    }
    fig = px.bar(
        hourly_s, x="hour", y="Required Staff",
        color="Shift", color_discrete_map=shift_color,
        labels={"hour": "Hour","required_staff": "Required Staff"}
    )
    fig.update_traces(hovertemplate="Hour %{x}:00<br>Shift: %{color}<extra></extra>" "<b>Shift:</b> %{customdata[0]}<br>" "<b>Required Staff:</b> %{y}<extra></extra>")
    fig.update_xaxes(tickmode="linear", title="Hour of Day")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("Gold = Peak Shift (full team). Brown = Standard Shift. Dark = Skeleton Crew sufficient.")

with col4:
    section_header("Store Staffing Comparison")
    chart_label("Average vs Peak Staff per Store", "Gap shows staffing variability — plan flex coverage")
    store_comp = staff_df.groupby("store_location")["Required Staff"].agg(["mean", "max"]).reset_index()
    store_comp.columns = ["Store", "Avg Staff", "Peak Staff"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Avg Staff", x=store_comp["Store"], y=store_comp["Avg Staff"],
        marker_color=COLORS["espresso"],
    ))
    fig.add_trace(go.Bar(
        name="Peak Staff", x=store_comp["Store"], y=store_comp["Peak Staff"],
        marker_color=COLORS["caramel"],
    ))
    fig.update_layout(barmode="group")
    apply_plot_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    chart_note("A large gap between avg and peak = high variability — you need flexible/on-call staff for those locations.")

# ── Detailed Table ─────────────────────────────────────────────────────────────
section_header("Detailed Staffing Schedule")
chart_label("Top 20 Busiest Store–Hour Combinations", "Highest risk understaffing windows")

top_slots = (
    staff_df.sort_values("Required Staff", ascending=False)
    .head(20)[["store_location", "hour", "Transactions", "Required Staff"]]
    .copy()
)
top_slots.columns = ["Store", "Hour", "Transactions", "Staff Required"]
top_slots["Hour"] = top_slots["Hour"].astype(str) + ":00"
st.dataframe(
    top_slots.style.background_gradient(subset=["Staff Required"], cmap="YlOrBr"),
    use_container_width=True, hide_index=True,
)
chart_note("Schedule these 20 slots first — they represent your highest-risk understaffing windows.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Insights & Recommendations")
insight_card(f"Peak staffing of {peak_staff} employees required at {peak_row['store_location']} during hour {int(peak_row['hour'])}:00.", kind="success")
insight_card(f"{busiest_store} consistently requires the most staff — prioritise experienced leads and ensure backup coverage.", kind="info")
insight_card(f"Hour {peak_hr}:00 is the network-wide peak — ensure all stores are fully staffed 30 minutes before this window.", kind="info")
insight_card(f"Based on {txn_per_staff} transactions per staff member, total weekly labour demand is {total_staff_hours:,} staff-hours.", kind="success")
insight_card("Cross-train staff across stores to allow flexible redeployment during unexpected demand spikes.", kind="warning")
insight_card("Re-run staffing analysis weekly as transaction patterns evolve with seasons and promotions.", kind="warning")
footer()

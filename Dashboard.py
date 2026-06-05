import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from style import (
    inject_css, sidebar_brand, page_header, section_header,
    kpi_card, chart_label, chart_note, insight_card,
    apply_plot_layout, footer, COLORS, COFFEE_PALETTE,
)
from utils import get_processed_data, calculate_kpis, workforce_planning

st.set_page_config(
    page_title="Afficionado Coffee Analytics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_brand("Afficionado Coffee", "Business Intelligence")

with st.sidebar:
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.7rem;
                    color:#4a3020;letter-spacing:0.12em;text-transform:uppercase;
                    margin-bottom:0.5rem;">Navigation</div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                    line-height:1.8;padding:0.5rem 0;">
            📊 &nbsp;Main Dashboard<br>
            📈 &nbsp;Executive Overview<br>
            🔮 &nbsp;Sales Forecast<br>
            ⚡ &nbsp;Peak Demand<br>
            🤖 &nbsp;Model Comparison<br>
            🔍 &nbsp;Demand Patterns<br>
            👥 &nbsp;Workforce Planning<br>
            🎯 &nbsp;Scenario Analysis
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="height:1px;background:linear-gradient(90deg,transparent,
                    rgba(200,150,62,0.2),transparent);margin:1rem 0;"></div>
    """, unsafe_allow_html=True)

    if "df" in st.session_state and st.session_state["df"] is not None:
        df_info = st.session_state["df"]
        st.markdown(f"""
            <div style="background:rgba(200,150,62,0.08);border:1px solid rgba(200,150,62,0.18);
                        border-radius:8px;padding:0.75rem;font-family:'Lato',sans-serif;">
                <div style="font-size:0.6rem;color:#6b5040;letter-spacing:0.15em;
                            text-transform:uppercase;margin-bottom:0.4rem;">Dataset Loaded</div>
                <div style="font-size:0.8rem;color:#C8963E;font-weight:700;">
                    ✓ &nbsp;{len(df_info):,} records
                </div>
                <div style="font-size:0.72rem;color:#8a7060;margin-top:0.2rem;">
                    {len(df_info.columns)} columns
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Clear Dataset", use_container_width=True):
            del st.session_state["df"]
            st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.25rem;">
        <div style="font-size:2.4rem;">☕</div>
        <div>
            <div style="font-family:'Playfair Display',serif;font-size:2rem;
                        font-weight:800;color:#f0e6d3;line-height:1.1;">
                Afficionado Coffee Analytics
            </div>
            <div style="font-family:'Lato',sans-serif;font-size:0.78rem;
                        color:#6b5040;letter-spacing:0.2em;text-transform:uppercase;
                        margin-top:3px;">
                Revenue · Operations · Customer Intelligence
            </div>
        </div>
    </div>
    <div style="height:1px;background:linear-gradient(90deg,rgba(200,150,62,0.4),
                rgba(200,150,62,0.05),transparent);margin:1rem 0 1.5rem 0;"></div>
""", unsafe_allow_html=True)

# ── Upload Section ────────────────────────────────────────────────────────────
if "df" not in st.session_state or st.session_state["df"] is None:
    st.markdown("""
        <div style="text-align:center;padding:0.5rem 0 1rem 0;">
            <div style="font-family:'Playfair Display',serif;font-size:1.3rem;
                        color:#d4b896;margin-bottom:0.4rem;">
                Begin Your Analysis
            </div>
            <div style="font-family:'Lato',sans-serif;font-size:0.88rem;color:#6b5040;
                        line-height:1.6;max-width:480px;margin:0 auto;">
                Upload your coffee shop transaction CSV once — your dataset will persist
                across all dashboard pages throughout your session.
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_up1, col_up2, col_up3 = st.columns([1, 3, 1])
    with col_up2:
        uploaded = st.file_uploader(
            "Drop your Coffee Shop CSV here",
            type=["csv"],
            help="Upload a CSV with columns: transaction_time, transaction_qty, unit_price, store_location, product_category, product_type, transaction_id",
        )

    if uploaded:
        with st.spinner("☕ Brewing your analytics..."):
            file_bytes = uploaded.read()
            df = get_processed_data(file_bytes, uploaded.name)
            st.session_state["df"] = df
        st.success(f"✓ Dataset loaded — {len(df):,} records ready for analysis.")
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
            <div style="background:rgba(20,12,6,0.7);border:1px solid rgba(200,150,62,0.12);
                        border-radius:12px;padding:1.5rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.6rem;">📊</div>
                <div style="font-family:'Playfair Display',serif;font-size:0.95rem;
                            color:#d4b896;margin-bottom:0.4rem;">Executive KPIs</div>
                <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                            line-height:1.5;">Revenue, transactions, and store performance at a glance</div>
            </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
            <div style="background:rgba(20,12,6,0.7);border:1px solid rgba(200,150,62,0.12);
                        border-radius:12px;padding:1.5rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.6rem;">🔮</div>
                <div style="font-family:'Playfair Display',serif;font-size:0.95rem;
                            color:#d4b896;margin-bottom:0.4rem;">AI Forecasting</div>
                <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                            line-height:1.5;">ML-powered demand prediction and revenue forecasting</div>
            </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown("""
            <div style="background:rgba(20,12,6,0.7);border:1px solid rgba(200,150,62,0.12);
                        border-radius:12px;padding:1.5rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.6rem;">👥</div>
                <div style="font-family:'Playfair Display',serif;font-size:0.95rem;
                            color:#d4b896;margin-bottom:0.4rem;">Workforce Planning</div>
                <div style="font-family:'Lato',sans-serif;font-size:0.78rem;color:#6b5040;
                            line-height:1.5;">Staffing recommendations driven by real transaction data</div>
            </div>
        """, unsafe_allow_html=True)

    footer()
    st.stop()

# ── Dashboard (data is loaded) ────────────────────────────────────────────────
df = st.session_state["df"]

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Executive Summary")

kpis = calculate_kpis(df)
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Total Revenue",    f"${kpis['Revenue']:,.0f}",            icon="💰", color="orange")
kpi_card(c2, "Transactions",     f"{kpis['Transactions']:,}",           icon="🧾", color="blue")
kpi_card(c3, "Avg Order Value",  f"${kpis['Avg_Order_Value']:.2f}",     icon="📈", color="green")
kpi_card(c4, "Units Sold",       f"{kpis['Quantity']:,}",               icon="📦", color="purple")

st.markdown("<br>", unsafe_allow_html=True)
c5, c6, c7, c8 = st.columns(4)
num_stores = df["store_location"].nunique() if "store_location" in df.columns else 0
num_products = df["product_category"].nunique() if "product_category" in df.columns else 0
date_range = ""
if "date" in df.columns:
    dates = pd.to_datetime(df["date"])
    date_range = f"{dates.min().strftime('%b %d')} – {dates.max().strftime('%b %d, %Y')}"
peak_hour = int(df.groupby("hour")["transaction_qty"].sum().idxmax()) if "hour" in df.columns else 0

kpi_card(c5, "Store Locations",  str(num_stores),              icon="🏪", color="gold")
kpi_card(c6, "Product Categories", str(num_products),          icon="☕", color="rust")
kpi_card(c7, "Data Period",      date_range or "N/A",          icon="📅", color="teal")
kpi_card(c8, "Peak Hour",        f"{peak_hour}:00",            icon="⏰", color="red")

st.markdown("<br>", unsafe_allow_html=True)

# ── Revenue Trend ─────────────────────────────────────────────────────────────
section_header("Revenue Trend")
chart_label("Daily Revenue","Total revenue generated each calendar day")

daily = (df.groupby("date")["revenue"].sum().reset_index())
daily["date"] = pd.to_datetime(daily["date"])

fig = go.Figure()
fig.add_trace(
    go.Bar(x=daily["date"], y=daily["revenue"], marker_color=COLORS["caramel"],
        marker_line_color=COLORS["gold"], marker_line_width=1.5, hovertemplate=
        "<b>%{x|%b %d, %Y}</b><br>" "Revenue: $%{y:,.0f}<extra></extra>"
    )
)

fig.update_xaxes(tickformat="%b %d",tickangle=30,title="")
fig.update_yaxes(tickprefix="$",tickformat=",.0f",title="")
apply_plot_layout(fig, height=320)
st.plotly_chart(fig,use_container_width=True)
chart_note(f"Total revenue: ${kpis['Revenue']:,.0f} across {len(daily)} days of data.")

# ── Two-column charts ──────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    section_header("Peak Demand Hours")
    chart_label("Transactions by Hour", "When customers visit most often")
    if "hour" in df.columns:
        hourly = df.groupby("hour")["transaction_qty"].sum().reset_index()
        peak_h = hourly.loc[hourly["transaction_qty"].idxmax(), "hour"]
        colors_h = [COLORS["caramel"] if h == peak_h else COLORS["espresso"] for h in hourly["hour"]]
        fig = go.Figure(go.Bar(
            x=hourly["hour"], y=hourly["transaction_qty"],
            marker_color=colors_h,
            hovertemplate="Hour %{x}:00<br>Qty: %{y:,}<extra></extra>",
        ))
        fig.update_xaxes(tickmode="linear", title="Hour of Day")
        fig.update_yaxes(title="Units Sold", tickformat=",")
        apply_plot_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)
        chart_note(f"Peak hour is {int(peak_h)}:00 — schedule maximum staff 30 minutes before.")

with col_right:
    section_header("Store Performance")
    chart_label("Revenue by Store Location", "Ranked by total revenue contribution")
    if "store_location" in df.columns:
        store_sales = (
            df.groupby("store_location")["revenue"].sum()
            .reset_index().sort_values("revenue", ascending=True)
        )
        fig = go.Figure(go.Bar(
            x=store_sales["revenue"], y=store_sales["store_location"],
            orientation="h",
            marker=dict(
                color=store_sales["revenue"],
                colorscale=[[0, COLORS["espresso"]], [0.5, COLORS["brown"]], [1, COLORS["caramel"]]],
                showscale=False,
            ),
            hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>",
        ))
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        apply_plot_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)
        chart_note(f"Top store: {store_sales.iloc[-1]['store_location']} — ${store_sales.iloc[-1]['revenue']:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Product Performance ────────────────────────────────────────────────────────
col_p1, col_p2 = st.columns(2)

with col_p1:
    section_header("Top Product Categories")
    chart_label("Revenue by Category", "Best performing product categories")
    if "product_category" in df.columns:
        products = (
            df.groupby("product_category")["revenue"].sum()
            .reset_index().sort_values("revenue", ascending=False).head(8)
        )
        fig = px.pie(
            products, names="product_category", values="revenue",
            hole=0.52,
            color_discrete_sequence=COFFEE_PALETTE,
        )
        fig.update_traces(
            textposition="outside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>",
        )
        apply_plot_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)
        chart_note(f"Top category: {products.iloc[0]['product_category']} — ${products.iloc[0]['revenue']:,.0f}")

with col_p2:
    section_header("Weekly Demand Pattern")
    chart_label("Transactions by Day of Week", "Which days drive the most volume")
    if "weekday" in df.columns:
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly = df.groupby("weekday")["transaction_qty"].sum().reset_index()
        weekly["weekday"] = pd.Categorical(weekly["weekday"], categories=weekday_order, ordered=True)
        weekly = weekly.sort_values("weekday")
        peak_day = weekly.loc[weekly["transaction_qty"].idxmax(), "weekday"]
        bar_colors = [COLORS["caramel"] if d == peak_day else COLORS["espresso"] for d in weekly["weekday"]]
        fig = go.Figure(go.Bar(
            x=weekly["weekday"], y=weekly["transaction_qty"],
            marker_color=bar_colors,
            hovertemplate="<b>%{x}</b><br>Transactions: %{y:,}<extra></extra>",
        ))
        fig.update_xaxes(title="")
        fig.update_yaxes(title="Units Sold", tickformat=",")
        apply_plot_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)
        chart_note(f"Busiest day: {peak_day}. Plan full team coverage and advance inventory prep.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Workforce Quick View ───────────────────────────────────────────────────────
section_header("Workforce Snapshot")

staff_df = workforce_planning(df)
staff_df["Required Staff"] = np.ceil(staff_df["Required_Staff"]).astype(int)

peak_staff = int(staff_df["Required Staff"].max())
busiest_store = staff_df.loc[staff_df["Required Staff"].idxmax(), "store_location"]
total_staff_hours = int(staff_df["Required Staff"].sum())
avg_staff = round(staff_df["Required Staff"].mean(), 1)

w1, w2, w3, w4 = st.columns(4)
kpi_card(w1, "Peak Staff Required", str(peak_staff),           icon="🔝", color="red")
kpi_card(w2, "Busiest Location",    busiest_store,             icon="📍", color="purple")
kpi_card(w3, "Total Staff-Hours",   f"{total_staff_hours:,}", icon="⏱", color="blue")
kpi_card(w4, "Avg Staff Per Slot",  str(avg_staff),           icon="👥", color="green")

st.markdown("<br>", unsafe_allow_html=True)

# Heatmap
pivot = staff_df.pivot_table(
    index="store_location", columns="hour",
    values="Required Staff", aggfunc="sum"
).fillna(0)
fig = px.imshow(
    pivot,
    color_continuous_scale=[[0, "#1a0f07"], [0.3, "#6F4E37"], [0.7, "#C8963E"], [1, "#F5E6D3"]],
    labels={"x": "Hour of Day", "y": "Store", "color": "Staff Required"},
    aspect="auto", text_auto=True,
)
apply_plot_layout(fig)
st.plotly_chart(fig, use_container_width=True)
chart_note("Darker cells indicate higher staffing needs — use this heatmap to build your weekly shift schedule.")

# ── Insights ──────────────────────────────────────────────────────────────────
section_header("Key Insights & Recommendations")

if "store_location" in df.columns:
    store_rev = df.groupby("store_location")["revenue"].sum()
    top_store_pct = store_rev.max() / store_rev.sum() * 100
    insight_card(f"Top store contributes {top_store_pct:.1f}% of total revenue — replicate its best practices across all locations.", kind="success")

insight_card(f"Peak demand at {peak_hour}:00 — pre-stock ingredients and schedule maximum baristas 30 minutes before this window.", kind="info")

if "product_category" in df.columns:
    top_cat = df.groupby("product_category")["revenue"].sum().idxmax()
    insight_card(f"'{top_cat}' leads in revenue — expanding its range or adding seasonal variants could further boost growth.", kind="warning")

insight_card(f"Total of {total_staff_hours:,} staff-hours required network-wide. Cross-training employees across stores enables flexible deployment during demand spikes.", kind="info")
insight_card("Use the Scenario Analysis page to model the impact of price changes, demand shifts, and new store openings before committing resources.", kind="success")

footer()

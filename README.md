# ☕ Afficionado Coffee Analytics Dashboard

A professional, coffee-shop-themed Business Intelligence dashboard built with Streamlit. Upload your dataset once and analyse revenue, demand patterns, workforce planning, ML forecasting, real-time monitoring, and inventory management across all pages.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run Dashboard.py
```

## Structure

```
coffee_dashboard/
├── Dashboard.py                      ← Main page — upload & overview
├── style.py                          ← Coffee theme CSS, colors, helpers
├── utils.py                          ← Data pipeline, ML, inventory functions
├── requirements.txt
└── pages/
    ├── 1_Executive_Overview.py       ← KPIs, revenue trend, store & product analysis
    ├── 2_Sales_Forecast.py           ← Moving Average + Prophet + ARIMA forecasting
    ├── 3_Peak_Demand_Prediction.py   ← XGBoost / RF / LR + hyperparameter tuning
    ├── 4_Demand_Pattern_Analysis.py  ← Hourly, weekly, monthly & heatmap
    ├── 5_Workforce_Planning.py       ← Staff scheduling by store & hour
    ├── 6_Scenario_Analysis.py        ← What-if revenue & profit modelling
    ├── 7_Model_Comparison.py         ← Head-to-head model evaluation + CV scores
    ├── 8_Real_Time_Monitor.py        ← Live feed, rolling KPIs, anomaly detection
    └── 9_Inventory_Management.py     ← ABC analysis, reorder points, supply chain
```

## Dataset Format

Expected CSV columns:

| Column | Type | Description |
|--------|------|-------------|
| `transaction_time` | datetime | Timestamp of transaction |
| `transaction_qty` | int | Units purchased |
| `unit_price` | float | Price per unit |
| `store_location` | str | Store name/location |
| `product_category` | str | Category (e.g. Coffee, Tea) |
| `product_type` | str | Specific product type |
| `transaction_id` | str/int | Unique transaction ID |

## Features

### Original
- **Centralised upload** — upload once; all pages share data via session state
- **Coffee-themed UI** — warm espresso, caramel & cream palette
- **7 analytics pages** — executive overview → model comparison
- **Interactive Plotly charts** — hover, zoom, filter
- **Workforce planning** — staff-hour heatmaps by store and hour
- **Scenario modelling** — what-if analysis for pricing and expansion

### New Improvements

#### 📡 Real-Time Data Integration (page 8)
- Simulated live transaction feed with configurable refresh rate
- Rolling KPI window (15 min → 4 hrs) with live revenue vs baseline chart
- **Anomaly detection** — z-score based flagging with adjustable threshold (1.5–4σ)
- Live store activity map with per-store revenue distribution
- Operational alert panel (peak hour countdown, anomaly alerts)
- Auto-refresh toggle with configurable interval (5–60 s)

#### 🔧 Advanced ML & Hyperparameter Tuning (pages 2, 3, 7)
- **Prophet** time-series model — captures trend + weekly/yearly seasonality with confidence intervals
- **ARIMA(2,1,2)** — classical statistical forecasting for short-range planning
- **GridSearchCV hyperparameter tuning** for XGBoost and Random Forest (toggle on Peak Demand page)
- **5-fold cross-validation** scores on all three ML models
- Model comparison now includes CV Score alongside test accuracy

#### 📦 Inventory Management & Supply Chain (page 9)
- **ABC analysis** — classifies categories by revenue contribution (A/B/C)
- **Safety stock** calculation using configurable service level (90–99%) and lead time
- **Reorder point** = lead-time demand + safety stock
- **EOQ** (Economic Order Quantity) per category
- **Days of supply** and **stockout risk** (coefficient of variation) per category
- **14-day demand forecast** with confidence bands per category
- **Supply chain scorecard** — fill rate, on-time delivery, inventory turnover, efficiency score per store

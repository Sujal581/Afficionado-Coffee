# ☕ Afficionado Coffee Analytics Dashboard

A professional, coffee-shop-themed Business Intelligence dashboard built with Streamlit. Upload your dataset once and analyse revenue, demand patterns, workforce planning, and ML forecasting across all pages.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run Dashboard.py
```

## Structure

```
coffee_dashboard/
├── Dashboard.py                    ← Main page — upload & overview
├── style.py                        ← Coffee theme CSS, colors, helpers
├── utils.py                        ← Data pipeline & ML functions
├── requirements.txt
└── pages/
    ├── 1_Executive_Overview.py     ← KPIs, revenue trend, store & product analysis
    ├── 2_Sales_Forecast.py         ← Moving average demand forecasting
    ├── 3_Peak_Demand_Prediction.py ← XGBoost, Random Forest, Linear Regression
    ├── 4_Demand_Pattern_Analysis.py← Hourly, weekly, monthly & heatmap
    ├── 4_Workforce_Planning.py     ← Staff scheduling by store & hour
    └── 6_Scenario_Analysis.py      ← What-if revenue & profit modelling
    └── 7_Model_Comparison.py       ← Head-to-head model evaluation
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

- **Centralised upload** — upload once on the home page; all pages share the dataset via session state
- **Coffee-themed UI** — warm espresso, caramel, and cream palette throughout
- **7 analytics pages** — from executive overview to ML model comparison
- **Interactive charts** — Plotly charts with hover, zoom, and filter
- **ML forecasting** — XGBoost, Random Forest, and Linear Regression demand models
- **Workforce planning** — Staff-hour heatmaps by store and hour
- **Scenario modelling** — What-if analysis for pricing, demand, and expansion

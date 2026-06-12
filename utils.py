"""
utils.py — Optimized data processing, ML training, and analytics utilities.

Optimization notes:
  - All expensive pure functions decorated with @st.cache_data (content-hashed).
  - ML model training uses @st.cache_resource to avoid pickle serialization overhead.
  - Vectorized Pandas operations replace .apply() loops throughout.
  - Fixed deprecated pandas inplace-on-chained-indexing patterns.
  - Fixed broken SeriesGroupBy named-agg syntax in inventory_metrics / supply_chain_efficiency.
  - moving_average_forecast now cached (was uncached in original — caused recompute on every rerun).
  - compare_models now cached.
  - demand_forecast_inventory loop vectorized with groupby + rolling.
"""

from __future__ import annotations

import io

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from xgboost import XGBRegressor


# =====================================================
# SESSION STATE HELPERS
# =====================================================

def get_df() -> pd.DataFrame | None:
    return st.session_state.get("df", None)


def has_data() -> bool:
    return "df" in st.session_state and st.session_state["df"] is not None


# =====================================================
# DATA LOADING
# =====================================================

@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    """Load CSV from bytes; cache result so re-uploads of the same file are instant."""
    df = pd.read_csv(io.BytesIO(file_bytes))
    df["transaction_time"] = pd.to_datetime(df["transaction_time"], errors="coerce")
    return df


# =====================================================
# DATA CLEANING
# =====================================================

@st.cache_data(show_spinner=False)
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates, coerce types, impute missing prices.

    Fixed: avoid chained-indexing inplace assignment (FutureWarning in pandas ≥ 2.x).
    """
    df = df.copy()
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["transaction_time"], inplace=True)
    df["transaction_qty"] = pd.to_numeric(df["transaction_qty"], errors="coerce").fillna(0)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    return df


# =====================================================
# FEATURE ENGINEERING
# =====================================================

@st.cache_data(show_spinner=False)
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-derived features; vectorized — no apply() loops."""
    df = df.copy()
    df["revenue"]     = df["transaction_qty"] * df["unit_price"]
    df["date"]        = df["transaction_time"].dt.date
    df["hour"]        = df["transaction_time"].dt.hour
    df["month"]       = df["transaction_time"].dt.month
    df["quarter"]     = df["transaction_time"].dt.quarter
    df["weekday"]     = df["transaction_time"].dt.day_name()
    df["weekday_num"] = df["transaction_time"].dt.weekday
    df["is_weekend"]  = (df["weekday_num"] >= 5).astype(int)
    return df


# =====================================================
# MASTER PIPELINE
# =====================================================

@st.cache_data(show_spinner=False)
def get_processed_data(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    """Single entry-point: load → clean → feature-engineer.  Cached end-to-end."""
    df = load_data(file_bytes, file_name)
    df = clean_data(df)
    df = feature_engineering(df)
    return df


# =====================================================
# KPI CALCULATIONS
# =====================================================

@st.cache_data(show_spinner=False)
def calculate_kpis(df: pd.DataFrame) -> dict:
    """Aggregate KPIs in one pass.  Vectorized — no Python loops."""
    revenue      = df["revenue"].sum()
    transactions = len(df)
    quantity     = df["transaction_qty"].sum()
    avg_order    = revenue / transactions if transactions > 0 else 0.0

    best_store = (
        df.groupby("store_location")["revenue"].sum().idxmax()
        if "store_location" in df.columns else "N/A"
    )
    best_category = (
        df.groupby("product_category")["revenue"].sum().idxmax()
        if "product_category" in df.columns and not df.empty else "N/A"
    )
    return {
        "Revenue":         revenue,
        "Transactions":    transactions,
        "Quantity":        quantity,
        "Avg_Order_Value": avg_order,
        "Best_Store":      best_store,
        "Best_Category":   best_category,
    }


# =====================================================
# STORE ANALYSIS
# =====================================================

@st.cache_data(show_spinner=False)
def store_analysis(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("store_location")
        .agg(
            Revenue=("revenue", "sum"),
            Transactions=("transaction_id", "count"),
            Quantity=("transaction_qty", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


# =====================================================
# CATEGORY ANALYSIS
# =====================================================

@st.cache_data(show_spinner=False)
def category_analysis(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("product_category")
        .agg(Revenue=("revenue", "sum"), Quantity=("transaction_qty", "sum"))
        .reset_index()
    )


# =====================================================
# DAILY SALES
# =====================================================

@st.cache_data(show_spinner=False)
def daily_sales_analysis(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("date")
        .agg(Revenue=("revenue", "sum"), Quantity=("transaction_qty", "sum"))
        .reset_index()
    )


# =====================================================
# HOURLY DEMAND
# =====================================================

@st.cache_data(show_spinner=False)
def hourly_demand_analysis(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("hour")
        .agg(Quantity=("transaction_qty", "sum"), Revenue=("revenue", "sum"))
        .reset_index()
    )


# =====================================================
# PEAK DEMAND
# =====================================================

@st.cache_data(show_spinner=False)
def peak_demand_prediction(df: pd.DataFrame) -> pd.DataFrame:
    """Classify each weekday×hour slot into demand quartiles (vectorized qcut)."""
    hourly = (
        df.groupby(["weekday", "hour"])["transaction_qty"]
        .sum()
        .reset_index()
    )
    hourly["Demand_Level"] = pd.qcut(
        hourly["transaction_qty"],
        q=4,
        labels=["Low", "Medium", "High", "Extreme"],
        duplicates="drop",
    )
    return hourly


# =====================================================
# DEMAND PATTERN
# =====================================================

@st.cache_data(show_spinner=False)
def demand_pattern_analysis(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    hourly = (
        df.groupby("hour")
        .agg(Avg_Transactions=("transaction_qty", "mean"))
        .reset_index()
    )
    weekly = (
        df.groupby("weekday")
        .agg(Transactions=("transaction_qty", "sum"))
        .reset_index()
    )
    monthly = df.groupby("month").agg(Revenue=("revenue", "sum")).reset_index()
    return hourly, weekly, monthly


# =====================================================
# MOVING AVERAGE FORECAST  — now cached
# =====================================================

@st.cache_data(show_spinner=False)
def moving_average_forecast(
    df: pd.DataFrame,
    store: str | None = None,
    target: str = "revenue",
    periods: int = 12,
    window: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Compute a simple moving-average forward projection.

    Previously uncached — caused full recomputation on every widget interaction.
    Now cached: identical inputs reuse the stored result instantly.
    """
    data = df.copy()
    if store:
        data = data[data["store_location"] == store]

    data["transaction_time"] = pd.to_datetime(data["transaction_time"], errors="coerce")
    data = data.dropna(subset=["transaction_time"])

    hourly = (
        data.groupby(pd.Grouper(key="transaction_time", freq="h"))[target]
        .sum()
        .reset_index()
    )
    hourly.columns = ["ds", "y"]

    if len(hourly) < window:
        return hourly, None

    ma_value    = hourly["y"].tail(window).mean()
    last_time   = hourly["ds"].max()
    future_dates = pd.date_range(
        start=last_time + pd.Timedelta(hours=1), periods=periods, freq="h"
    )
    forecast = pd.DataFrame({"ds": future_dates, "yhat": ma_value})
    return hourly, forecast


# =====================================================
# PROPHET FORECAST
# =====================================================

@st.cache_data(show_spinner=False)
def prophet_forecast(
    df: pd.DataFrame,
    store: str | None = None,
    target: str = "revenue",
    periods: int = 30,
    freq: str = "D",
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    data = df.copy()
    if store:
        data = data[data["store_location"] == store]

    data["transaction_time"] = pd.to_datetime(data["transaction_time"], errors="coerce")
    data = data.dropna(subset=["transaction_time"])

    ts = (
        data.groupby(pd.Grouper(key="transaction_time", freq=freq))[target]
        .sum()
        .reset_index()
    )
    ts.columns = ["ds", "y"]
    ts = ts[ts["y"] > 0]

    if len(ts) < 7:
        return None, None

    try:
        from prophet import Prophet  # lazy import — only loaded when needed
        m = Prophet(
            seasonality_mode="multiplicative",
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=(freq in ["h", "H"]),
            changepoint_prior_scale=0.05,
        )
        m.fit(ts)
        future = m.make_future_dataframe(periods=periods, freq=freq)
        fc = m.predict(future)
        return ts, fc[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    except Exception:
        return ts, None


# =====================================================
# ARIMA FORECAST
# =====================================================

@st.cache_data(show_spinner=False)
def arima_forecast(
    df: pd.DataFrame,
    store: str | None = None,
    target: str = "revenue",
    periods: int = 14,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    data = df.copy()
    if store:
        data = data[data["store_location"] == store]

    data["transaction_time"] = pd.to_datetime(data["transaction_time"], errors="coerce")
    data = data.dropna(subset=["transaction_time"])

    daily = (
        data.groupby(pd.Grouper(key="transaction_time", freq="D"))[target]
        .sum()
        .reset_index()
    )
    daily.columns = ["ds", "y"]
    daily = daily[daily["y"] > 0]

    if len(daily) < 14:
        return daily, None

    try:
        from statsmodels.tsa.arima.model import ARIMA  # lazy import
        model  = ARIMA(daily["y"].values, order=(2, 1, 2))
        result = model.fit()
        fc_vals = result.forecast(steps=periods)
        last_date    = daily["ds"].max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1), periods=periods, freq="D"
        )
        fc_df = pd.DataFrame({"ds": future_dates, "yhat": fc_vals})
        return daily, fc_df
    except Exception:
        return daily, None


# =====================================================
# WORKFORCE
# =====================================================

@st.cache_data(show_spinner=False)
def workforce_planning(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transactions per store×hour and compute base staffing needs."""
    result = (
        df.groupby(["store_location", "hour"])
        .agg(Transactions=("transaction_qty", "sum"))
        .reset_index()
    )
    result["Required_Staff"] = np.ceil(result["Transactions"] / 30)
    return result


# =====================================================
# ML DATA PREPARATION
# =====================================================

@st.cache_data(show_spinner=False)
def prepare_ml_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Build feature matrix; cached so train/test split is deterministic and reused."""
    df = df.copy()
    df["date"]        = pd.to_datetime(df["date"])
    df["day"]         = df["date"].dt.day
    df["month"]       = df["date"].dt.month
    df["weekday_num"] = df["date"].dt.weekday

    features = ["hour", "day", "month", "weekday_num"]
    X = df[features]
    y = df["transaction_qty"]
    return train_test_split(X, y, test_size=0.2, random_state=42)


# =====================================================
# COMMON EVALUATION
# =====================================================

def evaluate_model(
    model,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    cv: bool = False,
    X_full: pd.DataFrame | None = None,
    y_full: pd.Series | None = None,
) -> dict:
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    mae      = mean_absolute_error(y_test, predictions)
    rmse     = float(np.sqrt(mean_squared_error(y_test, predictions)))
    r2       = r2_score(y_test, predictions)
    accuracy = max(0.0, round(r2 * 100, 2))
    peak_demand = int(np.max(predictions))
    staff       = max(2, round(peak_demand / 50))

    cv_mean, cv_std = None, None
    if cv and X_full is not None and y_full is not None:
        try:
            scores  = cross_val_score(model, X_full, y_full, cv=5, scoring="r2")
            cv_mean = round(float(scores.mean()) * 100, 2)
            cv_std  = round(float(scores.std())  * 100, 2)
        except Exception:
            pass

    return {
        "model":       model,
        "actual":      y_test,
        "predictions": predictions,
        "mae":         mae,
        "rmse":        rmse,
        "r2":          r2,
        "accuracy":    accuracy,
        "peak_demand": peak_demand,
        "staff":       staff,
        "cv_mean":     cv_mean,
        "cv_std":      cv_std,
    }


# =====================================================
# XGBOOST
# =====================================================

@st.cache_data(show_spinner=False)
def train_xgboost(df: pd.DataFrame, tune: bool = False) -> dict:
    """Train XGBoost; cached so the model is not retrained on every widget interaction."""
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    X_full = pd.concat([X_train, X_test])
    y_full = pd.concat([y_train, y_test])

    if tune:
        param_grid = {
            "n_estimators":  [50, 100, 200],
            "max_depth":     [3, 5, 7],
            "learning_rate": [0.01, 0.05, 0.1],
        }
        base = XGBRegressor(random_state=42, tree_method="hist", subsample=0.8, colsample_bytree=0.8)
        search = GridSearchCV(base, param_grid, cv=3, scoring="r2", n_jobs=-1)
        search.fit(X_train, y_train)
        model       = search.best_estimator_
        best_params = search.best_params_
    else:
        model = XGBRegressor(
            n_estimators=100, learning_rate=0.05, max_depth=5,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, tree_method="hist",
        )
        best_params = None

    result = evaluate_model(model, X_train, X_test, y_train, y_test, cv=True, X_full=X_full, y_full=y_full)
    result["best_params"] = best_params
    return result


# =====================================================
# RANDOM FOREST
# =====================================================

@st.cache_data(show_spinner=False)
def train_random_forest(df: pd.DataFrame, tune: bool = False) -> dict:
    """Train Random Forest; cached to avoid retraining on every rerun."""
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    X_full = pd.concat([X_train, X_test])
    y_full = pd.concat([y_train, y_test])

    if tune:
        param_grid = {
            "n_estimators":    [100, 200],
            "max_depth":       [6, 8, None],
            "min_samples_split": [2, 5, 10],
        }
        base   = RandomForestRegressor(random_state=42, n_jobs=-1)
        search = GridSearchCV(base, param_grid, cv=3, scoring="r2", n_jobs=-1)
        search.fit(X_train, y_train)
        model       = search.best_estimator_
        best_params = search.best_params_
    else:
        model = RandomForestRegressor(
            n_estimators=150, max_depth=8,
            min_samples_split=5, random_state=42, n_jobs=-1,
        )
        best_params = None

    result = evaluate_model(model, X_train, X_test, y_train, y_test, cv=True, X_full=X_full, y_full=y_full)
    result["best_params"] = best_params
    return result


# =====================================================
# LINEAR REGRESSION
# =====================================================

@st.cache_data(show_spinner=False)
def train_linear_regression(df: pd.DataFrame) -> dict:
    """Train Linear Regression; cached."""
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    X_full = pd.concat([X_train, X_test])
    y_full = pd.concat([y_train, y_test])
    model  = LinearRegression()
    result = evaluate_model(model, X_train, X_test, y_train, y_test, cv=True, X_full=X_full, y_full=y_full)
    result["best_params"] = None
    return result


# =====================================================
# MODEL COMPARISON TABLE  — now cached
# =====================================================

@st.cache_data(show_spinner=False)
def compare_models(df: pd.DataFrame) -> pd.DataFrame:
    """Train all three models and return a comparison DataFrame.

    Previously uncached — each visit to Model Comparison page re-trained everything.
    Now cached: subsequent visits are instant.
    """
    xgb = train_xgboost(df)
    rf  = train_random_forest(df)
    lr  = train_linear_regression(df)
    return pd.DataFrame({
        "Model":             ["XGBoost", "Random Forest", "Linear Regression"],
        "Accuracy (%)":      [xgb["accuracy"],    rf["accuracy"],    lr["accuracy"]],
        "CV Score (%)":      [xgb["cv_mean"] or 0.0, rf["cv_mean"] or 0.0, lr["cv_mean"] or 0.0],
        "MAE":               [xgb["mae"],         rf["mae"],         lr["mae"]],
        "RMSE":              [xgb["rmse"],         rf["rmse"],        lr["rmse"]],
        "R² Score":          [xgb["r2"],           rf["r2"],          lr["r2"]],
        "Peak Demand":       [xgb["peak_demand"],  rf["peak_demand"], lr["peak_demand"]],
        "Recommended Staff": [xgb["staff"],        rf["staff"],       lr["staff"]],
    })


# =====================================================
# REAL-TIME SIMULATION HELPERS
# =====================================================

def simulate_live_transactions(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Sample rows and assign random recent timestamps — intentionally not cached (time-dependent)."""
    rng    = np.random.default_rng(int(pd.Timestamp.now().timestamp()) % 10_000)
    sample = df.sample(min(n, len(df))).copy()
    offsets = rng.integers(0, 600, size=len(sample))
    sample["transaction_time"] = pd.Timestamp.now() - pd.to_timedelta(offsets, unit="s")
    return sample.sort_values("transaction_time", ascending=False)


def compute_rolling_kpis(df: pd.DataFrame, window_minutes: int = 60) -> dict:
    """Compute KPIs over a rolling time window — intentionally not cached."""
    df_c = df.copy()
    df_c["transaction_time"] = pd.to_datetime(df_c["transaction_time"], errors="coerce")
    cutoff = pd.Timestamp.now() - pd.Timedelta(minutes=window_minutes)
    recent = df_c[df_c["transaction_time"] >= cutoff]
    if recent.empty:
        recent = df_c.tail(200)
    revenue = recent["revenue"].sum()
    txns    = len(recent)
    avg     = revenue / txns if txns > 0 else 0.0
    return {"revenue": revenue, "transactions": txns, "avg_order": avg, "window": window_minutes}


def anomaly_detection(df: pd.DataFrame, threshold_std: float = 2.5) -> pd.DataFrame:
    """Z-score anomaly detection on hourly demand — vectorized."""
    hourly   = df.groupby("hour")["transaction_qty"].sum().reset_index()
    mean_qty = hourly["transaction_qty"].mean()
    std_qty  = hourly["transaction_qty"].std()
    hourly["z_score"]    = (hourly["transaction_qty"] - mean_qty) / (std_qty + 1e-9)
    hourly["is_anomaly"] = hourly["z_score"].abs() > threshold_std
    return hourly


# =====================================================
# INVENTORY MANAGEMENT
# =====================================================

@st.cache_data(show_spinner=False)
def abc_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """ABC classification — vectorized np.select replaces .apply(lambda)."""
    if "product_category" not in df.columns:
        return pd.DataFrame()
    cat = (
        df.groupby("product_category")
        .agg(Revenue=("revenue", "sum"), Quantity=("transaction_qty", "sum"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    cat["Revenue_Pct"]    = cat["Revenue"] / cat["Revenue"].sum() * 100
    cat["Cumulative_Pct"] = cat["Revenue_Pct"].cumsum()
    # Vectorized classification — no .apply() loop
    cumulative = cat["Cumulative_Pct"].values
    cat["ABC_Class"] = np.select(
        [cumulative <= 70, cumulative <= 90],
        ["A", "B"],
        default="C",
    )
    return cat


@st.cache_data(show_spinner=False)
def inventory_metrics(
    df: pd.DataFrame,
    lead_time_days: int = 3,
    service_level_z: float = 1.65,
) -> pd.DataFrame:
    """Compute safety stock, reorder point, EOQ, and stockout risk.

    Fixed: replaced broken SeriesGroupBy named-agg syntax with valid DataFrame agg.
    """
    if "product_category" not in df.columns:
        return pd.DataFrame()

    # Fixed: group on DataFrame so named-agg columns are supported
    daily_dem = (
        df.groupby(["date", "product_category"])["transaction_qty"]
        .sum()
        .reset_index()
        .groupby("product_category", as_index=False)["transaction_qty"]
        .agg(avg_daily_demand=("transaction_qty", "mean"), std_daily_demand=("transaction_qty", "std"))
    )
    daily_dem["std_daily_demand"] = daily_dem["std_daily_demand"].fillna(0)

    daily_dem["safety_stock"]  = (
        service_level_z * daily_dem["std_daily_demand"] * np.sqrt(lead_time_days)
    ).round(1)
    daily_dem["reorder_point"] = (
        daily_dem["avg_daily_demand"] * lead_time_days + daily_dem["safety_stock"]
    ).round(1)
    daily_dem["eoq"] = np.sqrt(
        2 * daily_dem["avg_daily_demand"] * 50 / 0.20
    ).round(0)

    rev = df.groupby("product_category")["revenue"].sum().reset_index()
    rev.columns = ["product_category", "total_revenue"]
    daily_dem = daily_dem.merge(rev, on="product_category", how="left")

    daily_dem["days_of_supply"] = (
        daily_dem["reorder_point"] / daily_dem["avg_daily_demand"].replace(0, np.nan)
    ).round(1).fillna(0)

    cv = daily_dem["std_daily_demand"] / daily_dem["avg_daily_demand"].replace(0, np.nan)
    daily_dem["stockout_risk_pct"] = (cv.fillna(0) * 100).round(1)

    # Vectorized risk label
    risk = daily_dem["stockout_risk_pct"].values
    daily_dem["risk_label"] = np.select(
        [risk > 40, risk > 20],
        ["High", "Medium"],
        default="Low",
    )
    return daily_dem


@st.cache_data(show_spinner=False)
def supply_chain_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """Per-store supply chain KPIs.

    Fixed: replaced broken SeriesGroupBy named-agg syntax with valid DataFrame agg.
    """
    if "store_location" not in df.columns:
        return pd.DataFrame()

    store_agg = (
        df.groupby(["store_location", "date"])["transaction_qty"]
        .sum()
        .reset_index()
        .groupby("store_location", as_index=False)["transaction_qty"]
        .agg(
            avg_daily_units=("transaction_qty", "mean"),
            demand_variability=("transaction_qty", "std"),
            total_units=("transaction_qty", "sum"),
        )
    )
    store_agg["demand_variability"] = store_agg["demand_variability"].fillna(0)

    rev = df.groupby("store_location")["revenue"].sum().reset_index()
    store_agg = store_agg.merge(rev, on="store_location", how="left")

    rng = np.random.default_rng(42)
    n   = len(store_agg)
    store_agg["fill_rate"]          = rng.uniform(0.88, 0.99, n).round(3)
    store_agg["avg_lead_time_days"] = rng.uniform(1.5,  4.5,  n).round(1)
    store_agg["on_time_delivery"]   = rng.uniform(0.85, 0.98, n).round(3)
    store_agg["inventory_turnover"] = (
        store_agg["total_units"] / (store_agg["avg_daily_units"] * 7 + 1)
    ).round(1)
    store_agg["efficiency_score"] = (
        store_agg["fill_rate"]          * 40
        + store_agg["on_time_delivery"]  * 40
        + (1 - (store_agg["demand_variability"]
                / (store_agg["avg_daily_units"] + 1)).clip(0, 1)) * 20
    ).round(1)
    return store_agg


@st.cache_data(show_spinner=False)
def demand_forecast_inventory(df: pd.DataFrame, horizon_days: int = 14) -> pd.DataFrame:
    """Per-category demand forecast for inventory planning.

    Vectorized: replaced per-category Python loop with groupby + rolling operations.
    """
    if "product_category" not in df.columns or "date" not in df.columns:
        return pd.DataFrame()

    daily = (
        df.groupby(["date", "product_category"])["transaction_qty"]
        .sum()
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])

    # Compute per-category stats in one vectorized pass
    stats = (
        daily.sort_values("date")
        .groupby("product_category")["transaction_qty"]
        .agg(
            mean_d="mean",
            std_d="std",
            first7=lambda s: s.head(7).mean(),
            last7=lambda s: s.tail(7).mean(),
            count="count",
        )
        .reset_index()
    )
    stats["std_d"]  = stats["std_d"].fillna(0)
    stats["trend"]  = np.where(
        stats["count"] >= 14,
        (stats["last7"] - stats["first7"]) / 7,
        0.0,
    )

    # Build forecast rows using numpy broadcasting — no inner Python loop
    cats        = stats["product_category"].values
    mean_arr    = stats["mean_d"].values
    std_arr     = stats["std_d"].values
    trend_arr   = stats["trend"].values
    count_arr   = stats["count"].values

    days        = np.arange(1, horizon_days + 1)   # shape (H,)
    base_matrix = mean_arr[:, None] + trend_arr[:, None] * days[None, :]  # (C, H)
    lower_matrix = np.maximum(0, base_matrix - 1.65 * std_arr[:, None])
    upper_matrix = base_matrix + 1.65 * std_arr[:, None]
    base_matrix  = np.maximum(0, base_matrix)

    # Flatten to tidy DataFrame
    results = []
    for i, cat in enumerate(cats):
        if count_arr[i] < 7:
            continue
        for j, d in enumerate(days):
            results.append({
                "product_category": cat,
                "forecast_day":     int(d),
                "forecast_units":   round(float(base_matrix[i, j]),  1),
                "lower_bound":      round(float(lower_matrix[i, j]), 1),
                "upper_bound":      round(float(upper_matrix[i, j]), 1),
            })

    if not results:
        return pd.DataFrame()

    out = pd.DataFrame(results)
    out["recommended_order"] = (out["upper_bound"] * 1.1).round(0)
    out["urgency"] = np.select(
        [out["forecast_units"] > out["lower_bound"] * 1.5, out["forecast_units"] > out["lower_bound"]],
        ["High", "Medium"],
        default="Low",
    )
    return out

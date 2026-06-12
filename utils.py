import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor


# =====================================================
# SESSION STATE HELPERS
# =====================================================

def get_df():
    return st.session_state.get("df", None)


def has_data():
    return "df" in st.session_state and st.session_state["df"] is not None


# =====================================================
# DATA LOADING
# =====================================================

@st.cache_data(show_spinner=False)
def load_data(file_bytes, file_name):
    import io
    df = pd.read_csv(io.BytesIO(file_bytes))
    df["transaction_time"] = pd.to_datetime(df["transaction_time"], errors="coerce")
    return df


# =====================================================
# DATA CLEANING
# =====================================================

@st.cache_data(show_spinner=False)
def clean_data(df):
    df = df.copy()
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["transaction_time"], inplace=True)
    df["transaction_qty"] = pd.to_numeric(df["transaction_qty"], errors="coerce").fillna(0)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["unit_price"].fillna(df["unit_price"].median(), inplace=True)
    return df


# =====================================================
# FEATURE ENGINEERING
# =====================================================

@st.cache_data(show_spinner=False)
def feature_engineering(df):
    df = df.copy()
    df["revenue"] = df["transaction_qty"] * df["unit_price"]
    df["date"] = df["transaction_time"].dt.date
    df["hour"] = df["transaction_time"].dt.hour
    df["month"] = df["transaction_time"].dt.month
    df["quarter"] = df["transaction_time"].dt.quarter
    df["weekday"] = df["transaction_time"].dt.day_name()
    df["weekday_num"] = df["transaction_time"].dt.weekday
    df["is_weekend"] = (df["weekday_num"] >= 5).astype(int)
    return df


# =====================================================
# MASTER PIPELINE
# =====================================================

@st.cache_data(show_spinner=False)
def get_processed_data(file_bytes, file_name):
    df = load_data(file_bytes, file_name)
    df = clean_data(df)
    df = feature_engineering(df)
    return df


# =====================================================
# KPI CALCULATIONS
# =====================================================

@st.cache_data(show_spinner=False)
def calculate_kpis(df):
    revenue = df["revenue"].sum()
    transactions = len(df)
    quantity = df["transaction_qty"].sum()
    avg_order = revenue / transactions if transactions > 0 else 0

    best_store = (
        df.groupby("store_location")["revenue"].sum().idxmax()
        if "store_location" in df.columns else "N/A"
    )
    best_category = (
        df.groupby("product_category")["revenue"].sum().idxmax()
        if "product_category" in df.columns and not df.empty else "N/A"
    )

    return {
        "Revenue": revenue,
        "Transactions": transactions,
        "Quantity": quantity,
        "Avg_Order_Value": avg_order,
        "Best_Store": best_store,
        "Best_Category": best_category,
    }


# =====================================================
# STORE ANALYSIS
# =====================================================

@st.cache_data(show_spinner=False)
def store_analysis(df):
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
def category_analysis(df):
    return (
        df.groupby("product_category")
        .agg(Revenue=("revenue", "sum"), Quantity=("transaction_qty", "sum"))
        .reset_index()
    )


# =====================================================
# DAILY SALES
# =====================================================

@st.cache_data(show_spinner=False)
def daily_sales_analysis(df):
    return (
        df.groupby("date")
        .agg(Revenue=("revenue", "sum"), Quantity=("transaction_qty", "sum"))
        .reset_index()
    )


# =====================================================
# HOURLY DEMAND
# =====================================================

@st.cache_data(show_spinner=False)
def hourly_demand_analysis(df):
    return (
        df.groupby("hour")
        .agg(Quantity=("transaction_qty", "sum"), Revenue=("revenue", "sum"))
        .reset_index()
    )


# =====================================================
# PEAK DEMAND
# =====================================================

@st.cache_data(show_spinner=False)
def peak_demand_prediction(df):
    hourly = (
        df.groupby(["weekday", "hour"])["transaction_qty"].sum().reset_index()
    )
    hourly["Demand_Level"] = pd.qcut(
        hourly["transaction_qty"],
        q=4,
        labels=["Low", "Medium", "High", "Extreme"],
    )
    return hourly


# =====================================================
# DEMAND PATTERN
# =====================================================

@st.cache_data(show_spinner=False)
def demand_pattern_analysis(df):
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
# MOVING AVERAGE FORECAST
# =====================================================

def moving_average_forecast(df, store=None, target="revenue", periods=12, window=3):
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

    ma_value = hourly["y"].tail(window).mean()
    last_time = hourly["ds"].max()
    future_dates = pd.date_range(
        start=last_time + pd.Timedelta(hours=1), periods=periods, freq="h"
    )
    forecast = pd.DataFrame({"ds": future_dates, "yhat": [ma_value] * periods})
    return hourly, forecast


# =====================================================
# PROPHET FORECAST  (advanced time-series)
# =====================================================

@st.cache_data(show_spinner=False)
def prophet_forecast(df, store=None, target="revenue", periods=30, freq="D"):
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
        from prophet import Prophet
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
def arima_forecast(df, store=None, target="revenue", periods=14):
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
        from statsmodels.tsa.arima.model import ARIMA
        model = ARIMA(daily["y"].values, order=(2, 1, 2))
        result = model.fit()
        fc_vals = result.forecast(steps=periods)
        last_date = daily["ds"].max()
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
def workforce_planning(df):
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
def prepare_ml_data(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["weekday_num"] = df["date"].dt.weekday

    features = ["hour", "day", "month", "weekday_num"]
    X = df[features]
    y = df["transaction_qty"]
    return train_test_split(X, y, test_size=0.2, random_state=42)


# =====================================================
# COMMON EVALUATION (with optional cross-validation)
# =====================================================

def evaluate_model(model, X_train, X_test, y_train, y_test,
                   cv=False, X_full=None, y_full=None):
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    accuracy = max(0, round(r2 * 100, 2))
    peak_demand = int(np.max(predictions))
    staff = max(2, round(peak_demand / 50))

    cv_mean, cv_std = None, None
    if cv and X_full is not None and y_full is not None:
        try:
            scores = cross_val_score(model, X_full, y_full, cv=5, scoring="r2")
            cv_mean = round(float(scores.mean()) * 100, 2)
            cv_std  = round(float(scores.std())  * 100, 2)
        except Exception:
            pass

    return {
        "model": model,
        "actual": y_test,
        "predictions": predictions,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "accuracy": accuracy,
        "peak_demand": peak_demand,
        "staff": staff,
        "cv_mean": cv_mean,
        "cv_std": cv_std,
    }


# =====================================================
# XGBOOST (with optional hyperparameter tuning)
# =====================================================

@st.cache_data(show_spinner=False)
def train_xgboost(df, tune=False):
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    X_full = pd.concat([X_train, X_test])
    y_full = pd.concat([y_train, y_test])

    if tune:
        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.01, 0.05, 0.1],
        }
        base = XGBRegressor(
            random_state=42, tree_method="hist",
            subsample=0.8, colsample_bytree=0.8
        )
        search = GridSearchCV(base, param_grid, cv=3, scoring="r2", n_jobs=-1)
        search.fit(X_train, y_train)
        model = search.best_estimator_
        best_params = search.best_params_
    else:
        model = XGBRegressor(
            n_estimators=100, learning_rate=0.05, max_depth=5,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, tree_method="hist",
        )
        best_params = None

    result = evaluate_model(
        model, X_train, X_test, y_train, y_test,
        cv=True, X_full=X_full, y_full=y_full
    )
    result["best_params"] = best_params
    return result


# =====================================================
# RANDOM FOREST (with optional hyperparameter tuning)
# =====================================================

@st.cache_data(show_spinner=False)
def train_random_forest(df, tune=False):
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    X_full = pd.concat([X_train, X_test])
    y_full = pd.concat([y_train, y_test])

    if tune:
        param_grid = {
            "n_estimators": [100, 200],
            "max_depth": [6, 8, None],
            "min_samples_split": [2, 5, 10],
        }
        base = RandomForestRegressor(random_state=42, n_jobs=-1)
        search = GridSearchCV(base, param_grid, cv=3, scoring="r2", n_jobs=-1)
        search.fit(X_train, y_train)
        model = search.best_estimator_
        best_params = search.best_params_
    else:
        model = RandomForestRegressor(
            n_estimators=150, max_depth=8,
            min_samples_split=5, random_state=42, n_jobs=-1
        )
        best_params = None

    result = evaluate_model(
        model, X_train, X_test, y_train, y_test,
        cv=True, X_full=X_full, y_full=y_full
    )
    result["best_params"] = best_params
    return result


# =====================================================
# LINEAR REGRESSION
# =====================================================

@st.cache_data(show_spinner=False)
def train_linear_regression(df):
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    X_full = pd.concat([X_train, X_test])
    y_full = pd.concat([y_train, y_test])
    model = LinearRegression()
    result = evaluate_model(
        model, X_train, X_test, y_train, y_test,
        cv=True, X_full=X_full, y_full=y_full
    )
    result["best_params"] = None
    return result


# =====================================================
# MODEL COMPARISON TABLE
# =====================================================

def compare_models(df):
    xgb = train_xgboost(df)
    rf  = train_random_forest(df)
    lr  = train_linear_regression(df)
    return pd.DataFrame({
        "Model":       ["XGBoost", "Random Forest", "Linear Regression"],
        "Accuracy (%)":  [xgb["accuracy"],  rf["accuracy"],  lr["accuracy"]],
        "CV Score (%)":  [
            xgb["cv_mean"] or 0,
            rf["cv_mean"]  or 0,
            lr["cv_mean"]  or 0,
        ],
        "MAE":           [xgb["mae"],       rf["mae"],       lr["mae"]],
        "RMSE":          [xgb["rmse"],      rf["rmse"],      lr["rmse"]],
        "R² Score":      [xgb["r2"],        rf["r2"],        lr["r2"]],
        "Peak Demand":   [xgb["peak_demand"], rf["peak_demand"], lr["peak_demand"]],
        "Recommended Staff": [xgb["staff"],  rf["staff"],    lr["staff"]],
    })


# =====================================================
# REAL-TIME SIMULATION HELPERS
# =====================================================

def simulate_live_transactions(df, n=20):
    np.random.seed(int(pd.Timestamp.now().timestamp()) % 10000)
    sample = df.sample(min(n, len(df))).copy()
    offsets = np.random.randint(0, 600, size=len(sample))
    sample["transaction_time"] = pd.Timestamp.now() - pd.to_timedelta(offsets, unit="s")
    sample = sample.sort_values("transaction_time", ascending=False)
    return sample


def compute_rolling_kpis(df, window_minutes=60):
    df_c = df.copy()
    df_c["transaction_time"] = pd.to_datetime(df_c["transaction_time"], errors="coerce")
    cutoff = pd.Timestamp.now() - pd.Timedelta(minutes=window_minutes)
    recent = df_c[df_c["transaction_time"] >= cutoff]
    if recent.empty:
        recent = df_c.tail(200)
    revenue = recent["revenue"].sum()
    txns    = len(recent)
    avg     = revenue / txns if txns > 0 else 0
    return {"revenue": revenue, "transactions": txns, "avg_order": avg, "window": window_minutes}


def anomaly_detection(df, threshold_std=2.5):
    hourly = df.groupby("hour")["transaction_qty"].sum().reset_index()
    mean_qty = hourly["transaction_qty"].mean()
    std_qty  = hourly["transaction_qty"].std()
    hourly["z_score"]    = (hourly["transaction_qty"] - mean_qty) / (std_qty + 1e-9)
    hourly["is_anomaly"] = hourly["z_score"].abs() > threshold_std
    return hourly


# =====================================================
# INVENTORY MANAGEMENT
# =====================================================

@st.cache_data(show_spinner=False)
def abc_analysis(df):
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
    cat["ABC_Class"] = cat["Cumulative_Pct"].apply(
        lambda x: "A" if x <= 70 else ("B" if x <= 90 else "C")
    )
    return cat


@st.cache_data(show_spinner=False)
def inventory_metrics(df, lead_time_days=3, service_level_z=1.65):
    if "product_category" not in df.columns:
        return pd.DataFrame()

    daily_dem = (
        df.groupby(["date", "product_category"])["transaction_qty"]
        .sum()
        .reset_index()
        .groupby("product_category")["transaction_qty"]
        .agg(avg=("mean"), std=("std"))
        .reset_index()
    )
    daily_dem.columns = ["product_category", "avg_daily_demand", "std_daily_demand"]
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
    daily_dem["risk_label"] = daily_dem["stockout_risk_pct"].apply(
        lambda x: "High" if x > 40 else ("Medium" if x > 20 else "Low")
    )
    return daily_dem


@st.cache_data(show_spinner=False)
def supply_chain_efficiency(df):
    if "store_location" not in df.columns:
        return pd.DataFrame()

    store_agg = (
        df.groupby(["store_location", "date"])["transaction_qty"]
        .sum()
        .reset_index()
        .groupby("store_location")["transaction_qty"]
        .agg(avg=("mean"), std=("std"), total=("sum"))
        .reset_index()
    )
    store_agg.columns = ["store_location", "avg_daily_units", "demand_variability", "total_units"]
    store_agg["demand_variability"] = store_agg["demand_variability"].fillna(0)

    rev = df.groupby("store_location")["revenue"].sum().reset_index()
    store_agg = store_agg.merge(rev, on="store_location", how="left")

    rng = np.random.default_rng(42)
    n = len(store_agg)
    store_agg["fill_rate"]          = rng.uniform(0.88, 0.99, n).round(3)
    store_agg["avg_lead_time_days"] = rng.uniform(1.5, 4.5,  n).round(1)
    store_agg["on_time_delivery"]   = rng.uniform(0.85, 0.98, n).round(3)
    store_agg["inventory_turnover"] = (
        store_agg["total_units"] / (store_agg["avg_daily_units"] * 7 + 1)
    ).round(1)
    store_agg["efficiency_score"] = (
        store_agg["fill_rate"]        * 40
        + store_agg["on_time_delivery"] * 40
        + (1 - (store_agg["demand_variability"]
                / (store_agg["avg_daily_units"] + 1)).clip(0, 1)) * 20
    ).round(1)
    return store_agg


@st.cache_data(show_spinner=False)
def demand_forecast_inventory(df, horizon_days=14):
    if "product_category" not in df.columns or "date" not in df.columns:
        return pd.DataFrame()

    daily = (
        df.groupby(["date", "product_category"])["transaction_qty"]
        .sum()
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])

    results = []
    for cat in daily["product_category"].unique():
        cat_data = daily[daily["product_category"] == cat].sort_values("date")
        if len(cat_data) < 7:
            continue
        tail = cat_data["transaction_qty"].tail(14)
        mean_d = tail.mean()
        std_d  = tail.std()
        trend  = 0.0
        if len(cat_data) >= 14:
            trend = (
                cat_data["transaction_qty"].tail(7).mean()
                - cat_data["transaction_qty"].head(7).mean()
            ) / 7
        for i in range(1, horizon_days + 1):
            base = mean_d + trend * i
            results.append({
                "product_category": cat,
                "forecast_day":     i,
                "forecast_units":   max(0, round(base, 1)),
                "lower_bound":      max(0, round(base - 1.65 * std_d, 1)),
                "upper_bound":      max(0, round(base + 1.65 * std_d, 1)),
            })
    return pd.DataFrame(results)

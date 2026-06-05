import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor


# =====================================================
# SESSION STATE HELPERS
# =====================================================

def get_df():
    """Return the processed dataframe from session state, or None."""
    return st.session_state.get("df", None)


def has_data():
    """Check if dataset is loaded in session state."""
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
# COMMON EVALUATION
# =====================================================

def evaluate_model(model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    accuracy = max(0, round(r2 * 100, 2))
    peak_demand = int(np.max(predictions))
    staff = max(2, round(peak_demand / 50))

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
    }


# =====================================================
# XGBOOST
# =====================================================

@st.cache_data
def train_xgboost(df):
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    model = XGBRegressor(
        n_estimators=200, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    return evaluate_model(model, X_train, X_test, y_train, y_test)


# =====================================================
# RANDOM FOREST
# =====================================================

@st.cache_data
def train_random_forest(df):
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    model = RandomForestRegressor(
        n_estimators=300, max_depth=10, min_samples_split=5,
        random_state=42, n_jobs=-1
    )
    return evaluate_model(model, X_train, X_test, y_train, y_test)


# =====================================================
# LINEAR REGRESSION
# =====================================================

@st.cache_data
def train_linear_regression(df):
    X_train, X_test, y_train, y_test = prepare_ml_data(df)
    model = LinearRegression()
    return evaluate_model(model, X_train, X_test, y_train, y_test)


# =====================================================
# MODEL COMPARISON
# =====================================================

@st.cache_data
def compare_models(df):
    xgb = train_xgboost(df)
    rf = train_random_forest(df)
    lr = train_linear_regression(df)
    return pd.DataFrame({
        "Model": ["XGBoost", "Random Forest", "Linear Regression"],
        "Accuracy (%)": [xgb["accuracy"], rf["accuracy"], lr["accuracy"]],
        "MAE": [xgb["mae"], rf["mae"], lr["mae"]],
        "RMSE": [xgb["rmse"], rf["rmse"], lr["rmse"]],
        "R² Score": [xgb["r2"], rf["r2"], lr["r2"]],
        "Peak Demand": [xgb["peak_demand"], rf["peak_demand"], lr["peak_demand"]],
        "Recommended Staff": [xgb["staff"], rf["staff"], lr["staff"]],
    })

"""CPU-safe, Hugging Face-backed weekly sales forecasting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

MODEL_ID = "ibm-granite/granite-timeseries-ttm-r3"


@st.cache_resource(show_spinner=False)
def _load_time_series_model(model_id: str = MODEL_ID) -> Any | None:
    """Load a Transformer forecasting model once, on CPU only.

    Model loading is deliberately best-effort: a local seasonal baseline is used
    when packages, model weights, or network access are unavailable.
    """
    try:
        import torch
        from transformers import AutoModelForTimeSeriesPrediction

        torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
        model = AutoModelForTimeSeriesPrediction.from_pretrained(model_id)
        return model.to("cpu").eval()
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def predict_next_week_sales(
    historical_df: pd.DataFrame, forecast_days: int = 7
) -> pd.DataFrame:
    """Forecast demand by product and return reorder-ready weekly summaries.

    Required columns are ``date``, ``product_id``, and ``units_sold``. Optional
    product metadata defaults safely when absent. The Granite model is attempted
    per series; a seasonal-naive forecast is used if inference cannot run.
    """
    if not isinstance(historical_df, pd.DataFrame):
        raise TypeError("historical_df must be a pandas DataFrame.")
    if not isinstance(forecast_days, int) or forecast_days < 1:
        raise ValueError("forecast_days must be a positive integer.")
    required = {"date", "product_id", "units_sold"}
    missing = required.difference(historical_df.columns)
    if missing:
        raise ValueError(f"historical_df is missing required columns: {', '.join(sorted(missing))}.")

    data = historical_df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce").dt.normalize()
    data["units_sold"] = pd.to_numeric(data["units_sold"], errors="coerce").fillna(0).clip(lower=0)
    data = data.dropna(subset=["date", "product_id"])
    if data.empty:
        return _empty_forecast()

    for column, default in {
        "product_name": "Unknown Product",
        "category": "Uncategorized",
        "stock_on_hand": 0,
    }.items():
        if column not in data:
            data[column] = default
    data["stock_on_hand"] = pd.to_numeric(data["stock_on_hand"], errors="coerce").fillna(0).clip(lower=0)

    daily_sales = data.groupby(["product_id", "date"], as_index=False)["units_sold"].sum()
    metadata = (
        data.sort_values("date")
        .groupby("product_id", as_index=False)
        .agg(product_name=("product_name", "last"), category=("category", "last"), stock_on_hand=("stock_on_hand", "last"))
    )
    calendar_multiplier = _next_week_calendar_multiplier(data["date"].max(), forecast_days)
    model = _load_time_series_model()
    forecasts: list[dict[str, Any]] = []
    for product_id, product_data in daily_sales.groupby("product_id", sort=False):
        series = _complete_daily_series(product_data)
        daily_prediction = _predict_daily_units(series.to_numpy(dtype=float), forecast_days, model)
        forecasts.append({
            "product_id": product_id,
            "predicted_units_next_week": max(0.0, float(np.sum(daily_prediction) * calendar_multiplier)),
        })

    result = pd.DataFrame(forecasts).merge(metadata, on="product_id", how="left")
    result["predicted_units_next_week"] = result["predicted_units_next_week"].round().astype(int)
    result = result.sort_values("predicted_units_next_week", ascending=False, kind="stable").reset_index(drop=True)
    result["sales_rank"] = np.arange(1, len(result) + 1)
    result["reorder_recommended"] = result["predicted_units_next_week"] > result["stock_on_hand"]
    return result[[
        "product_id", "product_name", "category", "predicted_units_next_week",
        "sales_rank", "reorder_recommended",
    ]]


def _complete_daily_series(product_data: pd.DataFrame) -> pd.Series:
    """Fill missing calendar days with zero sales before forecasting."""
    indexed = product_data.set_index("date")["units_sold"].sort_index()
    return indexed.asfreq("D", fill_value=0.0)


def _predict_daily_units(history: np.ndarray, forecast_days: int, model: Any | None) -> np.ndarray:
    """Use the Transformer when compatible; otherwise apply a seasonal baseline."""
    if model is not None:
        try:
            import torch

            context = torch.tensor(history[-512:], dtype=torch.float32).unsqueeze(0)
            with torch.inference_mode():
                generated = model.generate(past_values=context)
            values = getattr(generated, "sequences", generated)
            values = np.asarray(values.detach().cpu() if hasattr(values, "detach") else values)
            values = values.reshape(-1, values.shape[-1]).mean(axis=0)
            if len(values) >= forecast_days and np.isfinite(values[:forecast_days]).all():
                return np.clip(values[:forecast_days], 0, None)
        except Exception:
            pass
    return _seasonal_naive_forecast(history, forecast_days)


def _seasonal_naive_forecast(history: np.ndarray, forecast_days: int) -> np.ndarray:
    """Fallback: repeat last week's daily pattern, or mean sales for short histories."""
    if history.size == 0:
        return np.zeros(forecast_days)
    if history.size >= 7:
        return np.resize(history[-7:], forecast_days)
    return np.repeat(float(np.mean(history)), forecast_days)


def _next_week_calendar_multiplier(last_date: pd.Timestamp, forecast_days: int) -> float:
    """Apply a 25% boost when the forecast window includes Ramadan or either Eid month."""
    try:
        from modules.calendar_utils import enrich_calendar_features

        future_dates = pd.DataFrame({"date": pd.date_range(last_date + pd.Timedelta(days=1), periods=forecast_days)})
        calendar = enrich_calendar_features(future_dates)
        return 1.25 if calendar[["is_ramadan", "is_eid"]].any(axis=None) else 1.0
    except Exception:
        return 1.0


def _empty_forecast() -> pd.DataFrame:
    """Return the expected schema for an upload with no usable sales rows."""
    return pd.DataFrame(columns=[
        "product_id", "product_name", "category", "predicted_units_next_week",
        "sales_rank", "reorder_recommended",
    ])


def naive_forecast(data: pd.DataFrame) -> pd.Series:
    """Retain the original chart helper for the initial Streamlit page."""
    numeric = data.select_dtypes(include="number")
    if numeric.empty:
        raise ValueError("The uploaded data needs at least one numeric column.")
    return numeric.iloc[:, 0].rolling(window=7, min_periods=1).mean()

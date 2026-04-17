"""Linear regression forecaster — used in Monthly Review Builder."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def forecast_trajectory(
    years: list[int],
    values: list[float],
    horizon: int = 3,
) -> dict:
    """
    Fit a linear model and project `horizon` years ahead.
    Returns: fitted, future_years, forecast, lower, upper, slope.
    """
    X = np.array(years).reshape(-1, 1)
    y = np.array(values)
    model = LinearRegression().fit(X, y)

    fitted = model.predict(X).tolist()
    residuals = y - np.array(fitted)
    std = float(np.std(residuals)) if len(residuals) > 1 else 5.0

    future_years = list(range(int(max(years)) + 1, int(max(years)) + horizon + 1))
    forecast = model.predict(np.array(future_years).reshape(-1, 1)).clip(0, 100).tolist()

    return {
        "fitted": fitted,
        "future_years": future_years,
        "forecast": forecast,
        "lower": [max(0.0, v - 1.96 * std) for v in forecast],
        "upper": [min(100.0, v + 1.96 * std) for v in forecast],
        "slope": float(model.coef_[0]),
    }


def school_trajectory(
    df: pd.DataFrame, school_code: str, subject: str
) -> dict | None:
    series = (
        df[(df["school_code"] == school_code) & (df["subject"] == subject)]
        .sort_values("year")[["year", "percentage"]]
        .dropna()
    )
    if len(series) < 2:
        return None
    return forecast_trajectory(series["year"].tolist(), series["percentage"].tolist())

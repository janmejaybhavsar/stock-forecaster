from datetime import timedelta

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src.models.base_model import ForecastModel


class ProphetModel(ForecastModel):
    """Seasonal forecaster using Holt-Winters Exponential Smoothing.
    Named 'prophet' in the registry for UI consistency.
    """
    name = "prophet"

    def __init__(self):
        self._model = None
        self._last_date = None
        self._fitted = None

    def fit(self, train_df: pd.DataFrame, target_col: str = "Close") -> None:
        series = train_df[target_col].values.astype(float)
        self._last_date = train_df.index[-1]

        self._model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add",
            seasonal_periods=5,
            initialization_method="estimated",
        )
        self._fitted = self._model.fit(optimized=True)

    def predict(self, horizon: int) -> pd.DataFrame:
        forecast = self._fitted.forecast(horizon)

        residuals = self._fitted.resid
        std = np.std(residuals)

        dates = pd.bdate_range(start=self._last_date + timedelta(days=1), periods=horizon)
        steps = np.arange(1, horizon + 1)

        return pd.DataFrame({
            "date": dates,
            "predicted_close": forecast,
            "lower_bound": forecast - 1.96 * std * np.sqrt(steps),
            "upper_bound": forecast + 1.96 * std * np.sqrt(steps),
        })

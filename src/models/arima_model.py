from datetime import timedelta

import pandas as pd
import pmdarima as pm

from src.models.base_model import ForecastModel


class ARIMAModel(ForecastModel):
    name = "arima"

    def __init__(self):
        self._model = None
        self._last_date = None

    def fit(self, train_df: pd.DataFrame, target_col: str = "Close") -> None:
        series = train_df[target_col].values
        self._last_date = train_df.index[-1]
        self._model = pm.auto_arima(
            series,
            start_p=1, start_q=1,
            max_p=5, max_q=5, max_d=2,
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            error_action="ignore",
        )

    def predict(self, horizon: int) -> pd.DataFrame:
        forecast, conf_int = self._model.predict(n_periods=horizon, return_conf_int=True)

        dates = pd.bdate_range(start=self._last_date + timedelta(days=1), periods=horizon)

        return pd.DataFrame({
            "date": dates,
            "predicted_close": forecast,
            "lower_bound": conf_int[:, 0],
            "upper_bound": conf_int[:, 1],
        })

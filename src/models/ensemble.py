import numpy as np
import pandas as pd

from src.models.base_model import ForecastModel


class EnsembleModel(ForecastModel):
    name = "ensemble"

    def __init__(self, model_names: list[str] | None = None):
        self._model_names = model_names or ["arima", "xgboost"]
        self._models: list[ForecastModel] = []
        self._weights: list[float] | None = None

    def fit(self, train_df: pd.DataFrame, target_col: str = "Close") -> None:
        from src.models.model_registry import get_model

        self._models = []
        for name in self._model_names:
            try:
                model = get_model(name)
                model.fit(train_df, target_col)
                self._models.append(model)
            except Exception:
                pass

        if not self._models:
            raise ValueError("No models could be fitted for ensemble")

        self._weights = [1.0 / len(self._models)] * len(self._models)

    def predict(self, horizon: int) -> pd.DataFrame:
        all_preds = []
        for model in self._models:
            try:
                pred = model.predict(horizon)
                all_preds.append(pred)
            except Exception:
                pass

        if not all_preds:
            raise ValueError("No models produced predictions")

        weights = self._weights[:len(all_preds)]
        weight_sum = sum(weights)
        weights = [w / weight_sum for w in weights]

        dates = all_preds[0]["date"]
        predicted = np.zeros(horizon)
        lower = np.zeros(horizon)
        upper = np.zeros(horizon)

        for pred_df, w in zip(all_preds, weights):
            predicted += w * pred_df["predicted_close"].values
            lower += w * pred_df["lower_bound"].values
            upper += w * pred_df["upper_bound"].values

        return pd.DataFrame({
            "date": dates,
            "predicted_close": predicted,
            "lower_bound": lower,
            "upper_bound": upper,
        })

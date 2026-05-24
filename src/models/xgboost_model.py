from datetime import timedelta

import pandas as pd
from xgboost import XGBRegressor

from src.models.base_model import ForecastModel


class XGBoostModel(ForecastModel):
    name = "xgboost"

    def __init__(self):
        self._model = None
        self._model_lower = None
        self._model_upper = None
        self._feature_cols: list[str] = []
        self._last_row = None
        self._last_date = None
        self._target_col = "Close"

    def fit(self, train_df: pd.DataFrame, target_col: str = "Close") -> None:
        self._target_col = target_col
        self._feature_cols = [c for c in train_df.columns if c not in ["Open", "High", "Low", "Close", "Volume"]]

        df = train_df.copy()
        df["target"] = df[target_col].shift(-1)
        df = df.dropna()

        X = df[self._feature_cols].values
        y = df["target"].values

        split = int(len(X) * 0.8)
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]

        self._model = XGBRegressor(
            n_estimators=500, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            early_stopping_rounds=20, verbosity=0,
        )
        self._model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        self._model_lower = XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            objective="reg:quantileerror", quantile_alpha=0.1, verbosity=0,
        )
        self._model_lower.fit(X_train, y_train)

        self._model_upper = XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            objective="reg:quantileerror", quantile_alpha=0.9, verbosity=0,
        )
        self._model_upper.fit(X_train, y_train)

        self._last_row = train_df.iloc[-1:].copy()
        self._last_date = train_df.index[-1]

    def predict(self, horizon: int) -> pd.DataFrame:
        predictions, lowers, uppers = [], [], []
        current_features = self._last_row[self._feature_cols].values

        for _ in range(horizon):
            pred = self._model.predict(current_features)[0]
            lower = self._model_lower.predict(current_features)[0]
            upper = self._model_upper.predict(current_features)[0]
            predictions.append(pred)
            lowers.append(lower)
            uppers.append(upper)

        dates = pd.bdate_range(start=self._last_date + timedelta(days=1), periods=horizon)

        return pd.DataFrame({
            "date": dates,
            "predicted_close": predictions,
            "lower_bound": lowers,
            "upper_bound": uppers,
        })

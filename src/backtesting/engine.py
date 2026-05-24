from typing import Callable

import numpy as np
import pandas as pd

from src.backtesting.metrics import directional_accuracy, mae, mape, rmse
from src.backtesting.report import BacktestResult
from src.models.base_model import ForecastModel


def walk_forward_backtest(
    model_cls: Callable[[], ForecastModel],
    data: pd.DataFrame,
    train_window: int = 252,
    test_window: int = 21,
    step_size: int = 21,
    target_col: str = "Close",
) -> BacktestResult:
    all_actuals = []
    all_predictions = []
    all_dates = []

    n = len(data)
    start = 0

    while start + train_window + test_window <= n:
        train_end = start + train_window
        test_end = min(train_end + test_window, n)

        train_data = data.iloc[start:train_end]
        test_data = data.iloc[train_end:test_end]

        model = model_cls()
        try:
            model.fit(train_data, target_col)
            pred_df = model.predict(len(test_data))

            actuals = test_data[target_col].values
            preds = pred_df["predicted_close"].values[:len(actuals)]

            for i, (idx, actual, pred) in enumerate(zip(test_data.index, actuals, preds)):
                all_dates.append(idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx))
                all_actuals.append(float(actual))
                all_predictions.append(float(pred))
        except Exception:
            pass

        start += step_size

    if not all_actuals:
        return BacktestResult(metrics={"error": "No predictions generated"})

    actuals_arr = np.array(all_actuals)
    preds_arr = np.array(all_predictions)

    metrics = {
        "mae": round(mae(actuals_arr, preds_arr), 4),
        "rmse": round(rmse(actuals_arr, preds_arr), 4),
        "mape": round(mape(actuals_arr, preds_arr), 2),
        "directional_accuracy": round(directional_accuracy(actuals_arr, preds_arr), 1),
    }

    predictions = [
        {"date": d, "actual": a, "predicted": p}
        for d, a, p in zip(all_dates, all_actuals, all_predictions)
    ]

    returns_actual = np.diff(actuals_arr) / actuals_arr[:-1]
    strategy_returns = np.where(np.diff(preds_arr) > 0, returns_actual, -returns_actual)

    cum_strategy = np.cumprod(1 + strategy_returns)
    cum_buyhold = np.cumprod(1 + returns_actual)

    equity_curve = []
    for i in range(len(cum_strategy)):
        equity_curve.append({
            "date": all_dates[i + 1],
            "strategy": round(float(cum_strategy[i]), 4),
            "buy_hold": round(float(cum_buyhold[i]), 4),
        })

    return BacktestResult(
        metrics=metrics,
        predictions=predictions,
        equity_curve=equity_curve,
    )

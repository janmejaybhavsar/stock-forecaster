import numpy as np


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    mask = actual != 0
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def directional_accuracy(actual: np.ndarray, predicted: np.ndarray) -> float:
    if len(actual) < 2:
        return 0.0
    actual_dir = np.diff(actual) > 0
    pred_dir = np.diff(predicted) > 0
    return float(np.mean(actual_dir == pred_dir) * 100)

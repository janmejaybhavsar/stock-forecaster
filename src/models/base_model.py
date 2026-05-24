from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class ForecastModel(ABC):
    name: str = "base"

    @abstractmethod
    def fit(self, train_df: pd.DataFrame, target_col: str = "Close") -> None: ...

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """Returns DataFrame with columns: date, predicted_close, lower_bound, upper_bound"""
        ...

    def save(self, path: Path) -> None:
        pass

    def load(self, path: Path) -> None:
        pass

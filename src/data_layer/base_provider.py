from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class DataProvider(ABC):
    """Abstract base for all stock data providers.

    All implementations return DataFrames with columns:
    Open, High, Low, Close, Volume (DatetimeIndex).
    """

    @abstractmethod
    def get_historical(
        self,
        ticker: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame: ...

    @abstractmethod
    def get_info(self, ticker: str) -> dict: ...

    @abstractmethod
    def search(self, query: str) -> list[dict]: ...

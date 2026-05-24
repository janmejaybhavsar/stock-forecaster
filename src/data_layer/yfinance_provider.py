from datetime import date

import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from src.data_layer.base_provider import DataProvider


class YFinanceProvider(DataProvider):

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_historical(
        self,
        ticker: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        df = yf.download(
            ticker,
            start=start.isoformat(),
            end=end.isoformat(),
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
        if df.empty:
            return df

        # yfinance may return MultiIndex columns for single ticker
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel("Ticker")

        df.index = pd.to_datetime(df.index)
        df.index.name = "Date"
        return df[["Open", "High", "Low", "Close", "Volume"]]

    def get_info(self, ticker: str) -> dict:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "ticker": ticker,
            "name": info.get("longName", info.get("shortName", ticker)),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", ""),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
        }

    def search(self, query: str) -> list[dict]:
        results = []
        try:
            t = yf.Ticker(query)
            info = t.info
            if info.get("longName") or info.get("shortName"):
                results.append({
                    "ticker": query.upper(),
                    "name": info.get("longName", info.get("shortName", query)),
                    "exchange": info.get("exchange", ""),
                })
        except Exception:
            pass
        return results

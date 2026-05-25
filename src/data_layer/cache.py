import sqlite3
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from config.settings import settings
from src.data_layer.base_provider import DataProvider

# ── In-memory cache for stock info with TTL ──────────────────────────
_INFO_CACHE_TTL = 300  # 5 minutes
_info_cache: dict[str, tuple[float, dict]] = {}
_info_cache_lock = threading.Lock()


def _get_cached_info(ticker: str) -> dict | None:
    """Return cached info if still valid, else None."""
    with _info_cache_lock:
        entry = _info_cache.get(ticker)
        if entry and (time.time() - entry[0]) < _INFO_CACHE_TTL:
            return entry[1]
    return None


def _set_cached_info(ticker: str, data: dict) -> None:
    """Store info in cache with current timestamp."""
    with _info_cache_lock:
        _info_cache[ticker] = (time.time(), data)


class CachedProvider(DataProvider):
    """Wraps a DataProvider with Parquet file caching and SQLite metadata."""

    def __init__(self, provider: DataProvider):
        self._provider = provider
        self._db_path = settings.cache_dir / "cache_meta.db"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    ticker TEXT,
                    interval TEXT,
                    last_fetched TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    row_count INTEGER,
                    PRIMARY KEY (ticker, interval)
                )
            """)

    def _parquet_path(self, ticker: str, interval: str) -> Path:
        return settings.cache_dir / f"{ticker.upper()}_{interval}.parquet"

    def _is_cache_valid(self, ticker: str, interval: str, start: date, end: date) -> bool:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT last_fetched, start_date, end_date FROM cache_entries WHERE ticker=? AND interval=?",
                (ticker.upper(), interval),
            ).fetchone()

        if not row:
            return False

        last_fetched = datetime.fromisoformat(row[0])
        cached_start = date.fromisoformat(row[1])
        cached_end = date.fromisoformat(row[2])

        max_age = timedelta(hours=24) if interval == "1d" else timedelta(hours=1)
        if datetime.now() - last_fetched > max_age:
            return False

        return cached_start <= start and cached_end >= end - timedelta(days=1)

    def get_historical(
        self,
        ticker: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        ticker_upper = ticker.upper()
        pq_path = self._parquet_path(ticker_upper, interval)

        if self._is_cache_valid(ticker_upper, interval, start, end) and pq_path.exists():
            df = pd.read_parquet(pq_path)
            df.index = pd.to_datetime(df.index)
            mask = (df.index.date >= start) & (df.index.date <= end)
            return df.loc[mask]

        df = self._provider.get_historical(ticker, start, end, interval)
        if df.empty:
            return df

        df.to_parquet(pq_path)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO cache_entries
                   (ticker, interval, last_fetched, start_date, end_date, row_count)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    ticker_upper,
                    interval,
                    datetime.now().isoformat(),
                    start.isoformat(),
                    end.isoformat(),
                    len(df),
                ),
            )
        return df

    def get_info(self, ticker: str) -> dict:
        ticker_upper = ticker.upper()
        cached = _get_cached_info(ticker_upper)
        if cached is not None:
            return cached
        info = self._provider.get_info(ticker)
        _set_cached_info(ticker_upper, info)
        return info

    def search(self, query: str) -> list[dict]:
        return self._provider.search(query)

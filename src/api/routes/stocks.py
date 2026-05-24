from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_data_provider
from src.api.schemas import SearchResult, StockInfo
from src.data_layer.base_provider import DataProvider

router = APIRouter(tags=["stocks"])


@router.get("/search", response_model=list[SearchResult])
def search_stocks(
    q: str = Query(..., min_length=1),
    provider: DataProvider = Depends(get_data_provider),
):
    return provider.search(q)


@router.get("/{ticker}/history")
def get_history(
    ticker: str,
    start: date = Query(default=None),
    end: date = Query(default=None),
    interval: str = Query(default="1d"),
    provider: DataProvider = Depends(get_data_provider),
):
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=730)

    df = provider.get_historical(ticker, start, end, interval)
    if df.empty:
        raise HTTPException(404, f"No data found for {ticker}")

    records = []
    for idx, row in df.iterrows():
        records.append({
            "date": idx.strftime("%Y-%m-%d"),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        })
    return records


@router.get("/{ticker}/info", response_model=StockInfo)
def get_stock_info(
    ticker: str,
    provider: DataProvider = Depends(get_data_provider),
):
    try:
        return provider.get_info(ticker)
    except Exception as e:
        raise HTTPException(404, str(e))

from pydantic import BaseModel


class StockInfo(BaseModel):
    ticker: str
    name: str
    sector: str = ""
    industry: str = ""
    market_cap: float = 0
    currency: str = "USD"
    exchange: str = ""
    fifty_two_week_high: float = 0
    fifty_two_week_low: float = 0
    current_price: float = 0
    previous_close: float = 0
    volume: int = 0


class SearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str = ""


class ForecastRequest(BaseModel):
    ticker: str
    model_name: str = "arima"
    horizon: int = 5
    include_sentiment: bool = False


class ForecastResponse(BaseModel):
    id: str
    status: str
    ticker: str = ""
    model_name: str = ""
    horizon: int = 0
    predictions: list[dict] | None = None
    error: str | None = None


class BacktestRequest(BaseModel):
    ticker: str
    model_name: str = "arima"
    train_window: int = 252
    test_window: int = 21
    step_size: int = 21


class BacktestResponse(BaseModel):
    id: str
    status: str
    ticker: str = ""
    model_name: str = ""
    metrics: dict | None = None
    predictions: list[dict] | None = None
    equity_curve: list[dict] | None = None
    error: str | None = None

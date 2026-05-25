from pydantic import BaseModel, Field, field_validator
import re


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
    ticker: str = Field(..., min_length=1, max_length=20)
    model_name: str = Field("arima", pattern=r"^(arima|xgboost|lstm|transformer|prophet|ensemble)$")
    horizon: int = Field(5, ge=1, le=30)
    include_sentiment: bool = False

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.upper().strip()
        if not re.match(r"^[A-Z0-9\.\-\^]+$", v):
            raise ValueError("Ticker must contain only letters, numbers, dots, hyphens, or ^")
        return v


class ForecastResponse(BaseModel):
    id: str
    status: str
    ticker: str = ""
    model_name: str = ""
    horizon: int = 0
    predictions: list[dict] | None = None
    error: str | None = None


class BacktestRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    model_name: str = Field("arima", pattern=r"^(arima|xgboost|lstm|transformer|prophet|ensemble)$")
    train_window: int = Field(252, ge=60, le=1000)
    test_window: int = Field(21, ge=5, le=252)
    step_size: int = Field(21, ge=1, le=252)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.upper().strip()
        if not re.match(r"^[A-Z0-9\.\-\^]+$", v):
            raise ValueError("Ticker must contain only letters, numbers, dots, hyphens, or ^")
        return v


class BacktestResponse(BaseModel):
    id: str
    status: str
    ticker: str = ""
    model_name: str = ""
    metrics: dict | None = None
    predictions: list[dict] | None = None
    equity_curve: list[dict] | None = None
    error: str | None = None

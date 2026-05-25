import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.schemas import ForecastRequest, ForecastResponse
from src.auth.ticker_validator import sanitize_ticker
from src.database.repositories import ForecastHistoryRepository

_limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["forecasts"])
logger = logging.getLogger(__name__)

_repo = ForecastHistoryRepository()
_ALLOWED_COMPARE_MODELS = {"arima", "xgboost", "lstm", "transformer", "prophet", "ensemble"}


def _run_forecast(forecast_id: str, req: ForecastRequest) -> None:
    try:
        from datetime import date, timedelta

        from src.data_layer.provider_factory import get_provider
        from src.features.pipeline import FeaturePipeline
        from src.models.model_registry import get_model

        provider = get_provider()
        end = date.today()
        start = end - timedelta(days=730)
        df = provider.get_historical(req.ticker, start, end)

        pipeline = FeaturePipeline()
        features_df = pipeline.build(req.ticker, df, include_sentiment=req.include_sentiment)

        model = get_model(req.model_name)
        model.fit(features_df, target_col="Close")
        predictions = model.predict(req.horizon)

        pred_records = []
        for _, row in predictions.iterrows():
            pred_records.append({
                "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
                "predicted_close": round(row["predicted_close"], 2),
                "lower_bound": round(row["lower_bound"], 2),
                "upper_bound": round(row["upper_bound"], 2),
            })

        _repo.update_result(forecast_id, predictions=pred_records, status="completed")
    except Exception as e:
        logger.error(f"Forecast {forecast_id} failed: {e}")
        _repo.update_result(forecast_id, predictions=[], status="failed", error=str(e))


@router.post("/run", response_model=ForecastResponse)
@_limiter.limit("10/minute")
def run_forecast(request: Request, req: ForecastRequest, bg: BackgroundTasks):
    try:
        normalized_ticker = sanitize_ticker(req.ticker)
    except ValueError as e:
        raise HTTPException(400, str(e))
    record = _repo.create(
        ticker=normalized_ticker,
        model_name=req.model_name,
        horizon=req.horizon,
    )
    bg.add_task(_run_forecast, record["id"], req)
    return ForecastResponse(
        id=record["id"],
        status="running",
        ticker=req.ticker,
        model_name=req.model_name,
        horizon=req.horizon,
    )


@router.get("/{forecast_id}", response_model=ForecastResponse)
def get_forecast(forecast_id: str):
    record = _repo.get_by_id(forecast_id)
    if not record:
        raise HTTPException(404, "Forecast not found")
    return ForecastResponse(
        id=record["id"],
        status=record["status"],
        ticker=record["ticker"],
        model_name=record["model_name"],
        horizon=record["horizon"],
        predictions=record.get("predictions", []),
        error=record.get("error"),
    )


# ── Parallel model comparison ────────────────────────────────────────


class CompareRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    models: list[str] = Field(..., min_length=2, max_length=6)
    horizon: int = Field(5, ge=1, le=30)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.upper().strip()
        if not re.match(r"^[A-Z0-9\.\-\^]+$", v):
            raise ValueError("Ticker must contain only letters, numbers, dots, hyphens, or ^")
        return v

    @field_validator("models")
    @classmethod
    def validate_models(cls, values: list[str]) -> list[str]:
        normalized = [m.lower().strip() for m in values]
        if any(m not in _ALLOWED_COMPARE_MODELS for m in normalized):
            raise ValueError(f"Models must be one of: {sorted(_ALLOWED_COMPARE_MODELS)}")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Models must be unique")
        return normalized


def _run_single_model(ticker: str, model_name: str, horizon: int, df) -> dict:
    """Run a single model forecast synchronously — called in a thread pool."""
    try:
        from src.features.pipeline import FeaturePipeline
        from src.models.model_registry import get_model

        pipeline = FeaturePipeline()
        features_df = pipeline.build(ticker, df, include_sentiment=False)

        model = get_model(model_name)
        model.fit(features_df, target_col="Close")
        predictions = model.predict(horizon)

        pred_records = []
        for _, row in predictions.iterrows():
            pred_records.append({
                "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
                "predicted_close": round(row["predicted_close"], 2),
                "lower_bound": round(row["lower_bound"], 2),
                "upper_bound": round(row["upper_bound"], 2),
            })

        return {"model": model_name, "status": "completed", "predictions": pred_records}
    except Exception as e:
        logger.error(f"Compare model {model_name} for {ticker} failed: {e}")
        return {"model": model_name, "status": "failed", "predictions": [], "error": str(e)}


@router.post("/compare")
@_limiter.limit("3/minute")
def compare_models(request: Request, req: CompareRequest):
    """Run multiple models in parallel and return all results at once."""
    try:
        normalized_ticker = sanitize_ticker(req.ticker)
    except ValueError as e:
        raise HTTPException(400, str(e))
    results = {}
    provider = get_provider()
    end = date.today()
    start = end - timedelta(days=730)
    df = provider.get_historical(req.ticker, start, end)

    with ThreadPoolExecutor(max_workers=min(len(req.models), 4)) as executor:
        futures = {
            executor.submit(_run_single_model, normalized_ticker, m, req.horizon): m
            for m in req.models
        }
        for future in as_completed(futures):
            model_name = futures[future]
            results[model_name] = future.result()

    return {
        "ticker": normalized_ticker,
        "horizon": req.horizon,
        "results": results,
    }

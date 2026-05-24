import uuid

from fastapi import APIRouter, BackgroundTasks

from src.api.schemas import ForecastRequest, ForecastResponse

router = APIRouter(tags=["forecasts"])

_store: dict[str, ForecastResponse] = {}


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

        _store[forecast_id].predictions = pred_records
        _store[forecast_id].status = "completed"
    except Exception as e:
        _store[forecast_id].status = "failed"
        _store[forecast_id].error = str(e)


@router.post("/run", response_model=ForecastResponse)
def run_forecast(req: ForecastRequest, bg: BackgroundTasks):
    forecast_id = str(uuid.uuid4())[:8]
    _store[forecast_id] = ForecastResponse(
        id=forecast_id,
        status="running",
        ticker=req.ticker,
        model_name=req.model_name,
        horizon=req.horizon,
    )
    bg.add_task(_run_forecast, forecast_id, req)
    return _store[forecast_id]


@router.get("/{forecast_id}", response_model=ForecastResponse)
def get_forecast(forecast_id: str):
    if forecast_id not in _store:
        from fastapi import HTTPException
        raise HTTPException(404, "Forecast not found")
    return _store[forecast_id]

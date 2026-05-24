import uuid

from fastapi import APIRouter, BackgroundTasks

from src.api.schemas import BacktestRequest, BacktestResponse

router = APIRouter(tags=["backtests"])

_store: dict[str, BacktestResponse] = {}


def _run_backtest(backtest_id: str, req: BacktestRequest) -> None:
    try:
        from datetime import date, timedelta

        from src.backtesting.engine import walk_forward_backtest
        from src.data_layer.provider_factory import get_provider
        from src.features.pipeline import FeaturePipeline
        from src.models.model_registry import get_model

        provider = get_provider()
        end = date.today()
        start = end - timedelta(days=req.train_window * 2 + req.test_window * 10 + 500)
        df = provider.get_historical(req.ticker, start, end)

        pipeline = FeaturePipeline()
        features_df = pipeline.build(req.ticker, df, include_sentiment=False)

        result = walk_forward_backtest(
            model_cls=lambda: get_model(req.model_name),
            data=features_df,
            train_window=req.train_window,
            test_window=req.test_window,
            step_size=req.step_size,
        )

        _store[backtest_id].metrics = result.metrics
        _store[backtest_id].predictions = result.predictions
        _store[backtest_id].equity_curve = result.equity_curve
        _store[backtest_id].status = "completed"
    except Exception as e:
        _store[backtest_id].status = "failed"
        _store[backtest_id].error = str(e)


@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest, bg: BackgroundTasks):
    backtest_id = str(uuid.uuid4())[:8]
    _store[backtest_id] = BacktestResponse(
        id=backtest_id,
        status="running",
        ticker=req.ticker,
        model_name=req.model_name,
    )
    bg.add_task(_run_backtest, backtest_id, req)
    return _store[backtest_id]


@router.get("/{backtest_id}", response_model=BacktestResponse)
def get_backtest(backtest_id: str):
    if backtest_id not in _store:
        from fastapi import HTTPException
        raise HTTPException(404, "Backtest not found")
    return _store[backtest_id]

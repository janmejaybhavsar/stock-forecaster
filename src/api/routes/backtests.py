import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.schemas import BacktestRequest, BacktestResponse
from src.database.repositories import BacktestHistoryRepository

_limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["backtests"])
logger = logging.getLogger(__name__)

_repo = BacktestHistoryRepository()


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

        _repo.update_result(
            backtest_id,
            metrics=result.metrics,
            predictions=result.predictions,
            equity_curve=result.equity_curve,
            status="completed",
        )
    except Exception as e:
        logger.error(f"Backtest {backtest_id} failed: {e}")
        _repo.update_result(
            backtest_id,
            metrics={},
            predictions=[],
            equity_curve=[],
            status="failed",
            error=str(e),
        )


@router.post("/run", response_model=BacktestResponse)
@_limiter.limit("5/minute")
def run_backtest(request: Request, req: BacktestRequest, bg: BackgroundTasks):
    record = _repo.create(
        ticker=req.ticker.upper().strip(),
        model_name=req.model_name,
    )
    bg.add_task(_run_backtest, record["id"], req)
    return BacktestResponse(
        id=record["id"],
        status="running",
        ticker=req.ticker,
        model_name=req.model_name,
    )


@router.get("/{backtest_id}", response_model=BacktestResponse)
def get_backtest(backtest_id: str):
    record = _repo.get_by_id(backtest_id)
    if not record:
        raise HTTPException(404, "Backtest not found")
    return BacktestResponse(
        id=record["id"],
        status=record["status"],
        ticker=record["ticker"],
        model_name=record["model_name"],
        metrics=record.get("metrics", {}),
        predictions=record.get("predictions", []),
        equity_curve=record.get("equity_curve", []),
        error=record.get("error"),
    )

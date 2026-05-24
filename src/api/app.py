import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, backtests, coach, forecasts, models, portfolio, signals, stocks, watchlists
from src.database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stock Forecaster API",
        version="2.0.0",
        description="Portfolio Growth Coach — ML forecasting with signals, coaching, and portfolio tracking",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(stocks.router, prefix="/api/v1/stocks")
    app.include_router(forecasts.router, prefix="/api/v1/forecasts")
    app.include_router(backtests.router, prefix="/api/v1/backtests")
    app.include_router(models.router, prefix="/api/v1/models")
    app.include_router(watchlists.router, prefix="/api/v1/watchlists")
    app.include_router(portfolio.router, prefix="/api/v1/portfolio")
    app.include_router(signals.router, prefix="/api/v1/signals")
    app.include_router(coach.router, prefix="/api/v1/coach")

    @app.get("/")
    def root():
        return {"message": "Stock Forecaster API", "docs": "/docs"}

    @app.get("/health")
    def health():
        """Health check endpoint for monitoring and container orchestration."""
        import time
        from src.database.connection import get_db

        # Check database
        try:
            get_db().execute("SELECT 1").fetchone()
            db_ok = True
        except Exception:
            db_ok = False

        return {
            "status": "healthy" if db_ok else "degraded",
            "database": "ok" if db_ok else "error",
            "timestamp": time.time(),
            "version": app.version,
        }

    return app

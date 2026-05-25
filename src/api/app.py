import os
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.routes import auth, backtests, coach, forecasts, models, portfolio, settings, signals, stocks, watchlists
from src.database.connection import init_db

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# CORS origins: configurable via CORS_ORIGINS env var (comma-separated) for production
_DEFAULT_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",
]


def _get_cors_origins() -> list[str]:
    """Get allowed origins from CORS_ORIGINS env var / settings, or use defaults for development."""
    env_origins = os.environ.get("CORS_ORIGINS", "")
    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]
    from config.settings import get_settings
    settings = get_settings()
    if settings.cors_origins:
        return [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    return _DEFAULT_ORIGINS


def _build_cors_config() -> tuple[list[str], str | None]:
    origins = _get_cors_origins()
    explicit_origins: list[str] = []
    wildcard_patterns: list[str] = []
    for origin in origins:
        if "*" in origin:
            wildcard_patterns.append(re.escape(origin).replace(r"\*", ".*"))
        else:
            explicit_origins.append(origin)
    origin_regex = "|".join(f"^{pattern}$" for pattern in wildcard_patterns) if wildcard_patterns else None
    return explicit_origins, origin_regex


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    cors_origins, cors_origin_regex = _build_cors_config()
    app = FastAPI(
        title="Stock Forecaster API",
        version="2.0.0",
        description="Portfolio Growth Coach — ML forecasting with signals, coaching, and portfolio tracking",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=cors_origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
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
    app.include_router(settings.router, prefix="/api/v1/user")

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

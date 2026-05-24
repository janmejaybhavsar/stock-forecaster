from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_current_user, get_optional_user

router = APIRouter(tags=["signals"])


@router.get("/{ticker}")
def get_signal(
    ticker: str,
    horizon: int = Query(5, ge=1, le=30),
    include_sentiment: bool = Query(False),
    user: dict | None = Depends(get_optional_user),
):
    """Get composite buy/sell/hold signal for a ticker."""
    from src.signals.engine import generate_signal

    result = generate_signal(
        ticker=ticker.upper().strip(),
        horizon=horizon,
        include_sentiment=include_sentiment,
    )
    return asdict(result)


@router.get("/portfolio/all")
def get_portfolio_signals(
    horizon: int = Query(5, ge=1, le=30),
    include_sentiment: bool = Query(False),
    user: dict = Depends(get_current_user),
):
    """Get signals for all holdings in the user's portfolio."""
    from dataclasses import asdict

    from src.database.repositories import HoldingsRepository
    from src.signals.engine import generate_portfolio_signals

    repo = HoldingsRepository()
    holdings = repo.list_by_user(user["id"])

    if not holdings:
        return {"signals": [], "message": "No holdings in portfolio"}

    results = generate_portfolio_signals(
        holdings=[{"ticker": h["ticker"]} for h in holdings],
        horizon=horizon,
        include_sentiment=include_sentiment,
    )

    return {
        "signals": [asdict(r) for r in results],
        "total_holdings": len(holdings),
    }


@router.get("/portfolio/notifications")
def get_portfolio_notifications(
    user: dict = Depends(get_current_user),
):
    """Get smart notifications for the user's portfolio."""
    from dataclasses import asdict

    from src.api.routes.portfolio import _enrich_holdings
    from src.database.repositories import HoldingsRepository
    from src.signals.notifications import generate_notifications

    repo = HoldingsRepository()
    holdings = repo.list_by_user(user["id"])

    if not holdings:
        return {"notifications": [], "message": "No holdings in portfolio"}

    enriched, summary = _enrich_holdings(holdings)

    notifications = generate_notifications(enriched, summary)

    return {
        "notifications": [asdict(n) for n in notifications],
        "count": len(notifications),
    }

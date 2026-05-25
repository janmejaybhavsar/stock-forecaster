import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import get_current_user, get_data_provider
from src.database.repositories import HoldingsRepository

router = APIRouter(tags=["portfolio"])
logger = logging.getLogger(__name__)
_repo = HoldingsRepository()


class HoldingCreate(BaseModel):
    ticker: str
    shares: float
    avg_cost: float


class HoldingUpdate(BaseModel):
    shares: float | None = None
    avg_cost: float | None = None


@router.post("/holdings")
def add_holding(req: HoldingCreate, user: dict = Depends(get_current_user)):
    return _repo.add(user["id"], req.ticker, req.shares, req.avg_cost)


def _fetch_single_info(provider, ticker: str) -> tuple[str, dict]:
    """Fetch info for a single ticker — called in parallel."""
    try:
        info = provider.get_info(ticker)
        return ticker, {"current_price": info.get("current_price", 0), "currency": info.get("currency", "USD")}
    except Exception as e:
        logger.warning(f"Failed to fetch info for {ticker}: {e}")
        return ticker, {"current_price": 0, "currency": "USD"}


def _enrich_holdings(holdings: list[dict]) -> tuple[list[dict], dict]:
    """Enrich holdings with live prices using parallel fetches, then compute summary."""
    provider = get_data_provider()

    # Fetch all ticker info in parallel (up to 8 concurrent)
    tickers = list({h["ticker"] for h in holdings})
    info_map: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=min(len(tickers), 8)) as executor:
        futures = {executor.submit(_fetch_single_info, provider, t): t for t in tickers}
        for future in as_completed(futures):
            ticker, info = future.result()
            info_map[ticker] = info

    total_value = 0.0
    total_cost = 0.0
    enriched = []

    for h in holdings:
        info = info_map.get(h["ticker"], {"current_price": 0, "currency": "USD"})
        current_price = info["current_price"]
        currency = info["currency"]

        market_value = current_price * h["shares"]
        cost_basis = h["avg_cost"] * h["shares"]
        pnl = market_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis else 0

        total_value += market_value
        total_cost += cost_basis

        enriched.append({
            **h,
            "current_price": current_price,
            "currency": currency,
            "market_value": round(market_value, 2),
            "cost_basis": round(cost_basis, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
        })

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0

    summary = {
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "holdings_count": len(enriched),
    }

    return enriched, summary


@router.get("/")
def get_portfolio(user: dict = Depends(get_current_user)):
    holdings = _repo.list_by_user(user["id"])
    enriched, summary = _enrich_holdings(holdings)
    return {"holdings": enriched, "summary": summary}


@router.put("/holdings/{holding_id}")
def update_holding(holding_id: str, req: HoldingUpdate, user: dict = Depends(get_current_user)):
    h = _repo.get_by_id(holding_id)
    if not h or h["user_id"] != user["id"]:
        raise HTTPException(404, "Holding not found")
    return _repo.update(holding_id, shares=req.shares, avg_cost=req.avg_cost)


@router.delete("/holdings/{holding_id}")
def delete_holding(holding_id: str, user: dict = Depends(get_current_user)):
    h = _repo.get_by_id(holding_id)
    if not h or h["user_id"] != user["id"]:
        raise HTTPException(404, "Holding not found")
    _repo.delete(holding_id)
    return {"status": "deleted"}

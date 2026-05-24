from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.database.repositories import WatchlistRepository

router = APIRouter(tags=["watchlists"])
_repo = WatchlistRepository()


class WatchlistCreate(BaseModel):
    name: str
    tickers: list[str] = []


class WatchlistUpdate(BaseModel):
    name: str | None = None
    tickers: list[str] | None = None


@router.post("/")
def create_watchlist(req: WatchlistCreate, user: dict = Depends(get_current_user)):
    return _repo.create(user["id"], req.name, req.tickers)


@router.get("/")
def list_watchlists(user: dict = Depends(get_current_user)):
    return _repo.list_by_user(user["id"])


@router.put("/{wl_id}")
def update_watchlist(wl_id: str, req: WatchlistUpdate, user: dict = Depends(get_current_user)):
    wl = _repo.get_by_id(wl_id)
    if not wl or wl["user_id"] != user["id"]:
        raise HTTPException(404, "Watchlist not found")
    return _repo.update(wl_id, name=req.name, tickers=req.tickers)


@router.delete("/{wl_id}")
def delete_watchlist(wl_id: str, user: dict = Depends(get_current_user)):
    wl = _repo.get_by_id(wl_id)
    if not wl or wl["user_id"] != user["id"]:
        raise HTTPException(404, "Watchlist not found")
    _repo.delete(wl_id)
    return {"status": "deleted"}

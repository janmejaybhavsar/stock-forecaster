import json
import uuid
from datetime import datetime

from src.database.connection import get_db


def _new_id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserRepository:
    def create(self, email: str, username: str, password_hash: str) -> dict:
        db = get_db()
        user_id = _new_id()
        db.execute(
            "INSERT INTO users (id, email, username, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, username, password_hash, _now()),
        )
        db.commit()
        return self.get_by_id(user_id)

    def get_by_email(self, email: str) -> dict | None:
        row = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None

    def get_by_id(self, user_id: str) -> dict | None:
        row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def get_by_username(self, username: str) -> dict | None:
        row = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Watchlists
# ---------------------------------------------------------------------------

class WatchlistRepository:
    def create(self, user_id: str, name: str, tickers: list[str]) -> dict:
        db = get_db()
        wl_id = _new_id()
        db.execute(
            "INSERT INTO watchlists (id, user_id, name, tickers, created_at) VALUES (?, ?, ?, ?, ?)",
            (wl_id, user_id, name, json.dumps(tickers), _now()),
        )
        db.commit()
        return self.get_by_id(wl_id)

    def list_by_user(self, user_id: str) -> list[dict]:
        rows = get_db().execute(
            "SELECT * FROM watchlists WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [_parse_watchlist(r) for r in rows]

    def get_by_id(self, wl_id: str) -> dict | None:
        row = get_db().execute("SELECT * FROM watchlists WHERE id = ?", (wl_id,)).fetchone()
        return _parse_watchlist(row) if row else None

    def update(self, wl_id: str, name: str | None = None, tickers: list[str] | None = None) -> dict:
        db = get_db()
        if name is not None:
            db.execute("UPDATE watchlists SET name = ? WHERE id = ?", (name, wl_id))
        if tickers is not None:
            db.execute("UPDATE watchlists SET tickers = ? WHERE id = ?", (json.dumps(tickers), wl_id))
        db.commit()
        return self.get_by_id(wl_id)

    def delete(self, wl_id: str) -> None:
        get_db().execute("DELETE FROM watchlists WHERE id = ?", (wl_id,))
        get_db().commit()


def _parse_watchlist(row) -> dict:
    d = dict(row)
    d["tickers"] = json.loads(d["tickers"])
    return d


# ---------------------------------------------------------------------------
# Forecast History
# ---------------------------------------------------------------------------

class ForecastHistoryRepository:
    def create(self, ticker: str, model_name: str, horizon: int, user_id: str | None = None) -> dict:
        db = get_db()
        fid = _new_id()
        db.execute(
            "INSERT INTO forecast_history (id, user_id, ticker, model_name, horizon, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (fid, user_id, ticker, model_name, horizon, _now()),
        )
        db.commit()
        return {"id": fid, "status": "running", "ticker": ticker, "model_name": model_name}

    def update_result(self, fid: str, predictions: list, status: str = "completed", error: str | None = None):
        db = get_db()
        db.execute(
            "UPDATE forecast_history SET predictions = ?, status = ?, error = ? WHERE id = ?",
            (json.dumps(predictions), status, error, fid),
        )
        db.commit()

    def get_by_id(self, fid: str) -> dict | None:
        row = get_db().execute("SELECT * FROM forecast_history WHERE id = ?", (fid,)).fetchone()
        return _parse_forecast(row) if row else None

    def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        rows = get_db().execute(
            "SELECT * FROM forecast_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [_parse_forecast(r) for r in rows]


def _parse_forecast(row) -> dict:
    d = dict(row)
    d["predictions"] = json.loads(d["predictions"]) if d["predictions"] else []
    return d


# ---------------------------------------------------------------------------
# Backtest History
# ---------------------------------------------------------------------------

class BacktestHistoryRepository:
    def create(self, ticker: str, model_name: str, user_id: str | None = None) -> dict:
        db = get_db()
        bid = _new_id()
        db.execute(
            "INSERT INTO backtest_history (id, user_id, ticker, model_name, created_at) VALUES (?, ?, ?, ?, ?)",
            (bid, user_id, ticker, model_name, _now()),
        )
        db.commit()
        return {"id": bid, "status": "running", "ticker": ticker, "model_name": model_name}

    def update_result(self, bid: str, metrics: dict, predictions: list, equity_curve: list,
                      status: str = "completed", error: str | None = None):
        db = get_db()
        db.execute(
            "UPDATE backtest_history SET metrics=?, predictions=?, equity_curve=?, status=?, error=? WHERE id=?",
            (json.dumps(metrics), json.dumps(predictions), json.dumps(equity_curve), status, error, bid),
        )
        db.commit()

    def get_by_id(self, bid: str) -> dict | None:
        row = get_db().execute("SELECT * FROM backtest_history WHERE id = ?", (bid,)).fetchone()
        return _parse_backtest(row) if row else None

    def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        rows = get_db().execute(
            "SELECT * FROM backtest_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [_parse_backtest(r) for r in rows]


def _parse_backtest(row) -> dict:
    d = dict(row)
    d["metrics"] = json.loads(d["metrics"]) if d["metrics"] else {}
    d["predictions"] = json.loads(d["predictions"]) if d["predictions"] else []
    d["equity_curve"] = json.loads(d["equity_curve"]) if d["equity_curve"] else []
    return d


# ---------------------------------------------------------------------------
# Holdings (Portfolio)
# ---------------------------------------------------------------------------

class HoldingsRepository:
    def add(self, user_id: str, ticker: str, shares: float, avg_cost: float) -> dict:
        db = get_db()
        hid = _new_id()
        db.execute(
            "INSERT INTO holdings (id, user_id, ticker, shares, avg_cost, added_at) VALUES (?, ?, ?, ?, ?, ?)",
            (hid, user_id, ticker.upper(), shares, avg_cost, _now()),
        )
        db.commit()
        return self.get_by_id(hid)

    def list_by_user(self, user_id: str) -> list[dict]:
        rows = get_db().execute(
            "SELECT * FROM holdings WHERE user_id = ? ORDER BY added_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, hid: str) -> dict | None:
        row = get_db().execute("SELECT * FROM holdings WHERE id = ?", (hid,)).fetchone()
        return dict(row) if row else None

    def update(self, hid: str, shares: float | None = None, avg_cost: float | None = None) -> dict:
        db = get_db()
        if shares is not None:
            db.execute("UPDATE holdings SET shares = ? WHERE id = ?", (shares, hid))
        if avg_cost is not None:
            db.execute("UPDATE holdings SET avg_cost = ? WHERE id = ?", (avg_cost, hid))
        db.commit()
        return self.get_by_id(hid)

    def delete(self, hid: str) -> None:
        get_db().execute("DELETE FROM holdings WHERE id = ?", (hid,))
        get_db().commit()


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class AlertRepository:
    def create(self, user_id: str, ticker: str, condition: str, target_price: float) -> dict:
        db = get_db()
        aid = _new_id()
        db.execute(
            "INSERT INTO alerts (id, user_id, ticker, condition, target_price, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (aid, user_id, ticker.upper(), condition, target_price, _now()),
        )
        db.commit()
        return self.get_by_id(aid)

    def list_by_user(self, user_id: str, active_only: bool = True) -> list[dict]:
        q = "SELECT * FROM alerts WHERE user_id = ?"
        if active_only:
            q += " AND triggered = 0"
        q += " ORDER BY created_at DESC"
        return [dict(r) for r in get_db().execute(q, (user_id,)).fetchall()]

    def get_by_id(self, aid: str) -> dict | None:
        row = get_db().execute("SELECT * FROM alerts WHERE id = ?", (aid,)).fetchone()
        return dict(row) if row else None

    def mark_triggered(self, aid: str) -> None:
        get_db().execute("UPDATE alerts SET triggered = 1 WHERE id = ?", (aid,))
        get_db().commit()

    def delete(self, aid: str) -> None:
        get_db().execute("DELETE FROM alerts WHERE id = ?", (aid,))
        get_db().commit()


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationRepository:
    def create(self, user_id: str, ntype: str, message: str, ticker: str | None = None) -> dict:
        db = get_db()
        nid = _new_id()
        db.execute(
            "INSERT INTO notifications (id, user_id, type, message, ticker, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (nid, user_id, ntype, message, ticker, _now()),
        )
        db.commit()
        return {"id": nid, "type": ntype, "message": message, "ticker": ticker, "read": 0}

    def list_by_user(self, user_id: str, unread_only: bool = False, limit: int = 50) -> list[dict]:
        q = "SELECT * FROM notifications WHERE user_id = ?"
        if unread_only:
            q += " AND read = 0"
        q += " ORDER BY created_at DESC LIMIT ?"
        return [dict(r) for r in get_db().execute(q, (user_id, limit)).fetchall()]

    def mark_read(self, nid: str) -> None:
        get_db().execute("UPDATE notifications SET read = 1 WHERE id = ?", (nid,))
        get_db().commit()

    def mark_all_read(self, user_id: str) -> None:
        get_db().execute("UPDATE notifications SET read = 1 WHERE user_id = ?", (user_id,))
        get_db().commit()


# ---------------------------------------------------------------------------
# Learning Progress
# ---------------------------------------------------------------------------

class LearningProgressRepository:
    def complete_step(self, user_id: str, module_id: str, step_id: str) -> None:
        db = get_db()
        pid = _new_id()
        db.execute(
            "INSERT OR IGNORE INTO learning_progress (id, user_id, module_id, step_id, completed_at) VALUES (?, ?, ?, ?, ?)",
            (pid, user_id, module_id, step_id, _now()),
        )
        db.commit()

    def get_progress(self, user_id: str) -> list[dict]:
        rows = get_db().execute(
            "SELECT module_id, step_id, completed_at FROM learning_progress WHERE user_id = ? ORDER BY completed_at",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

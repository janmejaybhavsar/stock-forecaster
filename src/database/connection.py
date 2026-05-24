import sqlite3
import threading
from pathlib import Path

from config.settings import get_settings

_lock = threading.Lock()
_connection: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS watchlists (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    tickers TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS forecast_history (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    ticker TEXT NOT NULL,
    model_name TEXT NOT NULL,
    horizon INTEGER NOT NULL,
    predictions TEXT DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'running',
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS backtest_history (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    ticker TEXT NOT NULL,
    model_name TEXT NOT NULL,
    metrics TEXT DEFAULT '{}',
    predictions TEXT DEFAULT '[]',
    equity_curve TEXT DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'running',
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS holdings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    ticker TEXT NOT NULL,
    shares REAL NOT NULL,
    avg_cost REAL NOT NULL,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    ticker TEXT NOT NULL,
    condition TEXT NOT NULL,
    target_price REAL NOT NULL,
    triggered INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS learning_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    module_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, module_id, step_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    ticker TEXT,
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db() -> sqlite3.Connection:
    global _connection
    with _lock:
        if _connection is None:
            settings = get_settings()
            db_path = settings.data_dir / "stock_forecaster.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            _connection = sqlite3.connect(str(db_path), check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.execute("PRAGMA journal_mode=WAL")
            _connection.execute("PRAGMA foreign_keys=ON")
        return _connection


def init_db() -> None:
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()

"""
Audit logging for security-relevant events.
Logs to both Python logger and a dedicated SQLite table.
"""

import logging
from datetime import datetime

from src.database.connection import get_db

logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)


def _ensure_table():
    """Create audit_log table if not exists."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            event_type TEXT NOT NULL,
            user_id TEXT,
            email TEXT,
            ip_address TEXT,
            detail TEXT,
            success INTEGER NOT NULL DEFAULT 1
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id, timestamp DESC)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_event ON audit_log(event_type, timestamp DESC)")
    db.commit()


def log_event(
    event_type: str,
    user_id: str | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    detail: str | None = None,
    success: bool = True,
) -> None:
    """Log a security event to the audit table and Python logger."""
    try:
        _ensure_table()
        db = get_db()
        db.execute(
            """INSERT INTO audit_log (timestamp, event_type, user_id, email, ip_address, detail, success)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().isoformat(),
                event_type,
                user_id,
                email,
                ip_address,
                detail,
                1 if success else 0,
            ),
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to write audit log: {e}")

    # Always log to Python logger
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        f"[{status}] {event_type} | user={user_id or email or 'anonymous'} | ip={ip_address} | {detail or ''}"
    )

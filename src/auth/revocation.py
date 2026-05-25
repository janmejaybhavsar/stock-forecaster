from datetime import UTC, datetime

_revoked_tokens: dict[str, datetime] = {}


def _parse_expiry(exp: int | float | str | datetime | None) -> datetime | None:
    if exp is None:
        return None
    if isinstance(exp, datetime):
        return exp if exp.tzinfo else exp.replace(tzinfo=UTC)
    if isinstance(exp, (int, float)):
        return datetime.fromtimestamp(exp, tz=UTC)
    if isinstance(exp, str):
        try:
            return datetime.fromtimestamp(float(exp), tz=UTC)
        except ValueError:
            return None
    return None


def _prune_expired() -> None:
    now = datetime.now(tz=UTC)
    expired = [jti for jti, exp in _revoked_tokens.items() if exp <= now]
    for jti in expired:
        _revoked_tokens.pop(jti, None)


def is_token_revoked(jti: str) -> bool:
    _prune_expired()
    return jti in _revoked_tokens


def revoke_token(jti: str, exp: int | float | str | datetime | None = None) -> None:
    expiry = _parse_expiry(exp)
    if expiry is None:
        return
    _prune_expired()
    _revoked_tokens[jti] = expiry

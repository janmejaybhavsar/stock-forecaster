from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.auth.revocation import is_token_revoked
from src.auth.security import decode_token
from src.data_layer.base_provider import DataProvider
from src.data_layer.provider_factory import get_provider
from src.database.repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_user_repo = UserRepository()


def get_data_provider() -> DataProvider:
    return get_provider()


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    # Check if token has been revoked
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has been revoked")

    user = _user_repo.get_by_id(payload.get("sub", ""))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def get_optional_user(token: str = Depends(oauth2_scheme)) -> dict | None:
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    # Check revocation for optional auth too
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        return None
    return _user_repo.get_by_id(payload.get("sub", ""))

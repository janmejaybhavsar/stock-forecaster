from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.audit import log_event
from src.auth.revocation import revoke_token
from src.auth.schemas import Token, UserCreate, UserLogin, UserResponse
from src.auth.security import create_access_token, decode_token, hash_password, verify_password
from src.api.dependencies import get_current_user
from src.database.repositories import UserRepository

router = APIRouter(tags=["auth"])
_users = UserRepository()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(req: UserCreate, request: Request):
    ip = request.client.host if request.client else "unknown"

    if _users.get_by_email(req.email):
        log_event("register", email=req.email, ip_address=ip, detail="Email already registered", success=False)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    if _users.get_by_username(req.username):
        log_event("register", email=req.email, ip_address=ip, detail="Username already taken", success=False)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")
    if len(req.password) < 8:
        log_event("register", email=req.email, ip_address=ip, detail="Password too short", success=False)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
    if not (any(c.isdigit() for c in req.password) and any(c.isalpha() for c in req.password)):
        log_event("register", email=req.email, ip_address=ip, detail="Password too simple", success=False)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must contain both letters and numbers")

    pw_hash = hash_password(req.password)
    user = _users.create(req.email, req.username, pw_hash)
    log_event("register", user_id=user["id"], email=req.email, ip_address=ip, detail="Account created")
    return UserResponse(**user)


@router.post("/login", response_model=Token)
def login(req: UserLogin, request: Request):
    ip = request.client.host if request.client else "unknown"

    user = _users.get_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        log_event("login", email=req.email, ip_address=ip, detail="Invalid credentials", success=False)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = create_access_token({"sub": user["id"]})
    log_event("login", user_id=user["id"], email=req.email, ip_address=ip, detail="Login successful")
    return Token(access_token=token)


@router.post("/logout")
def logout(request: Request, user: dict = Depends(get_current_user)):
    """Revoke the current session token."""
    ip = request.client.host if request.client else "unknown"
    # Extract token from header for revocation
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload and "jti" in payload:
            revoke_token(payload["jti"], payload.get("exp"))

    log_event("logout", user_id=user["id"], ip_address=ip, detail="Session revoked")
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)

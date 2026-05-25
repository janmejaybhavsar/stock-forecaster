from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.schemas import Token, UserCreate, UserLogin, UserResponse
from src.auth.security import create_access_token, hash_password, verify_password
from src.api.dependencies import get_current_user
from src.database.repositories import UserRepository

router = APIRouter(tags=["auth"])
_users = UserRepository()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(req: UserCreate):
    if _users.get_by_email(req.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    if _users.get_by_username(req.username):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")
    if len(req.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
    if not any(char.isalpha() for char in req.password) or not any(char.isdigit() for char in req.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must contain both letters and numbers")

    pw_hash = hash_password(req.password)
    user = _users.create(req.email, req.username, pw_hash)
    return UserResponse(**user)


@router.post("/login", response_model=Token)
def login(req: UserLogin):
    user = _users.get_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token = create_access_token({"sub": user["id"]})
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)

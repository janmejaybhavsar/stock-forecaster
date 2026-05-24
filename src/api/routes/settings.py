from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.database.repositories import UserSettingsRepository

router = APIRouter(tags=["settings"])
_settings_repo = UserSettingsRepository()


class UserSettingsResponse(BaseModel):
    llm_provider: str = "gemini"
    llm_api_key: str = ""


class UserSettingsUpdate(BaseModel):
    llm_provider: str = "gemini"
    llm_api_key: str = ""


@router.get("/settings", response_model=UserSettingsResponse)
def get_settings(user: dict = Depends(get_current_user)):
    data = _settings_repo.get(user["id"])
    return UserSettingsResponse(llm_provider=data["llm_provider"], llm_api_key=data["llm_api_key"])


@router.put("/settings", response_model=UserSettingsResponse)
def update_settings(req: UserSettingsUpdate, user: dict = Depends(get_current_user)):
    data = _settings_repo.save(user["id"], req.llm_provider, req.llm_api_key)
    return UserSettingsResponse(llm_provider=data["llm_provider"], llm_api_key=data["llm_api_key"])

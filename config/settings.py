import secrets
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_provider: str = "yfinance"
    alpha_vantage_api_key: str = ""
    polygon_api_key: str = ""
    api_host: str = "localhost"
    api_port: int = 8000
    streamlit_port: int = 8501

    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 168  # 7 days

    llm_provider: str = "gemini"
    llm_api_key: str = ""

    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    cache_dir: Path = Path(__file__).resolve().parent.parent / "data" / "cache"
    models_dir: Path = Path(__file__).resolve().parent.parent / "data" / "models"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.cache_dir.mkdir(parents=True, exist_ok=True)
        _settings.models_dir.mkdir(parents=True, exist_ok=True)
        _settings.data_dir.mkdir(parents=True, exist_ok=True)
    return _settings


settings = get_settings()

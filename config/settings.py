import logging
import os
import secrets
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


def _stable_jwt_secret() -> str:
    """Return a persistent JWT secret: env var > .env file > generate and persist."""
    if os.environ.get("JWT_SECRET"):
        return os.environ["JWT_SECRET"]
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        try:
            secret_from_file = dotenv_values(env_path).get("JWT_SECRET")
            if secret_from_file:
                return str(secret_from_file)
        except OSError as exc:
            logger.warning("Unable to read JWT_SECRET from %s: %s", env_path, exc)
    # Generate and persist so it survives restarts
    secret = secrets.token_urlsafe(32)
    try:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"\nJWT_SECRET={secret}\n")
    except OSError as exc:
        logger.warning("Unable to persist JWT_SECRET to %s; using in-memory secret: %s", env_path, exc)
    return secret


class Settings(BaseSettings):
    data_provider: str = "yfinance"
    alpha_vantage_api_key: str = ""
    polygon_api_key: str = ""
    api_host: str = "localhost"
    api_port: int = 8000
    streamlit_port: int = 8501

    jwt_secret: str = _stable_jwt_secret()
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

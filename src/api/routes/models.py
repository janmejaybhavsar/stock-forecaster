from fastapi import APIRouter

router = APIRouter(tags=["models"])


@router.get("")
def list_models():
    try:
        from src.models.model_registry import list_models
        return {"models": list_models()}
    except Exception:
        return {"models": ["arima", "xgboost", "lstm", "transformer", "prophet", "ensemble"]}

from src.models.base_model import ForecastModel
from src.models.arima_model import ARIMAModel
from src.models.xgboost_model import XGBoostModel
from src.models.lstm_model import LSTMModel
from src.models.transformer_model import TransformerModel
from src.models.prophet_model import ProphetModel
from src.models.ensemble import EnsembleModel

REGISTRY: dict[str, type[ForecastModel]] = {
    "arima": ARIMAModel,
    "xgboost": XGBoostModel,
    "lstm": LSTMModel,
    "transformer": TransformerModel,
    "prophet": ProphetModel,
    "ensemble": EnsembleModel,
}


def get_model(name: str, **kwargs) -> ForecastModel:
    cls = REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown model '{name}'. Available: {list(REGISTRY)}")
    return cls(**kwargs)


def list_models() -> list[str]:
    return list(REGISTRY.keys())

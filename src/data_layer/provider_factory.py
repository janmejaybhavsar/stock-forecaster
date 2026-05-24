from config.settings import settings
from src.data_layer.base_provider import DataProvider
from src.data_layer.cache import CachedProvider
from src.data_layer.yfinance_provider import YFinanceProvider

_PROVIDERS: dict[str, type[DataProvider]] = {
    "yfinance": YFinanceProvider,
}

_instance: DataProvider | None = None


def get_provider() -> DataProvider:
    global _instance
    if _instance is None:
        provider_name = settings.data_provider
        provider_cls = _PROVIDERS.get(provider_name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown provider '{provider_name}'. Available: {list(_PROVIDERS)}"
            )
        _instance = CachedProvider(provider_cls())
    return _instance

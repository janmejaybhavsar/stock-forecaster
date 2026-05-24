from dataclasses import dataclass, field


@dataclass
class BacktestResult:
    model_name: str = ""
    ticker: str = ""
    metrics: dict = field(default_factory=dict)
    predictions: list[dict] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)

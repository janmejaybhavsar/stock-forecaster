"""
Composite Signal Engine.
Combines technical indicators, model consensus, and sentiment
into a single actionable signal with reasoning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

from src.signals.rules import (
    RuleResult,
    evaluate_model_consensus,
    evaluate_sentiment,
    evaluate_technical,
)

logger = logging.getLogger(__name__)


SIGNAL_LABELS = {
    (0.6, 1.0): "STRONG BUY",
    (0.2, 0.6): "BUY",
    (-0.2, 0.2): "HOLD",
    (-0.6, -0.2): "SELL",
    (-1.0, -0.6): "STRONG SELL",
}

SIGNAL_COLORS = {
    "STRONG BUY": "#00C851",
    "BUY": "#7CB342",
    "HOLD": "#FFB300",
    "SELL": "#FF5252",
    "STRONG SELL": "#D50000",
}


@dataclass
class SignalResult:
    ticker: str
    signal_label: str  # STRONG BUY / BUY / HOLD / SELL / STRONG SELL
    composite_score: float  # -1 to +1
    confidence: float  # 0 to 100
    color: str
    reasoning: list[str] = field(default_factory=list)
    technical: dict = field(default_factory=dict)
    model_consensus: dict = field(default_factory=dict)
    sentiment: dict = field(default_factory=dict)
    current_price: float = 0.0
    weights_used: dict = field(default_factory=dict)


def _score_to_label(score: float) -> str:
    """Convert composite score [-1, 1] to a human-readable label."""
    if score >= 0.6:
        return "STRONG BUY"
    elif score >= 0.2:
        return "BUY"
    elif score > -0.2:
        return "HOLD"
    elif score > -0.6:
        return "SELL"
    else:
        return "STRONG SELL"


def _compute_confidence(
    tech: RuleResult, consensus: RuleResult, sentiment: RuleResult
) -> float:
    """
    Compute confidence 0-100 based on:
    - Agreement between signals (all same direction = high confidence)
    - Strength of individual signals
    - Number of data sources available
    """
    signals = [tech.signal, consensus.signal, sentiment.signal]
    non_zero = [s for s in signals if abs(s) > 0.05]

    if not non_zero:
        return 30.0  # Low confidence when no clear signals

    # Agreement: are they pointing the same way?
    positive = sum(1 for s in non_zero if s > 0)
    negative = sum(1 for s in non_zero if s < 0)
    max_agreement = max(positive, negative)
    agreement_ratio = max_agreement / len(non_zero)

    # Average signal strength
    avg_strength = sum(abs(s) for s in non_zero) / len(non_zero)

    # Data completeness (how many sources have real data)
    sources_with_data = sum(1 for s in signals if abs(s) > 0.05)
    completeness = sources_with_data / 3

    confidence = (
        agreement_ratio * 40  # Up to 40 points for agreement
        + avg_strength * 35  # Up to 35 points for signal strength
        + completeness * 25  # Up to 25 points for data completeness
    )

    return round(min(95.0, max(10.0, confidence)), 1)


def generate_signal(
    ticker: str,
    horizon: int = 5,
    include_sentiment: bool = True,
    models_to_run: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> SignalResult:
    """
    Generate a composite buy/sell/hold signal for a ticker.

    Args:
        ticker: Stock ticker symbol
        horizon: Forecast horizon in days
        include_sentiment: Whether to include sentiment analysis
        models_to_run: Which models to run (default: fast models only)
        weights: Custom weights for {technical, consensus, sentiment}
    """
    from src.data_layer.provider_factory import get_provider
    from src.features.technical import add_technical_indicators

    # Default weights
    w = weights or {"technical": 0.40, "consensus": 0.35, "sentiment": 0.25}

    # Default to fast models (skip LSTM/transformer for speed)
    if models_to_run is None:
        models_to_run = ["arima", "xgboost", "prophet"]

    # --- 1. Fetch data and compute technical indicators ---
    provider = get_provider()
    end = date.today()
    start = end - timedelta(days=730)

    try:
        df = provider.get_historical(ticker, start, end)
        df = add_technical_indicators(df)
        current_price = float(df["Close"].iloc[-1])
    except Exception as e:
        logger.error(f"Failed to fetch data for {ticker}: {e}")
        return SignalResult(
            ticker=ticker,
            signal_label="HOLD",
            composite_score=0.0,
            confidence=0.0,
            color=SIGNAL_COLORS["HOLD"],
            reasoning=[f"Unable to fetch data: {e}"],
        )

    # --- 2. Evaluate Technical Indicators ---
    tech_result = evaluate_technical(df)

    # --- 3. Run Models for Consensus ---
    model_predictions: dict[str, dict] = {}
    for model_name in models_to_run:
        try:
            from src.features.pipeline import FeaturePipeline
            from src.models.model_registry import get_model

            pipeline = FeaturePipeline()
            features_df = pipeline.build(ticker, df.copy(), include_sentiment=False)

            model = get_model(model_name)
            model.fit(features_df, target_col="Close")
            predictions = model.predict(horizon)

            if not predictions.empty:
                last_pred = predictions.iloc[-1]
                model_predictions[model_name] = {
                    "predicted_close": float(last_pred["predicted_close"]),
                    "horizon": horizon,
                }
        except Exception as e:
            logger.warning(f"Model {model_name} failed for {ticker}: {e}")
            continue

    consensus_result = evaluate_model_consensus(current_price, model_predictions)

    # --- 4. Evaluate Sentiment ---
    if include_sentiment:
        try:
            from src.features.sentiment import SentimentAnalyzer
            analyzer = SentimentAnalyzer()
            headlines = analyzer.fetch_headlines(ticker, days=14)
            scored = analyzer.score_headlines(headlines)
            sentiment_result = evaluate_sentiment(scored)
        except Exception as e:
            logger.warning(f"Sentiment analysis failed for {ticker}: {e}")
            sentiment_result = RuleResult(
                signal=0.0,
                reasoning=["Sentiment analysis unavailable"],
            )
    else:
        sentiment_result = RuleResult(signal=0.0, reasoning=["Sentiment not included"])
        # Redistribute weight to other factors
        w["technical"] = 0.55
        w["consensus"] = 0.45
        w["sentiment"] = 0.0

    # --- 5. Compute Composite Score ---
    composite = (
        tech_result.signal * w["technical"]
        + consensus_result.signal * w["consensus"]
        + sentiment_result.signal * w["sentiment"]
    )
    composite = max(-1.0, min(1.0, composite))

    label = _score_to_label(composite)
    confidence = _compute_confidence(tech_result, consensus_result, sentiment_result)

    # Combine all reasoning
    all_reasoning = []
    all_reasoning.extend(tech_result.reasoning)
    all_reasoning.extend(consensus_result.reasoning)
    all_reasoning.extend(sentiment_result.reasoning)

    return SignalResult(
        ticker=ticker,
        signal_label=label,
        composite_score=round(composite, 3),
        confidence=confidence,
        color=SIGNAL_COLORS[label],
        reasoning=all_reasoning,
        technical={
            "signal": round(tech_result.signal, 3),
            "details": tech_result.details,
            "reasoning": tech_result.reasoning,
        },
        model_consensus={
            "signal": round(consensus_result.signal, 3),
            "details": consensus_result.details,
            "reasoning": consensus_result.reasoning,
        },
        sentiment={
            "signal": round(sentiment_result.signal, 3),
            "details": sentiment_result.details,
            "reasoning": sentiment_result.reasoning,
        },
        current_price=current_price,
        weights_used=w,
    )


def generate_portfolio_signals(
    holdings: list[dict],
    horizon: int = 5,
    include_sentiment: bool = False,
) -> list[SignalResult]:
    """Generate signals for all holdings in a portfolio."""
    results = []
    for holding in holdings:
        ticker = holding["ticker"]
        try:
            result = generate_signal(
                ticker=ticker,
                horizon=horizon,
                include_sentiment=include_sentiment,
                models_to_run=["arima", "xgboost"],  # Fast only for portfolio scan
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Signal generation failed for {ticker}: {e}")
            results.append(SignalResult(
                ticker=ticker,
                signal_label="HOLD",
                composite_score=0.0,
                confidence=0.0,
                color=SIGNAL_COLORS["HOLD"],
                reasoning=[f"Analysis failed: {e}"],
            ))
    return results

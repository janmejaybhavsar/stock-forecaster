"""
Individual signal evaluation rules.
Each evaluator returns a dict with:
  - signal: float in [-1, 1] where -1=strong sell, +1=strong buy
  - details: dict of per-indicator breakdowns
  - reasoning: list[str] of human-readable explanations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RuleResult:
    signal: float  # -1 to +1
    details: dict = field(default_factory=dict)
    reasoning: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 1. Technical Indicator Signals
# ---------------------------------------------------------------------------

def evaluate_technical(df: pd.DataFrame) -> RuleResult:
    """Evaluate technical indicators from the most recent data."""
    if df.empty or len(df) < 50:
        return RuleResult(signal=0.0, reasoning=["Insufficient data for technical analysis"])

    latest = df.iloc[-1]
    close = latest["Close"]

    signals: list[float] = []
    details: dict = {}
    reasoning: list[str] = []

    # --- RSI ---
    rsi = latest.get("rsi_14")
    if rsi is not None and pd.notna(rsi):
        details["rsi_14"] = round(rsi, 1)
        if rsi < 30:
            sig = 0.8
            reasoning.append(f"RSI at {rsi:.0f} — stock is oversold (bullish)")
        elif rsi < 40:
            sig = 0.3
            reasoning.append(f"RSI at {rsi:.0f} — approaching oversold territory")
        elif rsi > 70:
            sig = -0.8
            reasoning.append(f"RSI at {rsi:.0f} — stock is overbought (bearish)")
        elif rsi > 60:
            sig = -0.3
            reasoning.append(f"RSI at {rsi:.0f} — approaching overbought territory")
        else:
            sig = 0.0
            reasoning.append(f"RSI at {rsi:.0f} — neutral range")
        signals.append(sig)

    # --- MACD Crossover ---
    macd_val = latest.get("macd")
    macd_sig = latest.get("macd_signal")
    macd_hist = latest.get("macd_hist")
    if all(v is not None and pd.notna(v) for v in [macd_val, macd_sig, macd_hist]):
        details["macd"] = round(macd_val, 4)
        details["macd_signal"] = round(macd_sig, 4)
        details["macd_histogram"] = round(macd_hist, 4)

        # Check for crossover using last 2 bars
        if len(df) >= 2:
            prev_hist = df.iloc[-2].get("macd_hist")
            if prev_hist is not None and pd.notna(prev_hist):
                if prev_hist < 0 and macd_hist > 0:
                    sig = 0.7
                    reasoning.append("MACD bullish crossover — momentum turning positive")
                elif prev_hist > 0 and macd_hist < 0:
                    sig = -0.7
                    reasoning.append("MACD bearish crossover — momentum turning negative")
                elif macd_hist > 0:
                    sig = 0.3
                    reasoning.append("MACD histogram positive — bullish momentum")
                else:
                    sig = -0.3
                    reasoning.append("MACD histogram negative — bearish momentum")
                signals.append(sig)

    # --- Bollinger Bands ---
    bb_upper = latest.get("bb_upper")
    bb_lower = latest.get("bb_lower")
    bb_middle = latest.get("bb_middle")
    if all(v is not None and pd.notna(v) for v in [bb_upper, bb_lower, bb_middle]):
        bb_width = bb_upper - bb_lower
        if bb_width > 0:
            bb_position = (close - bb_lower) / bb_width  # 0=lower band, 1=upper band
            details["bb_position"] = round(bb_position, 2)

            if bb_position < 0.1:
                sig = 0.6
                reasoning.append("Price near lower Bollinger Band — potential bounce (oversold)")
            elif bb_position > 0.9:
                sig = -0.6
                reasoning.append("Price near upper Bollinger Band — potential pullback (overbought)")
            elif bb_position < 0.3:
                sig = 0.2
                reasoning.append("Price in lower Bollinger zone — mild bullish signal")
            elif bb_position > 0.7:
                sig = -0.2
                reasoning.append("Price in upper Bollinger zone — mild bearish signal")
            else:
                sig = 0.0
            signals.append(sig)

    # --- SMA Crossovers (Golden/Death Cross) ---
    sma_50 = latest.get("sma_50")
    sma_200 = latest.get("sma_200")
    if all(v is not None and pd.notna(v) for v in [sma_50, sma_200]):
        details["sma_50"] = round(sma_50, 2)
        details["sma_200"] = round(sma_200, 2)

        if sma_50 > sma_200:
            # Check if it just crossed
            if len(df) >= 2:
                prev_sma50 = df.iloc[-2].get("sma_50")
                prev_sma200 = df.iloc[-2].get("sma_200")
                if prev_sma50 is not None and prev_sma200 is not None and pd.notna(prev_sma50) and pd.notna(prev_sma200):
                    if prev_sma50 <= prev_sma200:
                        sig = 0.9
                        reasoning.append("Golden Cross — 50-day SMA crossed above 200-day SMA (strong bullish)")
                    else:
                        sig = 0.4
                        reasoning.append("Price above 200-day SMA — bullish long-term trend")
                else:
                    sig = 0.4
                    reasoning.append("Price above 200-day SMA — bullish long-term trend")
            else:
                sig = 0.4
                reasoning.append("Price above 200-day SMA — bullish long-term trend")
            signals.append(sig)
        else:
            if len(df) >= 2:
                prev_sma50 = df.iloc[-2].get("sma_50")
                prev_sma200 = df.iloc[-2].get("sma_200")
                if prev_sma50 is not None and prev_sma200 is not None and pd.notna(prev_sma50) and pd.notna(prev_sma200):
                    if prev_sma50 >= prev_sma200:
                        sig = -0.9
                        reasoning.append("Death Cross — 50-day SMA crossed below 200-day SMA (strong bearish)")
                    else:
                        sig = -0.4
                        reasoning.append("Price below 200-day SMA — bearish long-term trend")
                else:
                    sig = -0.4
                    reasoning.append("Price below 200-day SMA — bearish long-term trend")
            else:
                sig = -0.4
                reasoning.append("Price below 200-day SMA — bearish long-term trend")
            signals.append(sig)

    # --- Price vs SMA 20 (short-term trend) ---
    sma_20 = latest.get("sma_20")
    if sma_20 is not None and pd.notna(sma_20):
        pct_from_sma20 = (close - sma_20) / sma_20 * 100
        details["pct_from_sma20"] = round(pct_from_sma20, 2)
        if pct_from_sma20 > 5:
            sig = -0.3
            reasoning.append(f"Price {pct_from_sma20:.1f}% above 20-day SMA — extended, may pull back")
        elif pct_from_sma20 < -5:
            sig = 0.3
            reasoning.append(f"Price {abs(pct_from_sma20):.1f}% below 20-day SMA — may bounce")
        else:
            sig = 0.0
        signals.append(sig)

    # --- Stochastic Oscillator ---
    stoch_k = latest.get("stoch_k")
    if stoch_k is not None and pd.notna(stoch_k):
        details["stoch_k"] = round(stoch_k, 1)
        if stoch_k < 20:
            sig = 0.5
            reasoning.append(f"Stochastic %K at {stoch_k:.0f} — oversold")
        elif stoch_k > 80:
            sig = -0.5
            reasoning.append(f"Stochastic %K at {stoch_k:.0f} — overbought")
        else:
            sig = 0.0
        signals.append(sig)

    # --- Volume ---
    vol_norm = latest.get("volume_norm")
    if vol_norm is not None and pd.notna(vol_norm):
        details["volume_vs_avg"] = round(vol_norm, 2)
        if vol_norm > 2.0:
            reasoning.append(f"Volume {vol_norm:.1f}x above average — high conviction move")

    # Compute composite technical signal
    if signals:
        composite = sum(signals) / len(signals)
    else:
        composite = 0.0

    return RuleResult(
        signal=max(-1.0, min(1.0, composite)),
        details=details,
        reasoning=reasoning,
    )


# ---------------------------------------------------------------------------
# 2. Model Consensus Signals
# ---------------------------------------------------------------------------

def evaluate_model_consensus(
    current_price: float,
    predictions: dict[str, dict],
) -> RuleResult:
    """
    Evaluate consensus from multiple model predictions.

    predictions: {model_name: {"predicted_close": float, "horizon": int, "confidence": float}}
    """
    if not predictions:
        return RuleResult(signal=0.0, reasoning=["No model predictions available"])

    bullish = 0
    bearish = 0
    total_return = 0.0
    model_signals: dict[str, str] = {}
    reasoning: list[str] = []

    for model_name, pred in predictions.items():
        predicted = pred.get("predicted_close", current_price)
        expected_return = (predicted - current_price) / current_price * 100

        if expected_return > 1.0:
            bullish += 1
            model_signals[model_name] = f"bullish ({expected_return:+.1f}%)"
        elif expected_return < -1.0:
            bearish += 1
            model_signals[model_name] = f"bearish ({expected_return:+.1f}%)"
        else:
            model_signals[model_name] = f"neutral ({expected_return:+.1f}%)"

        total_return += expected_return

    total_models = len(predictions)
    avg_return = total_return / total_models

    # Consensus signal
    if bullish > bearish:
        signal = min(1.0, (bullish / total_models) * 0.8 + abs(avg_return) / 10)
    elif bearish > bullish:
        signal = max(-1.0, -(bearish / total_models) * 0.8 - abs(avg_return) / 10)
    else:
        signal = avg_return / 10  # Slight lean based on average predicted return

    signal = max(-1.0, min(1.0, signal))

    reasoning.append(
        f"{bullish}/{total_models} models predict upside, "
        f"{bearish}/{total_models} predict downside"
    )
    if abs(avg_return) > 0.5:
        reasoning.append(f"Average predicted return: {avg_return:+.1f}% over forecast horizon")

    return RuleResult(
        signal=signal,
        details={
            "bullish_models": bullish,
            "bearish_models": bearish,
            "neutral_models": total_models - bullish - bearish,
            "total_models": total_models,
            "avg_predicted_return_pct": round(avg_return, 2),
            "per_model": model_signals,
        },
        reasoning=reasoning,
    )


# ---------------------------------------------------------------------------
# 3. Sentiment Signals
# ---------------------------------------------------------------------------

def evaluate_sentiment(scored_headlines: list[dict]) -> RuleResult:
    """
    Evaluate sentiment from FinBERT-scored headlines.

    scored_headlines: list of {"headline": str, "sentiment": "positive"|"negative"|"neutral", "score": float}
    """
    if not scored_headlines:
        return RuleResult(signal=0.0, reasoning=["No news headlines available for sentiment analysis"])

    pos_count = 0
    neg_count = 0
    neu_count = 0
    pos_total = 0.0
    neg_total = 0.0

    for h in scored_headlines:
        sentiment = h.get("sentiment", "neutral")
        score = h.get("score", 0.5)
        if sentiment == "positive":
            pos_count += 1
            pos_total += score
        elif sentiment == "negative":
            neg_count += 1
            neg_total += score
        else:
            neu_count += 1

    total = len(scored_headlines)

    # Net sentiment score: difference between positive and negative proportions
    pos_ratio = pos_count / total
    neg_ratio = neg_count / total
    net_sentiment = pos_ratio - neg_ratio  # -1 to +1

    # Weighted by confidence
    if pos_count + neg_count > 0:
        weighted_pos = pos_total / total
        weighted_neg = neg_total / total
        weighted_net = weighted_pos - weighted_neg
    else:
        weighted_net = 0.0

    # Combine ratio-based and confidence-weighted
    signal = (net_sentiment * 0.5 + weighted_net * 0.5)
    signal = max(-1.0, min(1.0, signal))

    reasoning: list[str] = []
    if signal > 0.2:
        reasoning.append(f"Positive news sentiment ({pos_count}/{total} headlines positive, score: {signal:.2f})")
    elif signal < -0.2:
        reasoning.append(f"Negative news sentiment ({neg_count}/{total} headlines negative, score: {signal:.2f})")
    else:
        reasoning.append(f"Neutral news sentiment ({pos_count} positive, {neg_count} negative out of {total})")

    return RuleResult(
        signal=signal,
        details={
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
            "total_headlines": total,
            "net_sentiment": round(net_sentiment, 3),
            "weighted_net": round(weighted_net, 3),
            "top_headlines": [
                {"headline": h["headline"], "sentiment": h["sentiment"], "score": h["score"]}
                for h in sorted(scored_headlines, key=lambda x: x.get("score", 0), reverse=True)[:5]
            ],
        },
        reasoning=reasoning,
    )

"""Tests for the signal engine: technical rules, model consensus, sentiment."""

import numpy as np
import pandas as pd
import pytest


class TestEvaluateTechnical:
    def _make_df(self, n=200, **overrides):
        """Create a DataFrame with default technical indicator columns."""
        df = pd.DataFrame({
            "Close": np.linspace(100, 110, n),
            "High": np.linspace(101, 111, n),
            "Low": np.linspace(99, 109, n),
            "Volume": np.full(n, 1_000_000),
            "rsi_14": np.full(n, 50),
            "macd": np.full(n, 0.5),
            "macd_signal": np.full(n, 0.3),
            "macd_hist": np.full(n, 0.2),
            "bb_upper": np.full(n, 115),
            "bb_lower": np.full(n, 95),
            "bb_middle": np.full(n, 105),
            "sma_20": np.full(n, 105),
            "sma_50": np.full(n, 103),
            "sma_200": np.full(n, 100),
            "stoch_k": np.full(n, 50),
            "stoch_d": np.full(n, 50),
            "volume_norm": np.full(n, 1.0),
        })
        for col, val in overrides.items():
            if callable(val):
                df[col] = val(n)
            else:
                df[col] = val
        return df

    def test_oversold_rsi_bullish(self):
        from src.signals.rules import evaluate_technical

        df = self._make_df(rsi_14=25)
        result = evaluate_technical(df)
        assert result.signal > 0
        assert any("oversold" in r.lower() for r in result.reasoning)

    def test_overbought_rsi_bearish(self):
        from src.signals.rules import evaluate_technical

        df = self._make_df(rsi_14=75)
        result = evaluate_technical(df)
        assert result.signal < 0
        assert any("overbought" in r.lower() for r in result.reasoning)

    def test_insufficient_data(self):
        from src.signals.rules import evaluate_technical

        df = self._make_df(n=10)
        result = evaluate_technical(df)
        assert result.signal == 0.0
        assert "Insufficient" in result.reasoning[0]

    def test_empty_dataframe(self):
        from src.signals.rules import evaluate_technical

        result = evaluate_technical(pd.DataFrame())
        assert result.signal == 0.0

    def test_signal_bounded(self):
        from src.signals.rules import evaluate_technical

        # All bearish indicators
        df = self._make_df(rsi_14=85, stoch_k=90)
        result = evaluate_technical(df)
        assert -1.0 <= result.signal <= 1.0

    def test_macd_bullish_crossover(self):
        from src.signals.rules import evaluate_technical

        df = self._make_df()
        df.loc[df.index[-2], "macd_hist"] = -0.1  # was negative
        df.loc[df.index[-1], "macd_hist"] = 0.1   # now positive
        result = evaluate_technical(df)
        assert any("bullish crossover" in r.lower() for r in result.reasoning)

    def test_bollinger_lower_band(self):
        from src.signals.rules import evaluate_technical

        # Price near lower band
        df = self._make_df(bb_lower=109, bb_upper=120, bb_middle=114.5)
        # Close is ~110, bb_lower=109, so position ≈ 0.09 → bullish
        result = evaluate_technical(df)
        assert any("lower bollinger" in r.lower() for r in result.reasoning)


class TestEvaluateModelConsensus:
    def test_bullish_consensus(self):
        from src.signals.rules import evaluate_model_consensus

        preds = {
            "arima": {"predicted_close": 115, "horizon": 5, "confidence": 0.7},
            "xgboost": {"predicted_close": 112, "horizon": 5, "confidence": 0.8},
            "prophet": {"predicted_close": 108, "horizon": 5, "confidence": 0.6},
        }
        result = evaluate_model_consensus(100, preds)
        assert result.signal > 0
        assert result.details["bullish_models"] == 3

    def test_bearish_consensus(self):
        from src.signals.rules import evaluate_model_consensus

        preds = {
            "arima": {"predicted_close": 90, "horizon": 5, "confidence": 0.7},
            "xgboost": {"predicted_close": 92, "horizon": 5, "confidence": 0.8},
        }
        result = evaluate_model_consensus(100, preds)
        assert result.signal < 0
        assert result.details["bearish_models"] == 2

    def test_mixed_signals(self):
        from src.signals.rules import evaluate_model_consensus

        preds = {
            "arima": {"predicted_close": 105, "horizon": 5, "confidence": 0.7},
            "xgboost": {"predicted_close": 95, "horizon": 5, "confidence": 0.8},
        }
        result = evaluate_model_consensus(100, preds)
        assert result.details["bullish_models"] == 1
        assert result.details["bearish_models"] == 1

    def test_no_predictions(self):
        from src.signals.rules import evaluate_model_consensus

        result = evaluate_model_consensus(100, {})
        assert result.signal == 0.0

    def test_signal_bounded(self):
        from src.signals.rules import evaluate_model_consensus

        preds = {f"model_{i}": {"predicted_close": 200, "horizon": 5, "confidence": 0.9} for i in range(10)}
        result = evaluate_model_consensus(100, preds)
        assert -1.0 <= result.signal <= 1.0


class TestEvaluateSentiment:
    def test_positive_sentiment(self):
        from src.signals.rules import evaluate_sentiment

        headlines = [
            {"headline": "Stock surges", "sentiment": "positive", "score": 0.9},
            {"headline": "Record earnings", "sentiment": "positive", "score": 0.85},
            {"headline": "Market neutral", "sentiment": "neutral", "score": 0.5},
        ]
        result = evaluate_sentiment(headlines)
        assert result.signal > 0
        assert result.details["positive_count"] == 2

    def test_negative_sentiment(self):
        from src.signals.rules import evaluate_sentiment

        headlines = [
            {"headline": "Stock crashes", "sentiment": "negative", "score": 0.95},
            {"headline": "Layoffs announced", "sentiment": "negative", "score": 0.8},
        ]
        result = evaluate_sentiment(headlines)
        assert result.signal < 0
        assert result.details["negative_count"] == 2

    def test_no_headlines(self):
        from src.signals.rules import evaluate_sentiment

        result = evaluate_sentiment([])
        assert result.signal == 0.0

    def test_signal_bounded(self):
        from src.signals.rules import evaluate_sentiment

        headlines = [{"headline": f"h{i}", "sentiment": "positive", "score": 0.99} for i in range(20)]
        result = evaluate_sentiment(headlines)
        assert -1.0 <= result.signal <= 1.0

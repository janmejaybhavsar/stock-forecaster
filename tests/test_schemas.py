"""Tests for Pydantic request schema validation."""

import pytest
from pydantic import ValidationError

from src.api.schemas import BacktestRequest, ForecastRequest


class TestForecastRequest:
    def test_valid_request(self):
        req = ForecastRequest(ticker="AAPL", model_name="arima", horizon=5)
        assert req.ticker == "AAPL"
        assert req.model_name == "arima"
        assert req.horizon == 5

    def test_ticker_uppercased(self):
        req = ForecastRequest(ticker="aapl")
        assert req.ticker == "AAPL"

    def test_ticker_with_exchange(self):
        req = ForecastRequest(ticker="RELIANCE.NS")
        assert req.ticker == "RELIANCE.NS"

    def test_ticker_with_caret(self):
        req = ForecastRequest(ticker="^GSPC")
        assert req.ticker == "^GSPC"

    def test_invalid_ticker_chars(self):
        with pytest.raises(ValidationError):
            ForecastRequest(ticker="AAPL$$$")

    def test_empty_ticker(self):
        with pytest.raises(ValidationError):
            ForecastRequest(ticker="")

    def test_ticker_too_long(self):
        with pytest.raises(ValidationError):
            ForecastRequest(ticker="A" * 21)

    def test_invalid_model_name(self):
        with pytest.raises(ValidationError):
            ForecastRequest(ticker="AAPL", model_name="invalid_model")

    def test_all_valid_models(self):
        for model in ["arima", "xgboost", "lstm", "transformer", "prophet", "ensemble"]:
            req = ForecastRequest(ticker="AAPL", model_name=model)
            assert req.model_name == model

    def test_horizon_min(self):
        req = ForecastRequest(ticker="AAPL", horizon=1)
        assert req.horizon == 1

    def test_horizon_max(self):
        req = ForecastRequest(ticker="AAPL", horizon=30)
        assert req.horizon == 30

    def test_horizon_too_low(self):
        with pytest.raises(ValidationError):
            ForecastRequest(ticker="AAPL", horizon=0)

    def test_horizon_too_high(self):
        with pytest.raises(ValidationError):
            ForecastRequest(ticker="AAPL", horizon=31)

    def test_defaults(self):
        req = ForecastRequest(ticker="AAPL")
        assert req.model_name == "arima"
        assert req.horizon == 5
        assert req.include_sentiment is False


class TestBacktestRequest:
    def test_valid_request(self):
        req = BacktestRequest(
            ticker="MSFT", model_name="xgboost",
            train_window=252, test_window=21, step_size=21,
        )
        assert req.ticker == "MSFT"

    def test_train_window_bounds(self):
        with pytest.raises(ValidationError):
            BacktestRequest(ticker="AAPL", train_window=59)
        with pytest.raises(ValidationError):
            BacktestRequest(ticker="AAPL", train_window=1001)

    def test_test_window_bounds(self):
        with pytest.raises(ValidationError):
            BacktestRequest(ticker="AAPL", test_window=4)
        with pytest.raises(ValidationError):
            BacktestRequest(ticker="AAPL", test_window=253)

    def test_step_size_bounds(self):
        with pytest.raises(ValidationError):
            BacktestRequest(ticker="AAPL", step_size=0)
        with pytest.raises(ValidationError):
            BacktestRequest(ticker="AAPL", step_size=253)

    def test_defaults(self):
        req = BacktestRequest(ticker="AAPL")
        assert req.model_name == "arima"
        assert req.train_window == 252
        assert req.test_window == 21
        assert req.step_size == 21

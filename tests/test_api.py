"""Tests for API endpoints: portfolio, signals, auth flow."""

from unittest.mock import patch, MagicMock

import pytest


class TestRootEndpoint:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "Stock Forecaster" in r.json()["message"]


class TestPortfolioAPI:
    def test_add_holding(self, client, auth_headers):
        r = client.post("/api/v1/portfolio/holdings", json={
            "ticker": "AAPL",
            "shares": 10,
            "avg_cost": 150.0,
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["ticker"] == "AAPL"

    def test_add_holding_unauthorized(self, client):
        r = client.post("/api/v1/portfolio/holdings", json={
            "ticker": "AAPL", "shares": 10, "avg_cost": 150.0,
        })
        assert r.status_code == 401

    def test_delete_holding(self, client, auth_headers):
        r = client.post("/api/v1/portfolio/holdings", json={
            "ticker": "MSFT", "shares": 5, "avg_cost": 300.0,
        }, headers=auth_headers)
        hid = r.json()["id"]

        r = client.delete(f"/api/v1/portfolio/holdings/{hid}", headers=auth_headers)
        assert r.status_code == 200


class TestSignalsAPI:
    @patch("src.signals.engine.generate_signal")
    def test_get_signal(self, mock_gen, client):
        from src.signals.engine import SignalResult
        mock_gen.return_value = SignalResult(
            ticker="AAPL",
            signal_label="BUY",
            composite_score=0.6,
            confidence=72.0,
            color="#00C851",
            reasoning=["Test reason"],
            technical={"rsi_14": 45},
            model_consensus={"bullish_models": 2},
            sentiment={},
            current_price=175.0,
        )

        r = client.get("/api/v1/signals/AAPL?horizon=5")
        assert r.status_code == 200
        data = r.json()
        assert data["ticker"] == "AAPL"
        assert data["signal_label"] == "BUY"
        assert data["confidence"] == 72.0


class TestModelsAPI:
    def test_list_models(self, client):
        r = client.get("/api/v1/models/")
        assert r.status_code == 200
        data = r.json()
        assert "models" in data
        assert len(data["models"]) > 0

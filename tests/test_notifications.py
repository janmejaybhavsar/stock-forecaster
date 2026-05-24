"""Tests for the smart notifications generator."""

from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np


class TestGenerateNotifications:
    def _mock_provider(self, change_pct=0.0, n_days=10):
        """Create a mock data provider with controlled price changes."""
        provider = MagicMock()
        prices = np.linspace(100, 100 * (1 + change_pct / 100), n_days)
        df = pd.DataFrame({
            "Close": prices,
            "High": prices * 1.01,
            "Low": prices * 0.99,
        })
        provider.get_historical.return_value = df
        return provider

    def test_no_holdings_returns_empty(self):
        from src.signals.notifications import generate_notifications

        result = generate_notifications([], {"total_value": 0})
        assert result == []

    @patch("src.data_layer.provider_factory.get_provider")
    def test_significant_move_notification(self, mock_get_prov):
        from src.signals.notifications import generate_notifications

        # Create mock with price change large enough to trigger alert (>3%)
        provider = MagicMock()
        prices = [100.0] * 8 + [100.0, 107.0]  # 7% jump on last day
        df = pd.DataFrame({
            "Close": prices,
            "High": [p * 1.01 for p in prices],
            "Low": [p * 0.99 for p in prices],
        })
        provider.get_historical.return_value = df
        mock_get_prov.return_value = provider

        holdings = [{"ticker": "AAPL", "market_value": 1000, "pnl": 100, "pnl_pct": 10}]
        summary = {"total_value": 1000, "total_pnl_pct": 10}

        result = generate_notifications(holdings, summary)
        price_alerts = [n for n in result if n.type == "price_alert"]
        assert len(price_alerts) > 0

    @patch("src.data_layer.provider_factory.get_provider")
    def test_concentration_warning(self, mock_get_prov):
        from src.signals.notifications import generate_notifications

        mock_get_prov.return_value = self._mock_provider(change_pct=0.5)

        holdings = [
            {"ticker": "AAPL", "market_value": 8000, "pnl": 100, "pnl_pct": 5},
            {"ticker": "GOOGL", "market_value": 2000, "pnl": 50, "pnl_pct": 3},
        ]
        summary = {"total_value": 10000, "total_pnl_pct": 4}

        result = generate_notifications(holdings, summary)
        risk_notifs = [n for n in result if n.type == "portfolio_risk"]
        assert len(risk_notifs) > 0  # AAPL is 80% of portfolio

    @patch("src.data_layer.provider_factory.get_provider")
    def test_pnl_milestone_positive(self, mock_get_prov):
        from src.signals.notifications import generate_notifications

        mock_get_prov.return_value = self._mock_provider(change_pct=0.5)

        holdings = [{"ticker": "AAPL", "market_value": 1000, "pnl": 200, "pnl_pct": 5}]
        summary = {"total_value": 1000, "total_pnl_pct": 15}

        result = generate_notifications(holdings, summary)
        milestones = [n for n in result if n.type == "milestone"]
        assert any("up" in m.message.lower() for m in milestones)

    @patch("src.data_layer.provider_factory.get_provider")
    def test_pnl_milestone_negative(self, mock_get_prov):
        from src.signals.notifications import generate_notifications

        mock_get_prov.return_value = self._mock_provider(change_pct=0.5)

        holdings = [{"ticker": "AAPL", "market_value": 700, "pnl": -300, "pnl_pct": -30}]
        summary = {"total_value": 700, "total_pnl_pct": -30}

        result = generate_notifications(holdings, summary)
        milestones = [n for n in result if n.type == "milestone"]
        assert len(milestones) > 0

    @patch("src.data_layer.provider_factory.get_provider")
    def test_sorted_by_priority(self, mock_get_prov):
        from src.signals.notifications import generate_notifications

        mock_get_prov.return_value = self._mock_provider(change_pct=7.0)

        holdings = [
            {"ticker": "AAPL", "market_value": 9000, "pnl": 500, "pnl_pct": 55},
        ]
        summary = {"total_value": 9000, "total_pnl_pct": 55}

        result = generate_notifications(holdings, summary)
        if len(result) >= 2:
            priorities = [n.priority for n in result]
            order = {"high": 0, "medium": 1, "low": 2}
            assert all(order.get(priorities[i], 99) <= order.get(priorities[i + 1], 99)
                       for i in range(len(priorities) - 1))

    def test_signal_based_notifications(self):
        from src.signals.notifications import generate_notifications

        with patch("src.data_layer.provider_factory.get_provider") as mock_prov:
            mock_prov.return_value = self._mock_provider(change_pct=0.5)

            holdings = [{"ticker": "AAPL", "market_value": 1000, "pnl": 0, "pnl_pct": 0}]
            summary = {"total_value": 1000, "total_pnl_pct": 0}
            signals = [{"ticker": "AAPL", "signal_label": "STRONG BUY", "confidence": 80}]

            result = generate_notifications(holdings, summary, signals=signals)
            opps = [n for n in result if n.type == "opportunity"]
            assert len(opps) > 0

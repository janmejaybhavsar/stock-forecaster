"""
Portfolio Coach — high-level coaching functions that combine data + LLM.
"""

from __future__ import annotations

import logging

from src.coach.llm_client import get_llm_client
from src.coach.prompts import (
    SYSTEM_PROMPT,
    QUESTION_TEMPLATE,
    build_portfolio_context,
    build_signal_context,
)

logger = logging.getLogger(__name__)


class PortfolioCoach:
    """AI-powered portfolio coach."""

    def __init__(self, provider: str | None = None, api_key: str | None = None):
        self.client = get_llm_client(provider=provider, api_key=api_key)
        logger.info(f"Portfolio Coach initialized with LLM: {self.client.name}")

    def analyze_portfolio(
        self,
        holdings: list[dict],
        summary: dict,
        signals: list[dict] | None = None,
    ) -> str:
        """Get an overall portfolio health analysis."""
        context = build_portfolio_context(holdings, summary, signals)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    "Please analyze my portfolio and tell me:\n"
                    "1. Overall health assessment\n"
                    "2. Key strengths\n"
                    "3. Key risks or concerns\n"
                    "4. Top 3 actionable suggestions\n"
                    "Keep it friendly and easy to understand."
                ),
            }
        ]

        return self.client.chat(messages, system=SYSTEM_PROMPT)

    def explain_signal(self, signal_data: dict) -> str:
        """Explain a buy/sell/hold signal in plain English."""
        context = build_signal_context(signal_data)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    "Please explain this signal in plain English. "
                    "What does it mean for me? Should I act on it? What are the risks?"
                ),
            }
        ]

        return self.client.chat(messages, system=SYSTEM_PROMPT)

    def suggest_rebalancing(
        self,
        holdings: list[dict],
        summary: dict,
    ) -> str:
        """Suggest portfolio rebalancing strategies."""
        context = build_portfolio_context(holdings, summary)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    "How should I rebalance my portfolio? Consider:\n"
                    "- Am I too concentrated in any one stock?\n"
                    "- Should I diversify into different sectors/markets?\n"
                    "- What percentage should each holding be?\n"
                    "- Any stocks I should consider adding or reducing?\n"
                    "Give me a specific rebalancing plan."
                ),
            }
        ]

        return self.client.chat(messages, system=SYSTEM_PROMPT)

    def answer_question(
        self,
        question: str,
        holdings: list[dict] | None = None,
        summary: dict | None = None,
        chat_history: list[dict] | None = None,
    ) -> str:
        """Answer a freeform question about the portfolio or investing."""
        if holdings and summary:
            portfolio_context = build_portfolio_context(holdings, summary)
        else:
            portfolio_context = "No portfolio data available."

        user_message = QUESTION_TEMPLATE.format(
            portfolio_context=portfolio_context,
            question=question,
        )

        messages = []
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        return self.client.chat(messages, system=SYSTEM_PROMPT)

"""
Learning Path Module Definitions.
Progressive, gamified learning with real portfolio integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LearningStep:
    id: str
    title: str
    description: str
    action_text: str  # What the user should do
    page_link: str | None = None  # Navigate to this page
    check_type: str = "manual"  # "manual" (user marks done) or "auto" (system checks)


@dataclass
class LearningModule:
    id: str
    title: str
    description: str
    icon: str
    steps: list[LearningStep] = field(default_factory=list)
    badge: str = ""  # Achievement badge emoji


MODULES: list[LearningModule] = [
    LearningModule(
        id="getting_started",
        title="Getting Started",
        description="Set up your account and add your first stock",
        icon="\U0001f680",
        badge="\U0001f31f",
        steps=[
            LearningStep(
                id="create_account",
                title="Create Your Account",
                description="Register for a free account to track your portfolio",
                action_text="Go to the Login page and create an account",
                page_link="pages/0_Login.py",
            ),
            LearningStep(
                id="explore_overview",
                title="Explore the Overview",
                description="Check out the stock chart and metrics for AAPL",
                action_text="Visit the Overview page and look at the candlestick chart",
                page_link="pages/1_Overview.py",
            ),
            LearningStep(
                id="add_first_stock",
                title="Add Your First Stock",
                description="Pick a stock you're interested in and add it to your portfolio",
                action_text="Go to Portfolio and add a holding (e.g., AAPL, 10 shares at your purchase price)",
                page_link="pages/6_Portfolio.py",
            ),
        ],
    ),
    LearningModule(
        id="reading_signals",
        title="Reading the Signals",
        description="Understand what buy/sell/hold signals mean",
        icon="\U0001f6a6",
        badge="\U0001f4a1",
        steps=[
            LearningStep(
                id="run_first_signal",
                title="Run Your First Signal",
                description="See what our AI thinks about a stock",
                action_text="Go to Signals page, select a ticker, and click 'Analyze Signal'",
                page_link="pages/7_Signals.py",
            ),
            LearningStep(
                id="understand_breakdown",
                title="Understand the Breakdown",
                description="Learn what Technical Analysis, Model Consensus, and Sentiment mean",
                action_text="Look at the Signal Breakdown section — each card shows a different analysis method",
            ),
            LearningStep(
                id="check_confidence",
                title="Check the Confidence Level",
                description="Higher confidence means more agreement between different analysis methods",
                action_text="Notice the confidence gauge — above 70% means strong agreement, below 40% means mixed signals",
            ),
        ],
    ),
    LearningModule(
        id="diversification",
        title="Diversification 101",
        description="Don't put all your eggs in one basket",
        icon="\U0001f95a",
        badge="\U0001f30d",
        steps=[
            LearningStep(
                id="check_allocation",
                title="Check Your Allocation",
                description="See how your money is spread across stocks",
                action_text="Go to Portfolio and look at the Allocation pie chart",
                page_link="pages/6_Portfolio.py",
            ),
            LearningStep(
                id="add_different_market",
                title="Add a Stock from a Different Market",
                description="If you only have US stocks, try adding an Indian stock (e.g., RELIANCE.NS) or vice versa",
                action_text="Add a stock from a different country/sector to your portfolio",
                page_link="pages/6_Portfolio.py",
            ),
            LearningStep(
                id="review_health",
                title="Review Portfolio Health",
                description="Check the Daily Briefing for concentration warnings",
                action_text="Go to Daily Briefing and look at the Portfolio Health section",
                page_link="pages/8_Daily_Briefing.py",
            ),
        ],
    ),
    LearningModule(
        id="technical_analysis",
        title="Technical Analysis 101",
        description="What RSI, MACD, and Bollinger Bands actually mean",
        icon="\U0001f4c9",
        badge="\U0001f9e0",
        steps=[
            LearningStep(
                id="learn_rsi",
                title="Learn About RSI",
                description=(
                    "RSI (Relative Strength Index) measures if a stock is overbought or oversold. "
                    "Below 30 = oversold (might bounce up). Above 70 = overbought (might pull back)."
                ),
                action_text="Run a signal for AAPL and find the RSI value in the Technical Analysis breakdown",
                page_link="pages/7_Signals.py",
            ),
            LearningStep(
                id="learn_macd",
                title="Learn About MACD",
                description=(
                    "MACD shows momentum direction. When the MACD line crosses above the signal line, "
                    "it's a bullish sign. When it crosses below, it's bearish."
                ),
                action_text="Look at the MACD value in the Technical Analysis card — is the histogram positive or negative?",
            ),
            LearningStep(
                id="learn_bollinger",
                title="Learn About Bollinger Bands",
                description=(
                    "Bollinger Bands show price range. When price is near the lower band, "
                    "it might be oversold. Near the upper band, it might be overbought."
                ),
                action_text="Check the BB Position in the signal breakdown — 0% = lower band, 100% = upper band",
            ),
        ],
    ),
    LearningModule(
        id="backtesting",
        title="Test Before You Invest",
        description="See how models would have performed in the past",
        icon="\U0001f52c",
        badge="\U0001f3af",
        steps=[
            LearningStep(
                id="run_backtest",
                title="Run a Backtest",
                description="See how well a forecasting model predicts historical prices",
                action_text="Go to Backtesting, select a stock and model, then run the backtest",
                page_link="pages/4_Backtesting.py",
            ),
            LearningStep(
                id="compare_models",
                title="Compare Different Models",
                description="Not all models perform equally — some are better for certain stocks",
                action_text="Go to Model Comparison to see how different models stack up",
                page_link="pages/3_Model_Comparison.py",
            ),
            LearningStep(
                id="understand_metrics",
                title="Understand the Metrics",
                description="MAE = average error. RMSE = penalizes big mistakes. Lower is better for both.",
                action_text="Look at the backtest results — which model has the lowest MAE?",
            ),
        ],
    ),
    LearningModule(
        id="advanced_features",
        title="Advanced Features",
        description="Sentiment analysis, ensemble models, and AI coaching",
        icon="\U0001f9d9",
        badge="\U0001f451",
        steps=[
            LearningStep(
                id="try_sentiment",
                title="Try Sentiment Analysis",
                description="See what the news says about a stock using FinBERT AI",
                action_text="Go to Sentiment page to analyze news headlines for your stock",
                page_link="pages/5_Sentiment.py",
            ),
            LearningStep(
                id="try_ensemble",
                title="Use the Ensemble Model",
                description="The ensemble combines multiple models for more reliable predictions",
                action_text="Run a forecast with the 'ensemble' model selected in the sidebar",
                page_link="pages/2_Forecast.py",
            ),
            LearningStep(
                id="talk_to_coach",
                title="Talk to Your AI Coach",
                description="Get personalized advice from the AI Portfolio Coach",
                action_text="Go to AI Coach, enter your API key, and ask 'Analyze my portfolio'",
                page_link="pages/9_AI_Coach.py",
            ),
        ],
    ),
    LearningModule(
        id="portfolio_management",
        title="Portfolio Management",
        description="Review, rebalance, and grow your portfolio",
        icon="\U0001f4bc",
        badge="\U0001f3c6",
        steps=[
            LearningStep(
                id="daily_briefing_habit",
                title="Make It a Habit",
                description="Check your Daily Briefing regularly to stay on top of your investments",
                action_text="Visit the Daily Briefing page and review all sections",
                page_link="pages/8_Daily_Briefing.py",
            ),
            LearningStep(
                id="review_signals_regularly",
                title="Review Signals Before Acting",
                description="Always check signals before buying or selling — don't act on impulse",
                action_text="Run 'Scan All Holdings' on the Signals page to see all your portfolio signals",
                page_link="pages/7_Signals.py",
            ),
            LearningStep(
                id="continuous_learning",
                title="Keep Learning!",
                description=(
                    "Investing is a journey. Keep exploring the app's features, "
                    "read about investing strategies, and never invest money you can't afford to lose."
                ),
                action_text="You've completed the learning path! Keep using the app to grow your knowledge.",
            ),
        ],
    ),
]


def get_module(module_id: str) -> LearningModule | None:
    for m in MODULES:
        if m.id == module_id:
            return m
    return None


def get_all_step_ids() -> list[tuple[str, str]]:
    """Return all (module_id, step_id) pairs."""
    result = []
    for m in MODULES:
        for s in m.steps:
            result.append((m.id, s.id))
    return result


def total_steps() -> int:
    return sum(len(m.steps) for m in MODULES)

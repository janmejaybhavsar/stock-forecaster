# Stock Forecaster — Portfolio Growth Coach

An intelligent stock forecasting platform that goes beyond predictions — it coaches you to grow your portfolio with actionable signals, daily briefings, and AI-powered advice.

## What Makes This Different

Most stock apps show charts and data. This one **coaches you**:

- **Signal Engine** — Composite buy/sell/hold signals combining technical analysis, ML model consensus, and news sentiment
- **Daily Briefing** — Personalized portfolio summary with action items, delivered at a glance
- **AI Coach** — Chat with your portfolio in plain English (powered by Groq/Gemini/OpenAI/Claude)
- **Learning Path** — 7-module guided journey from beginner to confident investor
- **Smart Notifications** — Proactive alerts for price moves, concentration risk, earnings dates, and milestones

100% free and open-source. No paid APIs required.

## Features

### ML Forecasting (6 Models)
- ARIMA, XGBoost, LSTM, Transformer, Prophet, Ensemble
- Backtesting with equity curves and error metrics
- Model comparison across different stocks

### Signal Engine
- Technical indicators: RSI, MACD, Bollinger Bands, SMA crossovers, Stochastic
- Model consensus: run multiple models and aggregate predictions
- FinBERT sentiment analysis from news headlines
- Composite score mapped to Strong Buy / Buy / Hold / Sell / Strong Sell

### Portfolio Tracking
- Add holdings with shares and cost basis
- Live P&L with current prices from yfinance
- Allocation breakdown and concentration warnings
- International stock support (US, India, etc.)

### AI Portfolio Coach
- Multi-LLM support: Groq (free), Gemini (free), OpenAI, Anthropic
- No SDK dependencies — pure REST API calls via httpx
- Portfolio analysis, signal explanations, rebalancing suggestions
- Full chat interface with conversation history

## Quick Start

### Prerequisites
- Python 3.11+
- ~2GB disk space (for PyTorch CPU)

### Install & Run

```bash
git clone https://github.com/your-username/stock-forecaster.git
cd stock-forecaster
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Start API server
uvicorn src.api.app:create_app --factory --reload --port 8000

# In another terminal — start dashboard
streamlit run src/dashboard/app.py --server.port 8501
```

Open http://localhost:8501 in your browser.

### Docker

```bash
docker compose up --build
```

API: http://localhost:8000 | Dashboard: http://localhost:8501

## Project Structure

```
stock-forecaster/
├── config/             # Settings and environment config
├── src/
│   ├── api/            # FastAPI backend
│   │   └── routes/     # Auth, stocks, forecasts, signals, coach, portfolio
│   ├── auth/           # JWT authentication
│   ├── coach/          # AI portfolio coach (multi-LLM)
│   ├── dashboard/      # Streamlit frontend (10 pages)
│   ├── data_layer/     # Data provider abstraction (yfinance)
│   ├── database/       # SQLite repositories
│   ├── features/       # Technical indicator computation
│   ├── learning/       # Learning path module definitions
│   ├── models/         # ML model implementations
│   ├── signals/        # Signal engine, rules, notifications
│   └── backtesting/    # Walk-forward backtesting engine
├── tests/              # pytest test suite (62 tests)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Create account |
| `/api/v1/auth/login` | POST | Get JWT token |
| `/api/v1/stocks/{ticker}/history` | GET | Price history |
| `/api/v1/forecasts/{ticker}` | GET | ML forecast |
| `/api/v1/signals/{ticker}` | GET | Buy/sell/hold signal |
| `/api/v1/signals/portfolio/all` | GET | Signals for all holdings |
| `/api/v1/portfolio/` | GET | Portfolio with live P&L |
| `/api/v1/portfolio/holdings` | POST | Add holding |
| `/api/v1/coach/analyze` | POST | AI portfolio analysis |
| `/api/v1/coach/ask` | POST | Chat with AI coach |
| `/health` | GET | Health check |

Full interactive docs at `/docs` when the API is running.

## Running Tests

```bash
pytest tests/ -v
```

## Tech Stack

- **Backend:** FastAPI, SQLite, JWT auth
- **Frontend:** Streamlit (multipage app)
- **ML:** PyTorch, XGBoost, statsmodels, Prophet, Transformers
- **Data:** yfinance, pandas, pandas-ta
- **AI Coach:** Groq / Gemini / OpenAI / Anthropic (via REST API)
- **NLP:** FinBERT for sentiment analysis

## License

MIT

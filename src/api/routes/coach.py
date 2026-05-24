from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import get_current_user

router = APIRouter(tags=["coach"])


class AskRequest(BaseModel):
    question: str
    provider: str | None = None
    api_key: str | None = None
    chat_history: list[dict] | None = None


class AnalyzeRequest(BaseModel):
    provider: str | None = None
    api_key: str | None = None


class ExplainRequest(BaseModel):
    ticker: str
    provider: str | None = None
    api_key: str | None = None


@router.post("/analyze")
def analyze_portfolio(req: AnalyzeRequest, user: dict = Depends(get_current_user)):
    """Get AI analysis of the user's portfolio."""
    from src.coach.coach import PortfolioCoach
    from src.database.repositories import HoldingsRepository

    repo = HoldingsRepository()
    holdings = repo.list_by_user(user["id"])
    if not holdings:
        raise HTTPException(400, "No holdings in portfolio")

    # Get enriched portfolio data
    try:
        # Use internal API call to get enriched holdings
        from src.api.routes.portfolio import _enrich_holdings
        enriched, summary = _enrich_holdings(holdings)
    except Exception as e:
        raise HTTPException(500, f"Failed to load portfolio: {e}")

    try:
        coach = PortfolioCoach(provider=req.provider, api_key=req.api_key)
        response = coach.analyze_portfolio(enriched, summary)
        return {"response": response, "provider": coach.client.name}
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Coach error: {e}")


@router.post("/explain")
def explain_signal(req: ExplainRequest, user: dict = Depends(get_current_user)):
    """Get AI explanation of a signal for a specific ticker."""
    from dataclasses import asdict
    from src.coach.coach import PortfolioCoach
    from src.signals.engine import generate_signal

    try:
        signal = generate_signal(req.ticker.upper().strip(), horizon=5, include_sentiment=False)
        signal_data = asdict(signal)
    except Exception as e:
        raise HTTPException(500, f"Signal generation failed: {e}")

    try:
        coach = PortfolioCoach(provider=req.provider, api_key=req.api_key)
        response = coach.explain_signal(signal_data)
        return {"response": response, "signal": signal_data, "provider": coach.client.name}
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Coach error: {e}")


@router.post("/ask")
def ask_question(req: AskRequest, user: dict = Depends(get_current_user)):
    """Ask the AI coach a freeform question."""
    from src.coach.coach import PortfolioCoach
    from src.database.repositories import HoldingsRepository

    repo = HoldingsRepository()
    holdings = repo.list_by_user(user["id"])

    enriched = None
    summary = None
    if holdings:
        try:
            from src.api.routes.portfolio import _enrich_holdings
            enriched, summary = _enrich_holdings(holdings)
        except Exception:
            pass

    try:
        coach = PortfolioCoach(provider=req.provider, api_key=req.api_key)
        response = coach.answer_question(
            question=req.question,
            holdings=enriched,
            summary=summary,
            chat_history=req.chat_history,
        )
        return {"response": response, "provider": coach.client.name}
    except RuntimeError as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(400, str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Coach error: {e}")

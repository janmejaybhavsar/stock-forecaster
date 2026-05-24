import logging
from datetime import datetime, timedelta

import feedparser

logger = logging.getLogger(__name__)


class SentimentAnalyzer:

    def __init__(self):
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from transformers import pipeline
            self._pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
            )
        return self._pipeline

    def fetch_headlines(self, ticker: str, days: int = 14) -> list[dict]:
        url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        try:
            feed = feedparser.parse(url)
            headlines = []
            cutoff = datetime.now() - timedelta(days=days)
            for entry in feed.entries[:50]:
                published = datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") and entry.published_parsed else datetime.now()
                if published >= cutoff:
                    headlines.append({
                        "headline": entry.title,
                        "published": published.isoformat(),
                        "source": entry.get("source", {}).get("title", ""),
                    })
            return headlines
        except Exception as e:
            logger.warning(f"Failed to fetch headlines for {ticker}: {e}")
            return []

    def score_headlines(self, headlines: list[dict]) -> list[dict]:
        if not headlines:
            return []

        pipe = self._get_pipeline()
        texts = [h["headline"][:512] for h in headlines]
        results = pipe(texts, batch_size=16, truncation=True)

        scored = []
        for headline, result in zip(headlines, results):
            scored.append({
                **headline,
                "sentiment": result["label"].lower(),
                "score": round(result["score"], 4),
            })
        return scored

    def get_daily_sentiment(self, ticker: str, days: int = 30) -> dict[str, dict]:
        headlines = self.fetch_headlines(ticker, days)
        scored = self.score_headlines(headlines)

        daily: dict[str, list] = {}
        for item in scored:
            day = item["published"][:10]
            daily.setdefault(day, []).append(item)

        aggregated = {}
        for day, items in daily.items():
            pos_scores = [i["score"] for i in items if i["sentiment"] == "positive"]
            neg_scores = [i["score"] for i in items if i["sentiment"] == "negative"]
            aggregated[day] = {
                "mean_positive": sum(pos_scores) / len(pos_scores) if pos_scores else 0,
                "mean_negative": sum(neg_scores) / len(neg_scores) if neg_scores else 0,
                "headline_count": len(items),
                "net_sentiment": (sum(pos_scores) - sum(neg_scores)) / len(items),
            }
        return aggregated

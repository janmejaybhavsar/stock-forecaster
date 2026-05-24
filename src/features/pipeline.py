import pandas as pd

from src.features.calendar_features import add_calendar_features
from src.features.technical import add_technical_indicators


class FeaturePipeline:

    def build(
        self,
        ticker: str,
        raw_df: pd.DataFrame,
        include_sentiment: bool = False,
    ) -> pd.DataFrame:
        df = raw_df.copy()
        df = add_technical_indicators(df)
        df = add_calendar_features(df)

        if include_sentiment:
            try:
                from src.features.sentiment import SentimentAnalyzer
                analyzer = SentimentAnalyzer()
                daily_sentiment = analyzer.get_daily_sentiment(ticker, days=60)
                sent_df = pd.DataFrame.from_dict(daily_sentiment, orient="index")
                sent_df.index = pd.to_datetime(sent_df.index)
                df = df.join(sent_df, how="left")
                for col in ["mean_positive", "mean_negative", "headline_count", "net_sentiment"]:
                    if col in df.columns:
                        df[col] = df[col].fillna(0)
            except Exception:
                pass

        df = df.dropna()
        return df

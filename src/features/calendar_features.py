import pandas as pd


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    idx = pd.to_datetime(df.index)
    df["day_of_week"] = idx.dayofweek
    df["month"] = idx.month
    df["quarter"] = idx.quarter
    df["is_month_start"] = idx.is_month_start.astype(int)
    df["is_month_end"] = idx.is_month_end.astype(int)
    df["is_quarter_end"] = idx.is_quarter_end.astype(int)
    return df

import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    for window in [10, 20, 50, 200]:
        sma = SMAIndicator(close, window=window)
        df[f"sma_{window}"] = sma.sma_indicator()

    for window in [12, 26]:
        ema = EMAIndicator(close, window=window)
        df[f"ema_{window}"] = ema.ema_indicator()

    rsi = RSIIndicator(close, window=14)
    df["rsi_14"] = rsi.rsi()

    macd = MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    bb = BollingerBands(close, window=20)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()

    atr = AverageTrueRange(high, low, close, window=14)
    df["atr_14"] = atr.average_true_range()

    obv = OnBalanceVolumeIndicator(close, volume)
    df["obv"] = obv.on_balance_volume()

    stoch = StochasticOscillator(high, low, close, window=14, smooth_window=3)
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    df["return_1d"] = close.pct_change(1)
    df["return_5d"] = close.pct_change(5)
    df["return_21d"] = close.pct_change(21)

    df["volatility_21d"] = close.pct_change().rolling(21).std()

    df["volume_norm"] = volume / volume.rolling(20).mean()

    return df

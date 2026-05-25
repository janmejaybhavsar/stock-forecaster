"""
Ticker validation against known exchange suffixes and format rules.
Prevents injection of invalid/malicious ticker strings into API calls.
"""

import re

# Known exchange suffixes supported by yfinance
VALID_SUFFIXES = {
    "",       # US (NYSE, NASDAQ) — no suffix
    ".NS",    # NSE India
    ".BO",    # BSE India
    ".L",     # London Stock Exchange
    ".T",     # Tokyo Stock Exchange
    ".HK",    # Hong Kong
    ".SS",    # Shanghai
    ".SZ",    # Shenzhen
    ".AX",    # Australian Securities Exchange
    ".TO",    # Toronto Stock Exchange
    ".V",     # TSX Venture
    ".PA",    # Euronext Paris
    ".DE",    # Deutsche Börse (XETRA)
    ".F",     # Frankfurt
    ".MI",    # Borsa Italiana
    ".AS",    # Euronext Amsterdam
    ".BR",    # Euronext Brussels
    ".LS",    # Euronext Lisbon
    ".MC",    # Bolsa de Madrid
    ".SW",    # SIX Swiss Exchange
    ".ST",    # Nasdaq Stockholm
    ".CO",    # Nasdaq Copenhagen
    ".HE",    # Nasdaq Helsinki
    ".OL",    # Oslo Børs
    ".IS",    # Nasdaq Iceland
    ".KS",    # Korea Stock Exchange
    ".KQ",    # KOSDAQ
    ".TW",    # Taiwan Stock Exchange
    ".SI",    # Singapore Exchange
    ".JK",    # Indonesia Stock Exchange
    ".KL",    # Bursa Malaysia
    ".BK",    # Stock Exchange of Thailand
    ".SA",    # B3 (Brazil)
    ".MX",    # Bolsa Mexicana
    ".BA",    # Buenos Aires
    ".SN",    # Santiago
    ".CR",    # Crypto (via yfinance)
}

# Ticker format: 1-10 alphanumeric chars (may include hyphens/dots for special tickers),
# optionally followed by a dot and a 1-3 char exchange suffix
_TICKER_PATTERN = re.compile(r"^[A-Z0-9\-\.]{1,10}(\.[A-Z]{1,3})?$", re.IGNORECASE)


def validate_ticker(ticker: str) -> tuple[bool, str]:
    """
    Validate a ticker symbol.

    Returns:
        (is_valid, error_message) — error_message is empty if valid.
    """
    if not ticker or not ticker.strip():
        return False, "Ticker cannot be empty"

    ticker = ticker.strip().upper()

    if len(ticker) > 15:
        return False, "Ticker too long (max 15 characters)"

    if not _TICKER_PATTERN.match(ticker):
        return False, "Invalid ticker format — must be alphanumeric with optional exchange suffix"

    # Check exchange suffix
    if "." in ticker:
        # Find the last dot to get the suffix
        last_dot = ticker.rfind(".")
        suffix = ticker[last_dot:]
        base = ticker[:last_dot]
        if suffix.upper() not in VALID_SUFFIXES:
            return False, f"Unknown exchange suffix '{suffix}'"
        if not base:
            return False, "Ticker base cannot be empty"
    else:
        base = ticker

    # Base symbol sanity check (at least 1 alpha char)
    if not any(c.isalpha() for c in base):
        return False, "Ticker must contain at least one letter"

    return True, ""


def sanitize_ticker(ticker: str) -> str:
    """
    Sanitize and normalize a ticker string.
    Returns uppercased, stripped ticker or raises ValueError if invalid.
    """
    ticker = ticker.strip().upper()
    is_valid, error = validate_ticker(ticker)
    if not is_valid:
        raise ValueError(error)
    return ticker

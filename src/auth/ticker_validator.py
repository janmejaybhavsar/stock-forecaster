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

# Ticker format aligned with API schemas: letters, numbers, dot, hyphen, caret.
_TICKER_PATTERN = re.compile(r"^[A-Z0-9\.\-\^]{1,20}$", re.IGNORECASE)


def validate_ticker(ticker: str) -> tuple[bool, str]:
    """
    Validate a ticker symbol.

    Returns:
        (is_valid, error_message) — error_message is empty if valid.
    """
    if not ticker or not ticker.strip():
        return False, "Ticker cannot be empty"

    ticker = ticker.strip().upper()

    if len(ticker) > 20:
        return False, "Ticker too long (max 20 characters)"

    if not _TICKER_PATTERN.match(ticker):
        return False, "Invalid ticker format — must be alphanumeric with optional exchange suffix"

    # Check exchange suffix only when it's a known suffix; otherwise keep dot(s) in base symbol
    base = ticker
    if "." in ticker:
        last_dot = ticker.rfind(".")
        suffix_candidate = ticker[last_dot:]
        base_candidate = ticker[:last_dot]
        if not base_candidate:
            return False, "Ticker base cannot be empty"
        if suffix_candidate.upper() in VALID_SUFFIXES:
            base = base_candidate

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

import streamlit as st

CURRENCY_SYMBOLS = {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥"}


def render_metric_cards(info: dict) -> None:
    cols = st.columns(4)

    price = info.get("current_price", 0)
    high_52 = info.get("fifty_two_week_high", 0)
    low_52 = info.get("fifty_two_week_low", 0)
    market_cap = info.get("market_cap", 0)
    currency = info.get("currency", "USD")
    sym = CURRENCY_SYMBOLS.get(currency, currency + " ")

    with cols[0]:
        st.metric("Current Price", f"{sym}{price:,.2f}")
    with cols[1]:
        st.metric("52W High", f"{sym}{high_52:,.2f}")
    with cols[2]:
        st.metric("52W Low", f"{sym}{low_52:,.2f}")
    with cols[3]:
        if market_cap > 1e12:
            cap_str = f"{sym}{market_cap / 1e12:.1f}T"
        elif market_cap > 1e9:
            cap_str = f"{sym}{market_cap / 1e9:.1f}B"
        else:
            cap_str = f"{sym}{market_cap / 1e6:.1f}M"
        st.metric("Market Cap", cap_str)

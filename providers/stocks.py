"""
Stock quotes provider for Pulse.
Uses yfinance (Yahoo Finance) — no API key required.
Runs synchronous yfinance calls in a thread pool to not block the event loop.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="pulse-stocks")

# Unicode sparkline characters (index 0 = lowest, 7 = highest)
SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _make_sparkline(prices: List[float], width: int = 7) -> str:
    """Build a Unicode sparkline string from a list of prices."""
    if not prices or len(prices) < 2:
        return "─" * width

    # Resample to `width` data points
    if len(prices) > width:
        step = len(prices) / width
        prices = [prices[int(i * step)] for i in range(width)]

    min_p = min(prices)
    max_p = max(prices)
    rng = max_p - min_p

    if rng == 0:
        return SPARK_CHARS[3] * len(prices)

    return "".join(
        SPARK_CHARS[min(7, int((p - min_p) / rng * 7))]
        for p in prices
    )


def _format_market_cap(cap: float) -> str:
    if cap >= 1e12:
        return f"${cap / 1e12:.2f}T"
    if cap >= 1e9:
        return f"${cap / 1e9:.1f}B"
    if cap >= 1e6:
        return f"${cap / 1e6:.1f}M"
    return f"${cap:,.0f}"


def _fetch_quotes_sync(tickers: List[str]) -> List[Dict[str, Any]]:
    """Synchronous fetch — run in thread pool."""
    try:
        import yfinance as yf
    except ImportError:
        return [{"ticker": t, "error": "yfinance not installed"} for t in tickers]

    results = []
    for sym in tickers:
        try:
            ticker = yf.Ticker(sym)
            info = ticker.fast_info

            current = float(getattr(info, "last_price", None) or 0)
            prev = float(getattr(info, "previous_close", None) or current)
            change = current - prev
            change_pct = (change / prev * 100) if prev else 0.0

            # 7-day price history for sparkline
            hist = ticker.history(period="7d", interval="1d")
            spark_prices = hist["Close"].tolist() if not hist.empty else []
            sparkline = _make_sparkline(spark_prices)

            # 52-week range — attribute name varies by yfinance version
            low_52 = float(
                getattr(info, "year_low", None)
                or getattr(info, "fifty_two_week_low", None)
                or 0
            )
            high_52 = float(
                getattr(info, "year_high", None)
                or getattr(info, "fifty_two_week_high", None)
                or 0
            )

            results.append({
                "ticker": sym,
                "price": current,
                "change": change,
                "change_pct": change_pct,
                "sparkline": sparkline,
                "market_cap": _format_market_cap(float(getattr(info, "market_cap", None) or 0)),
                "volume": int(getattr(info, "three_month_average_volume", None) or 0),
                "week_52_low": low_52,
                "week_52_high": high_52,
                "currency": getattr(info, "currency", "USD"),
            })
        except Exception as e:
            results.append({"ticker": sym, "error": str(e)})

    return results


async def fetch_quotes(tickers: List[str]) -> List[Dict[str, Any]]:
    """Async wrapper — runs yfinance in a thread executor."""
    if not tickers:
        return []
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_quotes_sync, tickers)

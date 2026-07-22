"""
NewsAPI headlines provider for Pulse.
Requires a free API key from https://newsapi.org/
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

NEWS_BASE = "https://newsapi.org/v2"

CATEGORIES = ["general", "technology", "business", "science", "health", "sports", "entertainment"]

CATEGORY_ICONS = {
    "general": "🌐",
    "technology": "💻",
    "business": "💼",
    "science": "🔬",
    "health": "🏥",
    "sports": "⚽",
    "entertainment": "🎬",
}


def _time_ago(pub_at: str) -> str:
    """Convert ISO timestamp to human-readable 'X ago'."""
    try:
        dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        total_secs = int(delta.total_seconds())
        if total_secs < 3600:
            return f"{total_secs // 60}m ago"
        if total_secs < 86400:
            return f"{total_secs // 3600}h ago"
        return f"{total_secs // 86400}d ago"
    except Exception:
        return ""


async def fetch_headlines(
    api_key: str,
    country: str = "us",
    category: str = "general",
    page_size: int = 25,
) -> Optional[List[Dict[str, Any]]]:
    """Fetch top headlines from NewsAPI."""
    if not api_key:
        return {"error": "no_key"}  # type: ignore[return-value]

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(
                f"{NEWS_BASE}/top-headlines",
                params={
                    "apiKey": api_key,
                    "country": country,
                    "category": category,
                    "pageSize": page_size,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        articles = _parse_articles(data, category)

        # NewsAPI free tier has very limited coverage for non-US countries.
        # Fall back to 'us' if the configured country returns nothing.
        if not articles and country.lower() != "us":
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp2 = await client.get(
                    f"{NEWS_BASE}/top-headlines",
                    params={
                        "apiKey": api_key,
                        "country": "us",
                        "category": category,
                        "pageSize": page_size,
                    },
                )
                resp2.raise_for_status()
                articles = _parse_articles(resp2.json(), category)
                # Mark articles so the widget can show a note
                for a in articles:
                    a["fallback_country"] = country

        return articles
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"error": "invalid_key"}  # type: ignore[return-value]
        return {"error": str(e)}  # type: ignore[return-value]
    except Exception as e:
        return {"error": str(e)}  # type: ignore[return-value]


def _parse_articles(data: dict, category: str) -> list:
    """Extract and clean article list from NewsAPI response."""
    articles = []
    for a in data.get("articles", []):
        title = a.get("title") or ""
        if not title or title == "[Removed]":
            continue
        articles.append({
            "title": title,
            "description": a.get("description") or "",
            "content": a.get("content") or "",
            "source": (a.get("source") or {}).get("name", "Unknown"),
            "author": a.get("author") or "",
            "url": a.get("url") or "",
            "time_ago": _time_ago(a.get("publishedAt") or ""),
            "category": category,
            "category_icon": CATEGORY_ICONS.get(category, "📰"),
            "fallback_country": "",
        })
    return articles

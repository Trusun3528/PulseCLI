"""
Hacker News provider for Pulse.
Uses the Algolia HN API — no API key required.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

HN_ALGOLIA = "https://hn.algolia.com/api/v1"
HN_ITEM_URL = "https://news.ycombinator.com/item?id="

STORY_TYPES = ["top", "new", "best", "ask", "show"]


def _extract_domain(url: str) -> str:
    """Extract the bare domain from a URL."""
    if not url:
        return "news.ycombinator.com"
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


async def fetch_stories(
    story_type: str = "top",
    limit: int = 30,
) -> Optional[List[Dict[str, Any]]]:
    """Fetch Hacker News stories via Algolia API."""
    story_type = story_type if story_type in STORY_TYPES else "top"

    tag_map = {
        "top": "front_page",
        "new": "story",
        "best": "front_page",
        "ask": "ask_hn",
        "show": "show_hn",
    }
    tag = tag_map.get(story_type, "front_page")

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(
                f"{HN_ALGOLIA}/search",
                params={
                    "tags": tag,
                    "hitsPerPage": limit,
                    "attributesToRetrieve": "objectID,title,url,author,points,num_comments,created_at",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        stories = []
        for hit in data.get("hits", []):
            obj_id = hit.get("objectID", "")
            stories.append({
                "title": hit.get("title") or "",
                "url": hit.get("url") or f"{HN_ITEM_URL}{obj_id}",
                "hn_url": f"{HN_ITEM_URL}{obj_id}",
                "score": hit.get("points") or 0,
                "comments": hit.get("num_comments") or 0,
                "author": hit.get("author") or "",
                "domain": _extract_domain(hit.get("url") or ""),
                "id": obj_id,
            })

        return stories

    except Exception as e:
        return {"error": str(e)}  # type: ignore[return-value]

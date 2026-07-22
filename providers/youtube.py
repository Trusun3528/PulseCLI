"""
YouTube Trending provider for Pulse.
Fetches trending videos using the YouTube Data API v3.
Requires an API key from Google Cloud Console.
"""

from typing import Any, Dict, List, Optional
import httpx

async def fetch_trending_videos(
    api_key: str,
    region_code: str = "US",
    limit: int = 25,
) -> Optional[List[Dict[str, Any]]]:
    """Fetch trending videos using YouTube Data API."""
    if not api_key:
        return {"error": "no_credentials"}  # type: ignore[return-value]

    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": limit,
        "key": api_key
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            videos = []
            for item in items:
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                
                videos.append({
                    "title": snippet.get("title", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "url": f"https://www.youtube.com/watch?v={item.get('id', '')}"
                })
            return videos
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            return [{"error": "Invalid API Key or Bad Request"}]
        elif e.response.status_code == 403:
            return [{"error": "API Key is invalid or quota exceeded"}]
        return [{"error": f"HTTP Error: {e.response.status_code}"}]
    except Exception as e:
        return [{"error": f"Error: {str(e)}"}]

def _format_count(count: int) -> str:
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)

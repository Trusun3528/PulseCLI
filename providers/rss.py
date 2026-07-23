"""
RSS Feed provider.
Fetches and parses an RSS or Atom feed using feedparser.
"""

import feedparser
import requests
from typing import List, Dict, Any

def get_rss_feed(url: str, limit: int = 25) -> Dict[str, Any]:
    """
    Fetches and parses the given RSS feed URL.
    Returns:
        Dict: {"title": str, "articles": List[Dict], "error": Optional[str]}
    """
    if not url:
        return {"title": "No URL", "articles": [], "error": "No RSS URL configured."}
        
    try:
        # Fetch using requests with a browser User-Agent to prevent 403/429 blocks (like Reddit)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        
        feed = feedparser.parse(res.text)
        
        if feed.bozo and hasattr(feed, 'bozo_exception'):
            # It might still have parsed some entries despite a bozo error
            if not feed.entries:
                return {"title": "Error", "articles": [], "error": f"Failed to parse feed: {feed.bozo_exception}"}
                
        feed_title = feed.feed.get("title", "RSS Feed")
        
        articles = []
        for entry in feed.entries[:limit]:
            title = entry.get("title", "No Title")
            link = entry.get("link", "")
            
            # Try to get published date
            published = entry.get("published", "")
            if not published:
                published = entry.get("updated", "Unknown Date")
                
            articles.append({
                "title": title,
                "link": link,
                "published": published
            })
            
        return {"title": feed_title, "articles": articles, "error": None}
    except requests.exceptions.RequestException as e:
        # Check for specific HTTP errors
        error_msg = str(e)
        if "429" in error_msg:
            error_msg = "429 Too Many Requests (Site is blocking access)"
        elif "403" in error_msg:
            error_msg = "403 Forbidden (Site is blocking access)"
            
        return {"title": "Error", "articles": [], "error": error_msg}
    except Exception as e:
        return {"title": "Error", "articles": [], "error": str(e)}

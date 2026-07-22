"""
Reddit posts provider for Pulse.
Uses PRAW with app-only OAuth (client credentials flow).
No user login required — just a Reddit app client_id + client_secret.

Get free credentials in ~30 seconds:
  1. Go to https://www.reddit.com/prefs/apps
  2. Click "Create App" at the bottom
  3. Choose "script" type, any name, redirect URI: http://localhost
  4. Copy the client_id (under the app name) and client_secret
"""

from typing import Any, Dict, List, Optional

SORT_OPTIONS = ["hot", "new", "top", "rising"]


def _format_score(score: int) -> str:
    if score >= 1_000_000:
        return f"{score / 1_000_000:.1f}M"
    if score >= 1000:
        return f"{score / 1000:.1f}k"
    return str(score)


async def fetch_posts(
    subreddit: str,
    sort: str = "hot",
    limit: int = 25,
    client_id: str = "",
    client_secret: str = "",
    user_agent: str = "pulse-cli:v1.0",
) -> Optional[List[Dict[str, Any]]]:
    """Fetch posts using PRAW (requires client_id + client_secret)."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    if not client_id or not client_secret:
        return {"error": "no_credentials"}  # type: ignore[return-value]

    sort = sort if sort in SORT_OPTIONS else "hot"

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(
            pool, _fetch_praw, subreddit, sort, limit, client_id, client_secret, user_agent
        )


def _fetch_praw(
    subreddit: str,
    sort: str,
    limit: int,
    client_id: str,
    client_secret: str,
    user_agent: str,
) -> List[Dict[str, Any]]:
    try:
        import praw

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        sub = reddit.subreddit(subreddit)

        sort_fn = {
            "hot": sub.hot,
            "new": sub.new,
            "top": sub.top,
            "rising": sub.rising,
        }.get(sort, sub.hot)

        posts = []
        for p in sort_fn(limit=limit):
            raw_score = p.score
            posts.append({
                "title": p.title,
                "subreddit": p.subreddit.display_name,
                "author": str(p.author) if p.author else "[deleted]",
                "score": _format_score(raw_score),
                "raw_score": raw_score,
                "num_comments": p.num_comments,
                "url": p.url,
                "permalink": f"https://reddit.com{p.permalink}",
                "flair": p.link_flair_text or "",
                "is_self": p.is_self,
                "selftext": (p.selftext or "")[:600],
                "domain": p.domain,
                "is_nsfw": p.over_18,
                "awards": p.total_awards_received,
            })
        return posts

    except Exception as e:
        err = str(e).lower()
        if "received 403" in err or "forbidden" in err:
            return [{"error": f"r/{subreddit} is private or forbidden"}]
        if "received 404" in err or "banned" in err:
            return [{"error": f"r/{subreddit} not found or banned"}]
        return [{"error": str(e)}]

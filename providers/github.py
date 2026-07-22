"""
GitHub Trending repositories provider for Pulse.
Scrapes the GitHub trending page — no API key required.
"""

from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

GITHUB_TRENDING_URL = "https://github.com/trending"

LANGUAGES = [
    "", "Python", "JavaScript", "TypeScript", "Go", "Rust",
    "Java", "C++", "C", "Ruby", "Swift", "Kotlin", "Shell",
    "HTML", "CSS", "Vue", "C#", "PHP", "Scala", "Dart",
]

SINCE_OPTIONS = ["daily", "weekly", "monthly"]

# Language badge colors (approximate terminal colors)
LANG_COLORS: Dict[str, str] = {
    "python": "#3572A5",
    "javascript": "#f1e05a",
    "typescript": "#3178c6",
    "go": "#00ADD8",
    "rust": "#dea584",
    "java": "#b07219",
    "c++": "#f34b7d",
    "c": "#555555",
    "ruby": "#701516",
    "swift": "#F05138",
    "kotlin": "#A97BFF",
    "shell": "#89e051",
    "html": "#e34c26",
    "css": "#563d7c",
    "vue": "#41b883",
    "c#": "#178600",
    "php": "#4F5D95",
    "scala": "#c22d40",
    "dart": "#00B4AB",
}


def _parse_number(text: str) -> str:
    """Clean up a number string scraped from GitHub."""
    return text.strip().replace(",", "").replace("\n", "").strip()


async def fetch_trending(
    language: str = "",
    since: str = "daily",
) -> Optional[List[Dict[str, Any]]]:
    """Scrape GitHub trending repositories."""
    since = since if since in SINCE_OPTIONS else "daily"

    url = GITHUB_TRENDING_URL
    if language:
        slug = language.lower().replace(" ", "-").replace("#", "%23")
        url = f"{GITHUB_TRENDING_URL}/{slug}"

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                params={"since": since},
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 pulse-cli/1.0",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        repos = []

        for article in soup.find_all("article", class_="Box-row"):
            try:
                # Repo full name
                h2 = article.find("h2")
                if not h2:
                    continue
                raw_name = h2.get_text(separator="/", strip=True)
                # Clean up extra whitespace/newlines
                parts = [p.strip() for p in raw_name.split("/") if p.strip()]
                full_name = "/".join(parts[-2:]) if len(parts) >= 2 else raw_name.strip()

                # Description
                desc_el = article.find("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                # Programming language
                lang_el = article.find("span", itemprop="programmingLanguage")
                lang_name = lang_el.get_text(strip=True) if lang_el else ""
                lang_color = LANG_COLORS.get(lang_name.lower(), "#888888")

                # Stars (link to /stargazers)
                star_els = article.find_all("a", href=lambda h: h and "/stargazers" in str(h))
                stars = _parse_number(star_els[0].get_text()) if star_els else "0"

                # Forks
                fork_els = article.find_all("a", href=lambda h: h and "/forks" in str(h))
                forks = _parse_number(fork_els[0].get_text()) if fork_els else "0"

                # Stars this period
                today_el = article.find("span", class_=lambda c: c and "float-sm-right" in c)
                stars_period = today_el.get_text(strip=True) if today_el else ""

                repos.append({
                    "name": full_name,
                    "description": description,
                    "language": lang_name,
                    "lang_color": lang_color,
                    "stars": stars,
                    "forks": forks,
                    "stars_period": stars_period,
                    "url": f"https://github.com/{full_name}",
                    "since": since,
                })
            except Exception:
                continue

        if not repos:
            return {"error": "No repositories found. GitHub may have changed its page structure."}  # type: ignore[return-value]

        return repos

    except Exception as e:
        return {"error": str(e)}  # type: ignore[return-value]

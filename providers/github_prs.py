import httpx
from typing import Any, Dict, List

async def fetch_github_prs(username: str, token: str = "") -> List[Dict[str, Any]]:
    """Fetch open PRs for a specific user from GitHub."""
    if not username:
        return [{"error": "GitHub username not configured. Press S for Settings."}]
        
    url = f"https://api.github.com/search/issues?q=is:pr+is:open+author:{username}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 403:
                return [{"error": "GitHub API rate limit exceeded. Add a Personal Access Token in Settings."}]
            
            resp.raise_for_status()
            data = resp.json()
            
            prs = []
            for item in data.get("items", [])[:30]:
                # repository_url looks like https://api.github.com/repos/owner/repo
                repo_url = item.get("repository_url", "")
                repo_name = repo_url.split("repos/")[-1] if "repos/" in repo_url else ""
                
                prs.append({
                    "title": item.get("title", ""),
                    "repo": repo_name,
                    "url": item.get("html_url", ""),
                    "created_at": item.get("created_at", "")[:10],
                    "state": item.get("state", "open")
                })
            return prs

    except Exception as e:
        return [{"error": str(e)}]

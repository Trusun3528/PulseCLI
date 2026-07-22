import httpx
from typing import Any, Dict, List

async def fetch_trending_models(limit: int = 25) -> List[Dict[str, Any]]:
    """Fetch trending models from Hugging Face."""
    url = f"https://huggingface.co/api/models?sort=trendingScore&limit={limit}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            models = []
            for item in data:
                models.append({
                    "id": item.get("id", ""),
                    "author": item.get("author", ""),
                    "downloads": item.get("downloads", 0),
                    "pipeline_tag": item.get("pipeline_tag", ""),
                    "url": f"https://huggingface.co/{item.get('id', '')}"
                })
            return models
    except Exception as e:
        return [{"error": str(e)}]

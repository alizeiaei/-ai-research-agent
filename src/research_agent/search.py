import asyncio
from urllib.parse import urlsplit

import httpx

from research_agent.models import SearchResult


class SearchError(RuntimeError):
    """Search provider failure."""


class BraveSearchClient:
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        if not api_key.strip():
            raise ValueError("BRAVE_API_KEY is required")
        self.api_key = api_key
        self.client = client

    async def search(self, query: str, count: int = 10) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("Query cannot be empty")
        if not 1 <= count <= 20:
            raise ValueError("Count must be between 1 and 20")

        async def request(client: httpx.AsyncClient) -> dict:
            for attempt in range(3):
                try:
                    response = await client.get(
                        self.BASE_URL,
                        params={"q": query, "count": count},
                        headers={"Accept": "application/json", "X-Subscription-Token": self.api_key},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, dict):
                        raise SearchError("Invalid search response")
                    return payload
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                    retryable = not isinstance(exc, httpx.HTTPStatusError) or (
                        exc.response.status_code in (429, 500, 502, 503, 504)
                    )
                    if not retryable or attempt == 2:
                        raise SearchError(f"Search failed: {exc}") from exc
                    await asyncio.sleep(0.25 * (2**attempt))
                except ValueError as exc:
                    raise SearchError("Invalid JSON from search provider") from exc
            raise SearchError("Search exhausted retries")

        if self.client is None:
            async with httpx.AsyncClient(timeout=15) as client:
                payload = await request(client)
        else:
            payload = await request(self.client)

        found: list[SearchResult] = []
        seen: set[str] = set()
        for item in payload.get("web", {}).get("results", []):
            if not isinstance(item, dict):
                continue
            try:
                url = item["url"]
                title = item["title"]
                host = urlsplit(url).hostname or "Unknown"
                source = (item.get("profile") or {}).get("name") or host
                result = SearchResult(
                    title=title, url=url, source=source, snippet=item.get("description") or ""
                )
            except (KeyError, TypeError, ValueError):
                continue
            canonical = str(result.url).rstrip("/").lower()
            if canonical not in seen:
                seen.add(canonical)
                found.append(result)
        return found

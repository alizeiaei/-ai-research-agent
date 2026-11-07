import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from research_agent.models import SearchResult


class SearchError(RuntimeError):
    """Search provider failure."""


class SearchProvider(Protocol):
    async def search(self, query: str, count: int = 10) -> list[SearchResult]: ...


TRACKING_QUERY_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def canonicalize_url(url: str) -> str:
    """Normalize common equivalent URL forms for duplicate detection."""
    parts = urlsplit(url)
    hostname = (parts.hostname or "").lower()
    port = parts.port
    if port and not ((parts.scheme.lower() == "http" and port == 80) or (parts.scheme.lower() == "https" and port == 443)):
        hostname = f"{hostname}:{port}"

    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_PARAMETERS
        ),
        doseq=True,
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), hostname, path, query, ""))


def retry_delay(response: httpx.Response | None, fallback: float) -> float:
    """Return a bounded Retry-After delay, falling back when the header is unusable."""
    if response is None or not (value := response.headers.get("Retry-After")):
        return fallback
    try:
        return min(max(float(value), 0.0), 60.0)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=UTC)
            return min(max((retry_at - datetime.now(UTC)).total_seconds(), 0.0), 60.0)
        except (TypeError, ValueError, OverflowError):
            return fallback


class BraveSearchClient:
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(
        self,
        api_key: str,
        client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        if not api_key.strip():
            raise ValueError("BRAVE_API_KEY is required")
        self.api_key = api_key
        self.client = client
        self.sleep = sleep

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
                    response = exc.response if isinstance(exc, httpx.HTTPStatusError) else None
                    await self.sleep(retry_delay(response, 0.25 * (2**attempt)))
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
        web = payload.get("web")
        if web is None:
            return []
        if not isinstance(web, dict) or not isinstance(web.get("results", []), list):
            raise SearchError("Invalid search response structure")

        for item in web.get("results", []):
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
            canonical = canonicalize_url(str(result.url))
            if canonical not in seen:
                seen.add(canonical)
                found.append(result)
        return found

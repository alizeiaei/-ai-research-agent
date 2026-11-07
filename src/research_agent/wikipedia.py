import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from research_agent.models import SearchResult
from research_agent.search import SearchError

LANGUAGE_PATTERN = re.compile(r"[a-z]{2,12}(?:-[a-z0-9]{1,8})*")
DEFAULT_USER_AGENT = "AIResearchAgent/0.1 (https://github.com/alizeiaei/-ai-research-agent)"


class WikipediaSearchProvider:
    """Search Wikipedia through the public MediaWiki API without an API key."""

    def __init__(
        self,
        language: str = "en",
        client: httpx.AsyncClient | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        language = language.strip().lower()
        if not LANGUAGE_PATTERN.fullmatch(language):
            raise ValueError("Wikipedia language must be a valid language code such as 'en' or 'fa'")
        if not user_agent.strip():
            raise ValueError("Wikipedia user agent cannot be empty")
        self.language = language
        self.client = client
        self.user_agent = user_agent

    @property
    def api_url(self) -> str:
        return f"https://{self.language}.wikipedia.org/w/api.php"

    async def search(self, query: str, count: int = 10) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("Query cannot be empty")
        if not 1 <= count <= 20:
            raise ValueError("Count must be between 1 and 20")

        async def request(client: httpx.AsyncClient) -> dict:
            try:
                response = await client.get(
                    self.api_url,
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "srlimit": count,
                        "format": "json",
                        "utf8": 1,
                    },
                    headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                )
                response.raise_for_status()
                payload = response.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                raise SearchError(f"Wikipedia search failed: {exc}") from exc
            except ValueError as exc:
                raise SearchError("Invalid JSON from Wikipedia") from exc
            if not isinstance(payload, dict):
                raise SearchError("Invalid Wikipedia response")
            return payload

        if self.client is None:
            async with httpx.AsyncClient(timeout=15) as client:
                payload = await request(client)
        else:
            payload = await request(self.client)

        query_section = payload.get("query")
        if query_section is None:
            return []
        if not isinstance(query_section, dict) or not isinstance(query_section.get("search"), list):
            raise SearchError("Invalid Wikipedia response structure")

        results = []
        for item in query_section["search"]:
            if not isinstance(item, dict):
                continue
            try:
                title = item["title"]
                snippet = BeautifulSoup(item.get("snippet") or "", "html.parser").get_text(
                    " ", strip=True
                )
                results.append(
                    SearchResult(
                        title=title,
                        url=f"https://{self.language}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                        source=f"Wikipedia ({self.language})",
                        snippet=snippet,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return results

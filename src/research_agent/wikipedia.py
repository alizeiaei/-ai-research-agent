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

    async def _request(self, client: httpx.AsyncClient, params: dict) -> dict:
        try:
            response = await client.get(
                self.api_url,
                params={**params, "format": "json", "utf8": 1},
                headers={"User-Agent": self.user_agent, "Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            raise SearchError(f"Wikipedia request failed: {exc}") from exc
        except ValueError as exc:
            raise SearchError("Invalid JSON from Wikipedia") from exc
        if not isinstance(payload, dict):
            raise SearchError("Invalid Wikipedia response")
        return payload

    async def _enrich_with_extracts(
        self, client: httpx.AsyncClient, results: list[SearchResult]
    ) -> list[SearchResult]:
        if not results:
            return results
        try:
            payload = await self._request(
                client,
                {
                    "action": "query",
                    "prop": "extracts|pageprops",
                    "exintro": 1,
                    "explaintext": 1,
                    "redirects": 1,
                    "titles": "|".join(result.title for result in results),
                },
            )
        except SearchError:
            return results

        pages = payload.get("query", {}).get("pages", {})
        if not isinstance(pages, dict):
            return results
        disambiguation_titles = {
            page.get("title")
            for page in pages.values()
            if isinstance(page, dict) and "disambiguation" in page.get("pageprops", {})
        }
        extracts = {
            page.get("title"): page.get("extract", "")[:5000]
            for page in pages.values()
            if isinstance(page, dict) and isinstance(page.get("title"), str)
        }
        return [
            result.model_copy(update={"snippet": extracts.get(result.title) or result.snippet})
            for result in results
            if result.title not in disambiguation_titles
        ]

    async def search(self, query: str, count: int = 10) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("Query cannot be empty")
        if not 1 <= count <= 20:
            raise ValueError("Count must be between 1 and 20")

        if self.client is None:
            async with httpx.AsyncClient(timeout=15) as client:
                payload = await self._request(
                    client,
                    {"action": "query", "list": "search", "srsearch": query, "srlimit": count},
                )
                results = self._parse_search_results(payload)
                return await self._enrich_with_extracts(client, results)
        else:
            payload = await self._request(
                self.client,
                {"action": "query", "list": "search", "srsearch": query, "srlimit": count},
            )
            results = self._parse_search_results(payload)
            return await self._enrich_with_extracts(self.client, results)

    def _parse_search_results(self, payload: dict) -> list[SearchResult]:
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

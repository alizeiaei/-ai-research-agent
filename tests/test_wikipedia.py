import httpx
import pytest

from research_agent.search import SearchError
from research_agent.wikipedia import WikipediaSearchProvider


def test_invalid_language():
    with pytest.raises(ValueError, match="language"):
        WikipediaSearchProvider("https://example.com")


@pytest.mark.asyncio
async def test_search_parses_results_and_removes_html():
    def handler(request):
        assert request.url.host == "fa.wikipedia.org"
        assert request.headers["User-Agent"] == "test-agent"
        if request.url.params.get("prop") == "extracts|pageprops":
            return httpx.Response(
                200,
                json={
                    "query": {
                        "pages": {
                            "1": {
                                "title": "هوش مصنوعی",
                                "extract": "هوش مصنوعی برای تشخیص بیماری استفاده می‌شود.",
                            },
                            "2": {
                                "title": "هوش مصنوعی (ابهام‌زدایی)",
                                "extract": "این عنوان به چند موضوع اشاره دارد.",
                                "pageprops": {"disambiguation": ""},
                            },
                        }
                    }
                },
            )
        assert request.url.params["srsearch"] == "هوش مصنوعی"
        return httpx.Response(
            200,
            json={
                "query": {
                    "search": [
                        {
                            "title": "هوش مصنوعی",
                            "snippet": '<span class="searchmatch">هوش</span> مصنوعی',
                        },
                        {
                            "title": "هوش مصنوعی (ابهام‌زدایی)",
                            "snippet": "چند موضوع",
                        },
                        {"broken": "result"},
                    ]
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        results = await WikipediaSearchProvider("fa", http, "test-agent").search("هوش مصنوعی")

    assert len(results) == 1
    assert results[0].title == "هوش مصنوعی"
    assert results[0].snippet == "هوش مصنوعی برای تشخیص بیماری استفاده می‌شود."
    assert str(results[0].url).startswith("https://fa.wikipedia.org/wiki/")


@pytest.mark.asyncio
@pytest.mark.parametrize("query_section", [[], "invalid", {"search": {}}, {"search": None}])
async def test_malformed_response(query_section):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"query": query_section})
        )
    ) as http:
        with pytest.raises(SearchError, match="structure"):
            await WikipediaSearchProvider(client=http).search("AI")


@pytest.mark.asyncio
async def test_missing_query_section_returns_empty_results():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    ) as http:
        assert await WikipediaSearchProvider(client=http).search("AI") == []


@pytest.mark.asyncio
async def test_http_error_becomes_search_error():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    ) as http:
        with pytest.raises(SearchError, match="Wikipedia request failed"):
            await WikipediaSearchProvider(client=http).search("AI")

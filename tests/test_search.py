import httpx
import pytest

from research_agent.search import BraveSearchClient, SearchError


def test_missing_api_key():
    with pytest.raises(ValueError):
        BraveSearchClient("")


@pytest.mark.asyncio
async def test_invalid_input():
    client = BraveSearchClient("test")
    with pytest.raises(ValueError):
        await client.search("")
    with pytest.raises(ValueError):
        await client.search("AI", count=21)


@pytest.mark.asyncio
async def test_search_parses_and_deduplicates():
    def handler(request):
        assert request.headers["X-Subscription-Token"] == "test"
        return httpx.Response(
            200,
            json={"web": {"results": [
                {"title": "AI chips", "url": "https://example.com/a", "description": "AI chips"},
                {"title": "Duplicate", "url": "https://example.com/a", "description": "duplicate"},
                {"title": "Broken"},
            ]}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        results = await BraveSearchClient("test", http).search("AI chips")
    assert len(results) == 1
    assert results[0].source == "example.com"


@pytest.mark.asyncio
async def test_nonretryable_error():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(401))
    ) as http:
        with pytest.raises(SearchError):
            await BraveSearchClient("test", http).search("AI")

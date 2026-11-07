import httpx
import pytest

from research_agent.search import BraveSearchClient, SearchError, canonicalize_url, retry_delay


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
                {
                    "title": "Duplicate",
                    "url": "https://EXAMPLE.com/a/?utm_source=newsletter#section",
                    "description": "duplicate",
                },
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


@pytest.mark.asyncio
async def test_retryable_error_honors_retry_after():
    attempts = 0
    delays = []

    def handler(request):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"web": {"results": []}})

    async def fake_sleep(delay):
        delays.append(delay)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        results = await BraveSearchClient("test", http, sleep=fake_sleep).search("AI")

    assert results == []
    assert attempts == 2
    assert delays == [2.0]


@pytest.mark.asyncio
@pytest.mark.parametrize("web", [[], "invalid", {"results": {}}, {"results": None}])
async def test_malformed_search_response(web):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"web": web}))
    ) as http:
        with pytest.raises(SearchError, match="structure"):
            await BraveSearchClient("test", http).search("AI")


@pytest.mark.asyncio
async def test_missing_web_section_is_an_empty_result():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    ) as http:
        assert await BraveSearchClient("test", http).search("AI") == []


def test_canonicalize_url_removes_tracking_and_normalizes_equivalent_forms():
    assert canonicalize_url("HTTPS://Example.COM:443/a/?b=2&utm_source=x&a=1#part") == (
        "https://example.com/a?a=1&b=2"
    )


def test_retry_delay_falls_back_for_invalid_header():
    response = httpx.Response(429, headers={"Retry-After": "not-a-delay"})
    assert retry_delay(response, 0.5) == 0.5

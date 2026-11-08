import httpx
import pytest

from research_agent.models import SearchResult
from research_agent.web import app


class FakeSearchProvider:
    async def search(self, query, count=10):
        return [
            SearchResult(
                title="هوش مصنوعی",
                url="https://fa.wikipedia.org/wiki/AI",
                source="Wikipedia (fa)",
                snippet="هوش مصنوعی و کاربردهای آن",
            )
        ]


@pytest.fixture
async def web_client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_index_and_health(web_client):
    index = await web_client.get("/")
    health = await web_client.get("/health")

    assert index.status_code == 200
    assert "AI Research Agent" in index.text
    assert health.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_research_api(monkeypatch, web_client):
    monkeypatch.setattr(
        "research_agent.web.create_search_provider",
        lambda provider, language: FakeSearchProvider(),
    )

    response = await web_client.post(
        "/api/research",
        json={"query": "هوش مصنوعی", "provider": "wikipedia", "language": "fa", "count": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "هوش مصنوعی"
    assert len(payload["evidence"]) == 1
    assert payload["evidence"][0]["title"] == "هوش مصنوعی"


@pytest.mark.asyncio
async def test_research_api_rejects_invalid_input(web_client):
    response = await web_client.post(
        "/api/research",
        json={"query": "x", "provider": "wikipedia", "language": "fa", "count": 21},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_research_api_reports_provider_error(monkeypatch, web_client):
    def fail_to_create(provider, language):
        raise ValueError("provider unavailable")

    monkeypatch.setattr("research_agent.web.create_search_provider", fail_to_create)
    response = await web_client.post(
        "/api/research",
        json={"query": "AI safety", "provider": "brave", "language": "en", "count": 5},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "provider unavailable"

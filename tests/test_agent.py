import pytest

from research_agent.agent import ResearchAgent
from research_agent.models import SearchResult


class FakeSearch:
    async def search(self, query, count=10):
        return [
            SearchResult(
                title="AI chip performance",
                url="https://example.org/research",
                source="Example",
                snippet="AI chip performance benchmark",
            ),
            SearchResult(
                title="Unrelated recipe",
                url="https://example.org/food",
                source="Example",
                snippet="baking bread",
            ),
        ]


@pytest.mark.asyncio
async def test_agent_includes_citations_and_filters_irrelevant_results():
    report = await ResearchAgent(FakeSearch()).research("AI chip performance")
    assert len(report.evidence) == 1
    assert "https://example.org/research" in report.markdown
    assert "Unrelated recipe" not in report.markdown
    assert "not independently verified" in report.markdown

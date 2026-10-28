from research_agent.evaluator import score_result
from research_agent.models import SearchResult


def test_relevance_score():
    result = SearchResult(
        title="AI chip performance", url="https://example.org", source="Example"
    )
    assert score_result("AI chip performance", result) == 1.0
    assert score_result("quantum gardening", result) == 0.0

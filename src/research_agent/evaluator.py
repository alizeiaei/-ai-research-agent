import re

from research_agent.models import Evidence, SearchResult

STOPWORDS = {"the", "and", "for", "with", "from", "what", "how", "are", "does"}


def score_result(query: str, result: SearchResult) -> float:
    terms = {w for w in re.findall(r"\w+", query.lower()) if len(w) > 2} - STOPWORDS
    if not terms:
        return 0.0
    title = result.title.lower()
    snippet = result.snippet.lower()
    matches = sum(1 for term in terms if term in title or term in snippet)
    return round(matches / len(terms), 3)


def evaluate(query: str, results: list[SearchResult], threshold: float = 0.2) -> list[Evidence]:
    evidence = [
        Evidence(
            title=result.title,
            url=result.url,
            source=result.source,
            excerpt=result.snippet,
            score=score_result(query, result),
        )
        for result in results
    ]
    return sorted((e for e in evidence if e.score >= threshold), key=lambda e: -e.score)

from research_agent.evaluator import evaluate
from research_agent.models import ResearchReport
from research_agent.search import BraveSearchClient


def render_markdown(query: str, evidence: list) -> str:
    lines = [f"# Research: {query}", "", "## Evidence", ""]
    if not evidence:
        lines.append("No relevant sources were found. Do not treat this as a verified conclusion.")
    for index, item in enumerate(evidence, 1):
        lines.extend(
            [
                f"### [{index}] {item.title}",
                f"- Source: {item.source}",
                f"- URL: {item.url}",
                f"- Relevance: {item.score:.2f}",
                f"- Search excerpt: {item.excerpt or '(not provided)'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Limitations",
            "",
            "This report lists search-result excerpts, not independently verified article contents.",
            "Relevance is lexical, not a credibility or factual-accuracy score.",
            "",
        ]
    )
    return "\n".join(lines)


class ResearchAgent:
    def __init__(self, search_client: BraveSearchClient):
        self.search_client = search_client

    async def research(self, query: str, count: int = 10) -> ResearchReport:
        results = await self.search_client.search(query, count=count)
        evidence = evaluate(query, results)
        return ResearchReport(
            query=query, evidence=evidence, markdown=render_markdown(query, evidence)
        )

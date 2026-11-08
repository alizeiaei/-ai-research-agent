from research_agent.evaluator import evaluate
from research_agent.models import ResearchReport
from research_agent.search import SearchProvider
from research_agent.synthesizer import synthesize_report


def render_markdown(
    query: str,
    evidence: list,
    answer: str,
    key_findings: list,
    practical_applications: list,
    limitations: list,
) -> str:
    lines = [f"# Research: {query}", "", "## Direct Answer", "", answer, ""]

    for heading, insights in (
        ("Key Findings", key_findings),
        ("Practical Applications", practical_applications),
        ("Risks and Limitations", limitations),
    ):
        lines.extend([f"## {heading}", ""])
        if not insights:
            lines.extend(["No supported items were identified in the retrieved evidence.", ""])
        for insight in insights:
            citation = f" ([{insight.source_title}]({insight.source_url}))" if insight.source_url else ""
            lines.append(f"- {insight.text}{citation}")
        lines.append("")

    lines.extend(["## Supporting Evidence", ""])
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
            "## Method Limitations",
            "",
            "This report lists search-result excerpts, not independently verified article contents.",
            "Relevance is lexical, not a credibility or factual-accuracy score.",
            "",
        ]
    )
    return "\n".join(lines)


class ResearchAgent:
    def __init__(self, search_client: SearchProvider):
        self.search_client = search_client

    async def research(self, query: str, count: int = 10) -> ResearchReport:
        results = await self.search_client.search(query, count=count)
        evidence = evaluate(query, results)
        answer, findings, applications, limitations = synthesize_report(query, evidence)
        return ResearchReport(
            query=query,
            evidence=evidence,
            answer=answer,
            key_findings=findings,
            practical_applications=applications,
            limitations=limitations,
            markdown=render_markdown(
                query, evidence, answer, findings, applications, limitations
            ),
        )

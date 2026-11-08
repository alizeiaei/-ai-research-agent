import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from research_agent.agent import ResearchAgent
from research_agent.providers import create_search_provider
from research_agent.search import SearchError


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an evidence-first research report")
    parser.add_argument("query", help="Research question or topic")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("report.md"))
    parser.add_argument("--provider", choices=("brave", "wikipedia"), default="brave")
    parser.add_argument("--language", default="en", help="Wikipedia language code, e.g. en or fa")
    args = parser.parse_args()
    load_dotenv()

    try:
        search_provider = create_search_provider(args.provider, args.language)
        report = asyncio.run(ResearchAgent(search_provider).research(args.query, args.count))
    except (SearchError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    try:
        args.output.write_text(report.markdown, encoding="utf-8")
    except OSError as exc:
        parser.exit(1, f"Error: could not write report to {args.output}: {exc}\n")
    print(f"Saved {len(report.evidence)} sources to {args.output}")


if __name__ == "__main__":
    main()

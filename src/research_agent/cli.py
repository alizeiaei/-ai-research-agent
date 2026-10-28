import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from research_agent.agent import ResearchAgent
from research_agent.search import BraveSearchClient, SearchError


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an evidence-first research report")
    parser.add_argument("query", help="Research question or topic")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("report.md"))
    args = parser.parse_args()
    load_dotenv()
    key = os.getenv("BRAVE_API_KEY", "")
    if not key:
        parser.error("Set BRAVE_API_KEY in your environment or .env file")
    try:
        report = asyncio.run(ResearchAgent(BraveSearchClient(key)).research(args.query, args.count))
    except (SearchError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    args.output.write_text(report.markdown, encoding="utf-8")
    print(f"Saved {len(report.evidence)} sources to {args.output}")


if __name__ == "__main__":
    main()

# AI Research Agent

An evidence-first Python research assistant that searches the web, filters results by lexical relevance, and generates Markdown reports with source URLs.

**Status:** Foundation MVP. This is not yet an LLM summarizer or a fact-checking system. It works with search snippets rather than independently verified full articles.

## Features

- Async Brave Search API integration
- Input validation and retries for transient errors
- Duplicate URL filtering
- Transparent lexical relevance scoring
- Source-linked Markdown reports with limitations
- Mocked HTTP tests and GitHub Actions CI

## Quick start

Requires Python 3.12+ and a Brave Search API key.

```bash
git clone https://github.com/alizeiaei/-ai-research-agent.git
cd -- -ai-research-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
# Set BRAVE_API_KEY in .env
research-agent "AI chip performance benchmarks" --output report.md
```

## Quality checks

```bash
python -m pytest -v
python -m ruff check .
```

Tests use mocked responses; no live API key is required.

## Architecture

Search client → typed results → relevance evaluator → report renderer → CLI.

## Roadmap

1. Safe article extraction and structured evidence.
2. Source credibility, independence and freshness evaluation.
3. Optional LLM synthesis with grounded citations.
4. JSON export and evaluation datasets.

## Security

Never commit your `.env` or API credentials. Treat all retrieved content as untrusted.

## License

No open-source license has been selected.

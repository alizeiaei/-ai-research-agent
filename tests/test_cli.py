import sys
from pathlib import Path

import pytest

from research_agent.cli import main
from research_agent.models import ResearchReport


def test_cli_reports_output_write_failure(monkeypatch, capsys):
    async def fake_research(self, query, count=10):
        return ResearchReport(query=query, evidence=[], markdown="# Report")

    def fail_to_write(self, data, encoding=None):
        raise PermissionError("read-only destination")

    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    monkeypatch.setattr("research_agent.cli.ResearchAgent.research", fake_research)
    monkeypatch.setattr(Path, "write_text", fail_to_write)
    monkeypatch.setattr(sys, "argv", ["research-agent", "AI safety", "--output", "report.md"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "could not write report to report.md" in capsys.readouterr().err


def test_cli_uses_wikipedia_without_brave_api_key(monkeypatch, tmp_path):
    captured = {}

    async def fake_research(self, query, count=10):
        captured["provider"] = self.search_client
        return ResearchReport(query=query, evidence=[], markdown="# Report")

    output = tmp_path / "report.md"
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    monkeypatch.setattr("research_agent.cli.load_dotenv", lambda: None)
    monkeypatch.setattr("research_agent.cli.ResearchAgent.research", fake_research)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "research-agent",
            "هوش مصنوعی",
            "--provider",
            "wikipedia",
            "--language",
            "fa",
            "--output",
            str(output),
        ],
    )

    main()

    assert captured["provider"].language == "fa"
    assert output.read_text(encoding="utf-8") == "# Report"

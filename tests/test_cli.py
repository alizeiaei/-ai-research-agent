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

from research_agent.models import Evidence
from research_agent.synthesizer import synthesize_report


def test_synthesizer_creates_source_linked_practical_sections():
    evidence = [
        Evidence(
            title="Medical AI",
            url="https://example.org/medical-ai",
            source="Example",
            excerpt=(
                "Artificial intelligence is used to help doctors detect disease in medical images. "
                "A major limitation is the risk of bias when training data is incomplete."
            ),
            score=1,
        )
    ]

    answer, findings, applications, limitations = synthesize_report(
        "artificial intelligence medical", evidence
    )

    assert "detect disease" in answer
    assert findings[0].source_title == "Medical AI"
    assert "detect disease" in applications[0].text
    assert "risk of bias" in limitations[0].text


def test_synthesizer_handles_empty_evidence():
    answer, findings, applications, limitations = synthesize_report("unknown", [])
    assert "No supported answer" in answer
    assert findings == applications == limitations == []


def test_synthesizer_supports_short_acronym_queries():
    evidence = [
        Evidence(
            title="Artificial intelligence",
            url="https://example.org/ai",
            source="Example",
            excerpt=(
                "Artificial intelligence (AI) enables machines to perform complex tasks. "
                "AI is used to help people analyze information."
            ),
            score=1,
        )
    ]
    answer, findings, applications, _ = synthesize_report("AI", evidence)
    assert "Artificial intelligence" in answer
    assert findings
    assert applications

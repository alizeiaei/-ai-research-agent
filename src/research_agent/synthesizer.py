import re

from research_agent.models import Evidence, ReportInsight

APPLICATION_CUES = {
    "application",
    "applied",
    "assist",
    "detect",
    "diagnos",
    "help",
    "predict",
    "use",
    "استفاده",
    "پیش‌بینی",
    "تشخیص",
    "درمان",
    "کاربرد",
    "کمک",
}
LIMITATION_CUES = {
    "bias",
    "concern",
    "error",
    "limitation",
    "privacy",
    "risk",
    "uncertain",
    "اشتباه",
    "حریم خصوصی",
    "خطر",
    "ریسک",
    "سوگیری",
    "محدودیت",
}


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    return [part.strip() for part in re.split(r"(?<=[.!?؟])\s+", normalized) if len(part) >= 35]


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"\w+", text.lower()) if len(term) >= 2}


def _sentence_score(sentence: str, query_terms: set[str]) -> float:
    sentence_terms = _terms(sentence)
    if not query_terms:
        return 0.0
    return len(sentence_terms & query_terms) / len(query_terms)


def _insight(sentence: str, evidence: Evidence) -> ReportInsight:
    return ReportInsight(text=sentence, source_title=evidence.title, source_url=evidence.url)


def synthesize_report(
    query: str, evidence: list[Evidence]
) -> tuple[str, list[ReportInsight], list[ReportInsight], list[ReportInsight]]:
    """Build an extractive, source-linked report without inventing unsupported claims."""
    if not evidence:
        return "No supported answer was found in the retrieved sources.", [], [], []

    query_terms = _terms(query)
    candidates: list[tuple[float, str, Evidence]] = []
    seen: set[str] = set()
    for item in evidence:
        for sentence in split_sentences(item.excerpt):
            key = sentence.casefold()
            if key in seen:
                continue
            seen.add(key)
            candidates.append((_sentence_score(sentence, query_terms), sentence, item))

    candidates.sort(key=lambda candidate: candidate[0], reverse=True)
    if not candidates:
        answer = evidence[0].excerpt.strip() or "No supported answer was found."
        return answer[:700], [], [], []

    answer_sentences = [sentence for _, sentence, _ in candidates[:2]]
    answer = " ".join(answer_sentences)[:1200]
    key_findings = [_insight(sentence, item) for _, sentence, item in candidates[:5]]

    practical = [
        _insight(sentence, item)
        for _, sentence, item in candidates
        if any(cue in sentence.casefold() for cue in APPLICATION_CUES)
    ][:5]
    limitations = [
        _insight(sentence, item)
        for _, sentence, item in candidates
        if any(cue in sentence.casefold() for cue in LIMITATION_CUES)
    ][:4]
    return answer, key_findings, practical, limitations

from pydantic import BaseModel, Field, HttpUrl


class SearchResult(BaseModel):
    title: str = Field(min_length=1)
    url: HttpUrl
    source: str = Field(min_length=1)
    snippet: str = ""


class Evidence(BaseModel):
    title: str
    url: HttpUrl
    source: str
    excerpt: str
    score: float = Field(ge=0, le=1)


class ReportInsight(BaseModel):
    text: str = Field(min_length=1)
    source_title: str = ""
    source_url: HttpUrl | None = None


class ResearchReport(BaseModel):
    query: str
    evidence: list[Evidence]
    markdown: str
    answer: str = ""
    key_findings: list[ReportInsight] = Field(default_factory=list)
    practical_applications: list[ReportInsight] = Field(default_factory=list)
    limitations: list[ReportInsight] = Field(default_factory=list)

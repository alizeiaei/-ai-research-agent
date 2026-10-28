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


class ResearchReport(BaseModel):
    query: str
    evidence: list[Evidence]
    markdown: str

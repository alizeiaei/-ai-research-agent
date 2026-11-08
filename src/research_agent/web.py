from pathlib import Path
from typing import Literal

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from research_agent.agent import ResearchAgent
from research_agent.models import ResearchReport
from research_agent.providers import create_search_provider
from research_agent.search import SearchError

WEB_DIR = Path(__file__).parent / "web_assets"

app = FastAPI(
    title="AI Research Agent",
    description="Evidence-first research API backed by configurable search providers.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


class ResearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    provider: Literal["wikipedia", "brave"] = "wikipedia"
    language: str = Field(default="en", min_length=2, max_length=24)
    count: int = Field(default=10, ge=1, le=20)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/research", response_model=ResearchReport)
async def research(request: ResearchRequest) -> ResearchReport:
    load_dotenv()
    try:
        provider = create_search_provider(request.provider, request.language)
        return await ResearchAgent(provider).research(request.query, request.count)
    except (SearchError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def main() -> None:
    uvicorn.run("research_agent.web:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()

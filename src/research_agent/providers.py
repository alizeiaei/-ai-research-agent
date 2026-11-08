import os

from research_agent.search import BraveSearchClient, SearchProvider
from research_agent.wikipedia import DEFAULT_USER_AGENT, WikipediaSearchProvider


def create_search_provider(provider: str, language: str = "en") -> SearchProvider:
    """Create a configured provider without exposing provider details to callers."""
    if provider == "wikipedia":
        return WikipediaSearchProvider(
            language=language,
            user_agent=os.getenv("WIKIPEDIA_USER_AGENT", DEFAULT_USER_AGENT),
        )
    if provider == "brave":
        key = os.getenv("BRAVE_API_KEY", "")
        if not key:
            raise ValueError("Set BRAVE_API_KEY in your environment or .env file")
        return BraveSearchClient(key)
    raise ValueError(f"Unsupported search provider: {provider}")

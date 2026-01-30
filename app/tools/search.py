from tavily import TavilyClient
from app.core.config import settings

def search_web(query: str):
    """
    Perform a web search using Tavily.
    """
    if not settings.TAVILY_API_KEY:
        return "Tavily API Key is missing."
    
    tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
    response = tavily.search(query=query)
    return response.get("results", [])

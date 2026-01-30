from app.tools.search import search_web

# Reuse shared search tool or add specific ones
def specific_market_tool(query):
    return search_web(query)

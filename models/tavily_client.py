import os
from tavily import TavilyClient as TavilyAPI
import asyncio

class TavilyClient:
    def __init__(self, config):
        self.client = TavilyAPI(api_key=config.get_api_key("TAVILY_API_KEY"))

    async def search(self, query: str, search_depth="basic", max_results=5):
        try:
            result = await asyncio.to_thread(
                self.client.search,
                query=query,
                search_depth=search_depth,
                max_results=max_results
            )
            return self._format_search_results(result)
        except Exception as e:
            raise Exception(f"Error performing Tavily search: {str(e)}")

    def _format_search_results(self, result):
        formatted_results = []
        for item in result.get('results', []):
            formatted_results.append({
                'title': item.get('title'),
                'url': item.get('url'),
                'content': item.get('content')
            })
        return formatted_results

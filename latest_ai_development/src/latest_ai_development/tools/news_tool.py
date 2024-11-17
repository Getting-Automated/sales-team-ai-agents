# tools/news_tool.py

from crewai.tools import BaseTool
import os
import requests

class NewsTool(BaseTool):
    name = "news_tool"
    description = "Retrieves industry news articles using NewsAPI.org."

    def _run(self, industry_keywords: str) -> list:
        """Fetch news articles for the given industry keywords."""
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            return {"error": "News API key not found."}
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': industry_keywords,
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 20
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('articles', [])
        else:
            return {"error": f"News API error: {response.text}"}

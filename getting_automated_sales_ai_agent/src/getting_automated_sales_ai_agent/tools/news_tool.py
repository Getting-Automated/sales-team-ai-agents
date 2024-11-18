# tools/news_tool.py

from crewai.tools import BaseTool
from pydantic import Field, BaseModel
import os
import requests
from typing import Type

class NewsToolArgs(BaseModel):
    industry_keywords: str = Field(description="Keywords to search for news articles")

class NewsTool(BaseTool):
    name: str = "news_tool"
    description: str = "Retrieves industry news articles using NewsAPI.org."
    args_schema: Type[BaseModel] = NewsToolArgs

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

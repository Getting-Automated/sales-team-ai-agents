# tools/reddit_tool.py

from crewai.tools import BaseTool
from pydantic import Field, BaseModel
import os
import praw
from typing import Type, List

class RedditToolArgs(BaseModel):
    subreddit_list: List[str] = Field(description="List of subreddits to search")
    industry_keywords: str = Field(description="Keywords to search for in Reddit posts")

class RedditTool(BaseTool):
    name: str = "reddit_tool"
    description: str = "Retrieves Reddit discussions using PRAW."
    args_schema: Type[BaseModel] = RedditToolArgs

    def _run(self, subreddit_list: list, industry_keywords: str) -> list:
        """Fetch Reddit posts from given subreddits and keywords."""
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        if not all([client_id, client_secret, user_agent]):
            return {"error": "Reddit API credentials not found."}
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        posts = []
        for subreddit in subreddit_list:
            subreddit_obj = reddit.subreddit(subreddit)
            for submission in subreddit_obj.search(industry_keywords, limit=10):
                posts.append({
                    'title': submission.title,
                    'selftext': submission.selftext,
                    'url': submission.url
                })
        return posts

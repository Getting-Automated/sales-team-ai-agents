# tools/reddit_tool.py

from crewai.tools import BaseTool
import os
import praw

class RedditTool(BaseTool):
    name = "reddit_tool"
    description = "Retrieves Reddit discussions using PRAW."

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

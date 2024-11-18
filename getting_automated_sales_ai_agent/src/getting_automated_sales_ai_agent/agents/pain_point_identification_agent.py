# agents/pain_point_agent.py

from crewai import Agent
from langchain_community.llms import OpenAI
from ..tools.news_tool import NewsTool
from ..tools.reddit_tool import RedditTool
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool
import os
import json

def pain_point_agent_logic(self):
    # Access inputs
    industry_keywords = self.config.get('industry_keywords', '')
    if not industry_keywords:
        return "Industry keywords not provided."

    # Get news articles using NewsTool
    articles = self.news_tool._run(industry_keywords)
    article_texts = [article.get('content') or article.get('description', '') for article in articles]

    # Get Reddit posts using RedditTool
    subreddit_list = self.config.get('subreddit_list', ['industry_subreddit'])
    reddit_posts = self.reddit_tool._run(subreddit_list, industry_keywords)
    reddit_texts = [post['title'] + '\n' + post['selftext'] for post in reddit_posts]

    # Combine texts
    all_texts = article_texts + reddit_texts
    combined_text = '\n'.join(all_texts)

    # Prepare analysis prompt
    analysis_prompt = f"""
    Analyze the following texts to identify common pain points in the industry:

    {combined_text}

    Summarize the key pain points, extract relevant keywords, and highlight significant quotes.
    Respond in JSON format: {{"pain_points": "...", "keywords": [...], "quotes": [...]}}
    """

    # Analyze using the agent's LLM
    analysis_result = self.llm.complete(analysis_prompt)
    try:
        analysis = json.loads(analysis_result)
    except json.JSONDecodeError:
        self.logger.error("Error parsing analysis result.")
        return "Error in analysis."

    # Prepare data for Airtable
    pain_points_data = {
        'Industry': industry_keywords,
        'PainPoints': analysis.get('pain_points'),
        'Keywords': ', '.join(analysis.get('keywords', [])),
        'HighlightedQuotes': '\n'.join(analysis.get('quotes', [])),
    }

    # Store data in Airtable using AirtableTool
    airtable_result = self.airtable_tool._run('create', 'PainPointsTable', data=pain_points_data)
    if 'error' in airtable_result:
        self.logger.error(f"Error storing pain points in Airtable: {airtable_result['error']}")
    else:
        self.logger.info("Pain points stored successfully.")

    return "Pain point identification completed and data stored in Airtable."

def get_pain_point_agent(config, tools, llm):
    agent_conf = config['pain_point_agent']
    agent_instance = Agent(
        llm=llm,
        tools=tools,
        **agent_conf
    )
    # Assign custom logic to the agent's run method
    agent_instance.run = pain_point_agent_logic.__get__(agent_instance, Agent)
    return agent_instance

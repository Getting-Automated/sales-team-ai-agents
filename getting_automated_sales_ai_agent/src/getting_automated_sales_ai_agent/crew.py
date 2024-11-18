# crew.py

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import yaml

# Import tools
from .tools.proxycurl_tool import ProxycurlTool
from .tools.company_data_tool import CompanyDataTool
from .tools.news_tool import NewsTool
from .tools.reddit_tool import RedditTool
from .tools.airtable_tool import AirtableTool

class GettingAutomatedSalesAiAgent:
    """GettingAutomatedSalesAiAgent crew"""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            api_key=os.getenv('OPENAI_API_KEY')
        )

        # Initialize tools with LLM
        self.proxycurl_tool = ProxycurlTool(llm=self.llm)
        self.company_data_tool = CompanyDataTool(llm=self.llm)
        self.news_tool = NewsTool(llm=self.llm)
        self.reddit_tool = RedditTool(llm=self.llm)
        self.airtable_tool = AirtableTool(llm=self.llm)

        # Initialize agents
        self.customer_icp_agent = Agent(
            role="Customer ICP Agent",
            goal="Analyze leads based on provided Customer ICP and assign scores",
            backstory="You're an experienced sales analyst specializing in evaluating potential leads for market fit.",
            tools=[self.proxycurl_tool, self.company_data_tool, self.airtable_tool],
            llm=self.llm,
            verbose=True
        )

        self.pain_point_agent = Agent(
            role="Pain Point Identification Agent",
            goal="Identify industry pain points using provided keywords",
            backstory="You're a market researcher adept at uncovering industry trends and challenges.",
            tools=[self.news_tool, self.reddit_tool, self.airtable_tool],
            llm=self.llm,
            verbose=True
        )

        self.solution_templates_agent = Agent(
            role="Solution Templates Agent",
            goal="Customize solution templates based on identified pain points",
            backstory="You're a solutions architect with expertise in tailoring offerings to meet client needs.",
            tools=[self.airtable_tool],
            llm=self.llm,
            verbose=True
        )

        self.offer_creator_agent = Agent(
            role="Offer Researcher & Creator Agent",
            goal="Generate personalized offers and email drafts using data from other agents",
            backstory="You're a creative writer and strategist who specializes in crafting compelling offers.",
            tools=[self.airtable_tool],
            llm=self.llm,
            verbose=True
        )

    def create_tasks(self):
        return [
            Task(
                description="Analyze the provided leads and assign scores based on ICP fit.",
                expected_output="A list of leads with their ICP fit scores and analysis.",
                agent=self.customer_icp_agent
            ),
            Task(
                description="Identify industry pain points using the provided keywords.",
                expected_output="A comprehensive list of industry pain points and trends.",
                agent=self.pain_point_agent
            ),
            Task(
                description="Customize solution templates based on identified pain points.",
                expected_output="Customized solution templates that address identified pain points.",
                agent=self.solution_templates_agent
            ),
            Task(
                description="Generate personalized offers and email drafts.",
                expected_output="Personalized offer documents and email drafts for each qualified lead.",
                agent=self.offer_creator_agent
            )
        ]

    @property
    def crew(self):
        """Creates the crew"""
        return Crew(
            agents=[
                self.customer_icp_agent,
                self.pain_point_agent,
                self.solution_templates_agent,
                self.offer_creator_agent
            ],
            tasks=self.create_tasks(),
            process=Process.sequential,
            verbose=True
        )

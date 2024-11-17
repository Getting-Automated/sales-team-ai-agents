# crew.py

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
import os
import yaml

# Import tools
from tools.proxycurl_tool import ProxycurlTool
from tools.company_data_tool import CompanyDataTool
from tools.news_tool import NewsTool
from tools.reddit_tool import RedditTool
from tools.airtable_tool import AirtableTool

# Import agents
from agents.customer_icp_agent import get_customer_icp_agent
from agents.pain_point_identification_agent import get_pain_point_agent
from agents.solutions_template_agent import get_solution_templates_agent
from agents.offer_researcher_creator_agent import get_offer_creator_agent

@CrewBase
class YourProjectCrew:
    """YourProjectCrew crew"""

    # Load environment variables
    load_dotenv()

    def __init__(self):
        # Load configurations from YAML files
        with open('config/agents.yaml', 'r') as f:
            self.agents_config = yaml.safe_load(f)

        with open('config/tasks.yaml', 'r') as f:
            self.tasks_config = yaml.safe_load(f)

        # Optionally load additional configurations
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)

        # Instantiate the default LLM instance
        self.default_llm = self.get_default_llm_instance()

        # Instantiate tools at the class level
        self.proxycurl_tool = ProxycurlTool()
        self.company_data_tool = CompanyDataTool(llm=self.default_llm)  # Pass the LLM instance
        self.news_tool = NewsTool()
        self.reddit_tool = RedditTool()
        self.airtable_tool = AirtableTool()

    def get_default_llm_instance(self):
        return LLM(
            model='gpt-4',
            temperature=0.7,
            max_tokens=1500,
            api_key=os.getenv('OPENAI_API_KEY'),
        )

    def get_llm_instance(self, llm_conf):
        """Create an LLM instance based on the provided configuration."""
        return LLM(
            model=llm_conf.get('model', 'gpt-4'),
            temperature=llm_conf.get('temperature', 0.7),
            max_tokens=llm_conf.get('max_tokens', 1500),
            api_key=os.getenv('OPENAI_API_KEY'),
        )

    @agent
    def customer_icp_agent(self) -> Agent:
        agent_conf = self.agents_config['customer_icp_agent'].copy()
        llm_conf = agent_conf.pop('llm', {})
        llm_instance = self.get_llm_instance(llm_conf) if llm_conf else self.default_llm
        tools = [
            self.proxycurl_tool,
            self.company_data_tool,
            self.airtable_tool
        ]
        agent_instance = get_customer_icp_agent(agent_conf, tools, llm_instance)
        agent_instance.inputs = self.inputs
        agent_instance.config = self.config
        return agent_instance

    @agent
    def pain_point_agent(self) -> Agent:
        agent_conf = self.agents_config['pain_point_agent'].copy()
        llm_conf = agent_conf.pop('llm', {})
        llm_instance = self.get_llm_instance(llm_conf) if llm_conf else self.default_llm
        tools = [
            self.news_tool,
            self.reddit_tool,
            self.airtable_tool
        ]
        agent_instance = get_pain_point_agent(agent_conf, tools, llm_instance)
        agent_instance.inputs = self.inputs
        agent_instance.config = self.config
        return agent_instance

    @agent
    def solution_templates_agent(self) -> Agent:
        agent_conf = self.agents_config['solution_templates_agent'].copy()
        llm_conf = agent_conf.pop('llm', {})
        llm_instance = self.get_llm_instance(llm_conf) if llm_conf else self.default_llm
        tools = [self.airtable_tool]
        agent_instance = get_solution_templates_agent(agent_conf, tools, llm_instance)
        agent_instance.inputs = self.inputs
        agent_instance.config = self.config
        return agent_instance

    @agent
    def offer_creator_agent(self) -> Agent:
        agent_conf = self.agents_config['offer_creator_agent'].copy()
        llm_conf = agent_conf.pop('llm', {})
        llm_instance = self.get_llm_instance(llm_conf) if llm_conf else self.default_llm
        tools = [self.airtable_tool]
        agent_instance = get_offer_creator_agent(agent_conf, tools, llm_instance)
        agent_instance.inputs = self.inputs
        agent_instance.config = self.config
        return agent_instance

    @task
    def customer_analysis_task(self) -> Task:
        task_conf = self.tasks_config['customer_analysis_task'].copy()
        agent_name = task_conf.pop('agent')
        return Task(
            agent=getattr(self, agent_name),
            **task_conf
        )

    @task
    def pain_point_task(self) -> Task:
        task_conf = self.tasks_config['pain_point_task'].copy()
        agent_name = task_conf.pop('agent')
        return Task(
            agent=getattr(self, agent_name),
            **task_conf
        )

    @task
    def template_customization_task(self) -> Task:
        task_conf = self.tasks_config['template_customization_task'].copy()
        agent_name = task_conf.pop('agent')
        return Task(
            agent=getattr(self, agent_name),
            **task_conf
        )

    @task
    def offer_creation_task(self) -> Task:
        task_conf = self.tasks_config['offer_creation_task'].copy()
        agent_name = task_conf.pop('agent')
        return Task(
            agent=getattr(self, agent_name),
            **task_conf
        )

    @crew
    def crew(self) -> Crew:
        """Creates the YourProjectCrew crew"""
        return Crew(
            agents=self.agents,  # Automatically collected by the @agent decorator
            tasks=self.tasks,    # Automatically collected by the @task decorator
            process=Process.sequential,
            verbose=True,
        )

# crew.py

from crewai import Agent, Crew, Process, Task, LLM
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import yaml
import json

# Import tools
from .tools.proxycurl_tool import ProxycurlTool
from .tools.company_data_tool import CompanyDataTool
from .tools.reddit_tool import RedditTool
from .tools.airtable_tool import AirtableTool
from .tools.perplexity_tool import PerplexityTool
from .tools.openai_tool import OpenAITool

class GettingAutomatedSalesAiAgent:
    """GettingAutomatedSalesAiAgent crew"""

    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Load configurations
        config_dir = Path(__file__).parent / "config"
        print(f"\nDEBUG: Config directory path: {config_dir}")
        
        # Load crew configuration
        crew_config_path = config_dir / "crew.yaml"
        print(f"DEBUG: Loading crew config from: {crew_config_path}")
        with open(crew_config_path, 'r') as f:
            self.crew_config = yaml.safe_load(f)
            print(f"DEBUG: Crew config loaded: {self.crew_config.keys()}")
            
        # Load ICP configuration
        icp_config_path = config_dir / "config.yaml"
        print(f"DEBUG: Loading ICP config from: {icp_config_path}")
        with open(icp_config_path, 'r') as f:
            self.icp_config = yaml.safe_load(f)
            # print(f"DEBUG: ICP config loaded: {self.icp_config.keys()}")
        
        # print(f"DEBUG: Full ICP config: {json.dumps(self.icp_config, indent=2)}")
        
        self.inputs = {
            'leads': None,  # Will be set later
            'config': self.icp_config  # Include ICP config here
        }
        
        # Initialize LLM using CrewAI's LLM class with provider prefix
        self.llm = LLM(
            model="openai/gpt-4o",
            temperature=0.7,
            api_key=os.getenv('OPENAI_API_KEY')
        )

        # Initialize tools with error handling and API key validation
        try:
            perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
            openai_api_key = os.getenv('OPENAI_API_KEY')
            
            if not perplexity_api_key:
                raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            self.tools = {
                'proxycurl_tool': ProxycurlTool(llm=self.llm),
                'company_data_tool': CompanyDataTool(llm=self.llm),
                'perplexity_tool': PerplexityTool(llm=self.llm),
                'openai_tool': OpenAITool(llm=self.llm),
                'airtable_tool': AirtableTool(llm=self.llm)
            }
        except ValueError as e:
            print(f"Error initializing tools: {str(e)}")
            raise

        # Initialize agents from config
        self.agents = self._initialize_agents()

    def _initialize_agents(self):
        """Initialize agents from config"""
        agents = {}
        
        # Initialize worker agents with delegation enabled
        for agent_id, agent_config in self.crew_config['agents'].items():
            # Get the tools specified in the config
            agent_tools = [self.tools[tool] for tool in agent_config['tools']]
            
            # Create the agent with delegation enabled
            agents[agent_id] = Agent(
                role=agent_config['role'],
                goal=agent_config['goal'],
                backstory=agent_config['backstory'],
                tools=agent_tools,
                llm=self.llm,
                verbose=self.crew_config['process']['verbose'],
                allow_delegation=True  # Enable delegation for all agents
            )
        
        # Initialize manager agent with delegation enabled
        manager_config = self.crew_config['manager']
        self.manager_agent = Agent(
            role=manager_config['role'],
            goal=manager_config['goal'],
            backstory=manager_config['backstory'],
            llm=self.llm,
            verbose=self.crew_config['process']['verbose'],
            allow_delegation=True  # Enable delegation for manager
        )
        
        return agents

    def create_tasks(self):
        """Create tasks for processing leads"""
        if not self.inputs.get('leads'):
            raise ValueError("No leads data provided to analyze")
        
        tasks = []
        for lead in self.inputs['leads']:
            try:
                # Company Evaluation Task
                tasks.append(Task(
                    description=f"""
                    Evaluate company {lead.get('company')} for potential fit:
                    - Analyze company size, industry, and growth stage
                    - Review technical infrastructure and stack
                    - Assess market position and challenges
                    
                    Lead Data: {json.dumps(lead, indent=2)}
                    """,
                    expected_output="Detailed company evaluation report with fit assessment",
                    agent=self.agents['company_evaluator']
                ))

                # Pain Point Analysis Task
                tasks.append(Task(
                    description=f"""
                    Identify key pain points for {lead.get('company')}:
                    - Research industry-specific challenges
                    - Analyze growth-related pain points
                    - Evaluate technical and operational bottlenecks
                    
                    Previous Analysis: {{context.company_evaluation}}
                    """,
                    expected_output="List of identified pain points with analysis",
                    agent=self.agents['pain_point_agent']
                ))

                # Offer Creation Task
                tasks.append(Task(
                    description=f"""
                    Create customized offer for {lead.get('company')}:
                    - Address identified pain points
                    - Align with company's technical capabilities
                    - Demonstrate clear ROI and value proposition
                    
                    Pain Points: {{context.pain_points}}
                    """,
                    expected_output="Detailed offer proposal with ROI analysis",
                    agent=self.agents['offer_creator_agent']
                ))

                # Email Campaign Task
                tasks.append(Task(
                    description=f"""
                    Generate personalized email campaign for {lead.get('name')}:
                    - Create compelling initial outreach
                    - Design follow-up sequence
                    - Incorporate pain points and solutions
                    
                    Solution: {{context.offer}}
                    """,
                    expected_output="Complete email campaign sequence with follow-ups",
                    agent=self.agents['email_campaign_agent']
                ))

            except Exception as e:
                print(f"Error creating tasks for lead {lead.get('name')}: {str(e)}")
                continue

        return tasks

    @property
    def crew(self):
        """Create and return the crew with hierarchical process"""
        return Crew(
            agents=list(self.agents.values()),
            tasks=self.create_tasks(),
            process=Process.hierarchical,
            manager_agent=self.manager_agent,
            verbose=self.crew_config['process']['verbose']
        )

    def run(self):
        """Execute the crew's tasks and return results"""
        try:
            result = self.crew.kickoff()
            print("\nCompleted analysis")
            return result
        except Exception as e:
            print(f"Error running crew: {str(e)}")
            raise
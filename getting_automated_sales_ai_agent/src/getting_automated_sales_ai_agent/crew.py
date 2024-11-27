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
        crew_config_path = config_dir / "agents.yaml"
        print(f"DEBUG: Loading crew config from: {crew_config_path}")
        with open(crew_config_path) as f:
            self.crew_config = yaml.safe_load(f)
        print(f"DEBUG: Crew config loaded: {self.crew_config.keys()}")
        
        # Load ICP configuration
        icp_config_path = config_dir / "config.yaml"
        print(f"DEBUG: Loading ICP config from: {icp_config_path}")
        with open(icp_config_path, 'r') as f:
            self.icp_config = yaml.safe_load(f)
        
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
        
        # Initialize manager agent
        manager_config = self.crew_config['manager']
        self.manager_agent = Agent(
            role=manager_config['role'],
            goal=manager_config['goal'],
            backstory=manager_config['backstory'],
            llm=self.llm,
            verbose=self.crew_config['process']['verbose'],
            allow_delegation=True,
            memory=True
        )
        
        # Get list of agent configs (excluding process, llm, and manager)
        agent_configs = {k: v for k, v in self.crew_config.items() 
                        if k not in ['process', 'llm', 'manager']}
        
        # Initialize worker agents
        for agent_id, agent_config in agent_configs.items():
            agent_tools = [
                self.tools[tool] 
                for tool in agent_config.get('tools', [])
                if tool in self.tools
            ]
            
            print(f"\nDEBUG: Initializing {agent_id} with tools: {[tool.__class__.__name__ for tool in agent_tools]}")
            
            agents[agent_id] = Agent(
                role=agent_config['role'],
                goal=agent_config['goal'],
                backstory=agent_config['backstory'],
                tools=agent_tools,
                llm=self.llm,
                verbose=self.crew_config['process']['verbose'],
                allow_delegation=True,
                memory=agent_config.get('memory', True)
            )
        
        return agents

    def create_tasks(self):
        """Create tasks for processing leads"""
        if not self.inputs.get('leads'):
            raise ValueError("No leads data provided to analyze")
        
        # Get ICP configuration
        icp_config = self.icp_config.get('customer_icp', {})
        
        tasks = []
        for lead in self.inputs['leads']:
            try:
                # Individual Lead Evaluation Task
                tasks.append(Task(
                    description=f"""
                    {self.crew_config['individual_evaluator']['backstory']}
                    
                    Goal: {self.crew_config['individual_evaluator']['goal']}
                    
                    Evaluate individual lead {lead.get('name')} against these ICP criteria:
                    - Target Departments: {', '.join(icp_config.get('target_departments', []))}
                    - Job Titles: {', '.join(icp_config.get('job_titles', []))}
                    - Decision Making Authority: {', '.join(icp_config.get('decision_making_authority', []))}
                    
                    Lead Data: {json.dumps(lead, indent=2)}
                    """,
                    expected_output="Detailed individual evaluation report with ICP alignment score",
                    agent=self.agents['individual_evaluator']
                ))

                # Company Evaluation Task
                tasks.append(Task(
                    description=f"""
                    {self.crew_config['agents']['company_evaluator']['backstory']}
                    
                    Goal: {self.crew_config['agents']['company_evaluator']['goal']}
                    
                    Evaluate company {lead.get('company')} against these ICP criteria:
                    - Industries: {', '.join(icp_config.get('industries', []))}
                    - Business Models: {', '.join(icp_config.get('business_models', []))}
                    - Technologies: {', '.join(icp_config.get('technologies', []))}
                    - Growth Stages: {', '.join(icp_config.get('growth_stages', []))}
                    - Employee Count Range: {icp_config.get('minimum_requirements', {}).get('employee_count_min')} - {icp_config.get('minimum_requirements', {}).get('employee_count_max')}
                    
                    Company Data: {json.dumps(lead, indent=2)}
                    """,
                    expected_output="Comprehensive company analysis with fit assessment",
                    agent=self.agents['company_evaluator']
                ))

                # Pain Point Analysis Task
                tasks.append(Task(
                    description=f"""
                    {self.crew_config['agents']['pain_point_analyst']['backstory']}
                    
                    Goal: {self.crew_config['agents']['pain_point_analyst']['goal']}
                    
                    Profile Overview: {icp_config.get('profile_overview', '')}
                    
                    Analyze pain points for {lead.get('company')} considering:
                    - Industry challenges in {lead.get('industry')}
                    - Technical infrastructure needs
                    - Growth-related operational challenges
                    
                    Previous Evaluations: {{context.individual_evaluation}}
                    Company Analysis: {{context.company_evaluation}}
                    """,
                    expected_output="Detailed pain point analysis with prioritization",
                    agent=self.agents['pain_point_agent'],
                    context=["individual_evaluation", "company_evaluation"]
                ))

                # Offer Creation Task
                tasks.append(Task(
                    description=f"""
                    {self.crew_config['agents']['offer_creator']['backstory']}
                    
                    Goal: {self.crew_config['agents']['offer_creator']['goal']}
                    
                    Create personalized solution offering for {lead.get('company')}:
                    - Address identified pain points
                    - Align with ICP profile: {icp_config.get('profile_overview', '')}
                    - Demonstrate clear value proposition and ROI
                    
                    Pain Points: {{context.pain_points}}
                    Company Evaluation: {{context.company_evaluation}}
                    """,
                    expected_output="Personalized offer with value proposition",
                    agent=self.agents['offer_creator_agent'],
                    context=["pain_point_analysis", "company_evaluation"]
                ))

                # Email Campaign Task
                tasks.append(Task(
                    description=f"""
                    Generate a 5-email campaign sequence and store in Airtable:
                    Lead ID: {lead_id}
                    
                    Create 5 strategic emails in sequence using the airtable_tool:

                    1. Initial Outreach (Sequence Number: 1, Wait Days: 0)
                    - Focus on introduction and primary value proposition
                    - Reference specific company research
                    
                    2. Value-Add Follow-up (Sequence Number: 2, Wait Days: 3)
                    - Share relevant content or insight
                    - Build credibility without hard selling
                    
                    3. Pain Point Focus (Sequence Number: 3, Wait Days: 5)
                    - Address specific pain points identified
                    - Share relevant industry insights
                    
                    4. ROI Discussion (Sequence Number: 4, Wait Days: 7)
                    - Present concrete business value
                    - Include specific metrics or outcomes
                    
                    5. Final Value Proposition (Sequence Number: 5, Wait Days: 10)
                    - Create urgency
                    - Make strong final offer
                    - Include all previous context
                    
                    For each email, create a record in the 'Email Campaigns' table with:
                    - Lead ID: {lead_id}
                    - Email Subject: Unique, compelling subject line
                    - Email Body: Personalized content
                    - Sequence Number: (1 through 5)
                    - Wait Days: (0, 3, 5, 7, or 10)
                    - Personalization Notes: Specific personalization points
                    - Pain Points Addressed: Pain points tackled in this email
                    - Call To Action: Primary CTA for this stage
                    
                    Ensure each email:
                    1. Builds upon previous communications
                    2. References any positive interactions
                    3. Provides unique value at each touch
                    4. Maintains consistent narrative
                    5. Gets progressively more direct with CTAs
                    """,
                    expected_output="Complete email sequence (5 emails) created in Airtable",
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
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
        
        tasks = []
        for lead in self.inputs['leads']:
            # Use email as unique identifier
            lead_id = f"LEAD_{lead.get('email', '').replace('@', '_at_').replace('.', '_dot_')}"
            
            # Create context as a list with a properly formatted dictionary
            task_context = [{
                'description': f"Context for lead {lead.get('name')}",
                'expected_output': "Lead and configuration data",
                'lead': lead,
                'config': self.icp_config,
                'lead_id': lead_id,
                'airtable_record_id': None  # We'll update this after the initial search/create
            }]
            
            # Initial Lead Storage Task
            tasks.append(Task(
                description=f"""
                Store or update lead in Airtable Leads table.
                First, search for existing lead by email: {lead.get('email')}
                
                Use the airtable_tool to:
                1. Search for existing lead:
                   - action: "search"
                   - table_name: "Leads"
                   - search_field: "Email"
                   - search_value: "{lead.get('email')}"
                
                2. If not found, create new record:
                   - action: "create"
                   - table_name: "Leads"
                   - data:
                     - Lead ID: {lead_id}
                     - Name: {lead.get('name')}
                     - Email: {lead.get('email')}
                     - Company: {lead.get('company')}
                     - Role: {lead.get('role')}
                     - Individual Evaluation Status: "Not Started"
                     - Company Evaluation Status: "Not Started"
                     - Raw Data: {json.dumps(lead)}
                
                3. If found, update the task context with the found record ID.
                
                Return the Airtable record ID and current evaluation statuses.
                Update the task context with the Airtable record ID.
                """,
                expected_output="Airtable record details including record ID",
                agent=self.agents['individual_evaluator'],
                context=task_context
            ))
            
            # Individual Evaluation Task
            tasks.append(Task(
                description=f"""
                {self.crew_config['individual_evaluator']['backstory']}
                
                Goal: {self.crew_config['individual_evaluator']['goal']}
                
                Evaluate individual lead {lead.get('name')} against these ICP criteria:
                - Target Departments: {', '.join(self.icp_config.get('target_departments', []))}
                - Job Titles: {', '.join(self.icp_config.get('job_titles', []))}
                - Decision Making Authority: {', '.join(self.icp_config.get('decision_making_authority', []))}
                
                Lead Data: {json.dumps(lead, indent=2)}
                
                After evaluation, update the Airtable record using:
                - action: "update"
                - table_name: "Leads"
                - record_id: [Use the Airtable record ID from the task context]
                - data: [Include evaluation results]
                """,
                expected_output="Detailed individual evaluation report with ICP alignment score",
                agent=self.agents['individual_evaluator'],
                context=task_context
            ))
            
            # Company Evaluation Task
            tasks.append(Task(
                description=f"""
                {self.crew_config['company_evaluator']['backstory']}
                
                Goal: {self.crew_config['company_evaluator']['goal']}
                
                Evaluate company {lead.get('company')} against these ICP criteria:
                - Industries: {', '.join(self.icp_config.get('industries', []))}
                - Business Models: {', '.join(self.icp_config.get('business_models', []))}
                - Technologies: {', '.join(self.icp_config.get('technologies', []))}
                - Growth Stages: {', '.join(self.icp_config.get('growth_stages', []))}
                - Employee Count Range: {self.icp_config.get('minimum_requirements', {}).get('employee_count_min')} - {self.icp_config.get('minimum_requirements', {}).get('employee_count_max')}
                
                Company Data: {json.dumps(lead, indent=2)}
                """,
                expected_output="Company evaluation results",
                agent=self.agents['company_evaluator'],
                context=task_context
            ))

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
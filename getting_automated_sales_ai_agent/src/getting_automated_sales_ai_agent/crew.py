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
        
        # Load crew configuration
        with open(config_dir / "crew.yaml", 'r') as f:
            self.crew_config = yaml.safe_load(f)
            
        # Load ICP configuration
        with open(config_dir / "config.yaml", 'r') as f:
            self.icp_config = yaml.safe_load(f)
        
        # Load pricing configuration
        with open(config_dir / "pricing.yaml", 'r') as f:
            pricing_config = yaml.safe_load(f)
            self.pricing_config = pricing_config['models']  # Access the 'models' key
        
        self.inputs = {
            'leads': None,  # Will be set later
            'config': self.icp_config  # Include ICP config here
        }
        
        # Initialize LLM using CrewAI's LLM class with provider prefix
        self.llm = LLM(
            model="openai/gpt-4o-mini",
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
        agents = {}
        for agent_id, agent_config in self.crew_config['agents'].items():
            # Get the tools specified in the config
            agent_tools = [self.tools[tool] for tool in agent_config['tools']]
            
            # Create the agent
            agents[agent_id] = Agent(
                role=agent_config['role'],
                goal=agent_config['goal'],
                backstory=agent_config['backstory'],
                tools=agent_tools,
                llm=self.llm,
                verbose=self.crew_config['process']['verbose']
            )
        return agents

    def create_tasks(self):
        if not self.inputs['leads']:
            raise ValueError("No leads data provided to analyze")
        
        leads = self.inputs['leads']
        icp_criteria = self.icp_config['customer_icp']['scoring_criteria']
        tasks = []
        
        for lead in leads:
            print(f"\nCreating tasks for lead: {lead.get('name')} at {lead.get('company')}")
            
            email = lead.get('email', '')
            domain = email.split('@')[-1] if email else None
            
            if not domain:
                print(f"Warning: No email domain found for {lead.get('name')}")
                domain = lead.get('company_website', '').replace('https://', '').replace('www.', '').split('/')[0]
                if not domain:
                    print(f"Skipping lead {lead.get('name')} - no email or website domain found")
                    continue
                print(f"Using website domain instead: {domain}")
            
            # Task 1: ICP Analysis
            tasks.append(
                Task(
                    description=f"""
                    Analyze this lead and their company for ICP fit. Follow these steps exactly:
                    1. Company Website Analysis: Use CompanyDataTool for domain: {domain}
                    2. Individual Analysis: Use ProxycurlTool for LinkedIn: {lead.get('linkedin_url')}
                    3. Score this opportunity using the provided criteria
                    4. Provide a detailed assessment of their tech stack and growth stage
                    
                    LEAD DATA:
                    {json.dumps(lead, indent=2)}
                    
                    SCORING CRITERIA:
                    {json.dumps(icp_criteria, indent=2)}
                    """,
                    expected_output="ICP analysis and company data",
                    agent=self.agents['customer_icp']
                )
            )
            
            # Task 2: Pain Point Analysis
            tasks.append(
                Task(
                    description=f"""
                    Identify pain points using company context and research. Focus on:
                    1. Mid-market specific challenges for their size ({lead.get('employees', '')} employees)
                    2. Technology gaps and integration issues with their current stack
                    3. Growth bottlenecks at their current stage
                    4. Operational inefficiencies across departments
                    5. Resource constraints and competitive pressures
                    
                    Company Domain: {domain}
                    Company Website: {lead.get('company_website')}
                    
                    LEAD DATA:
                    {json.dumps(lead, indent=2)}
                    
                    PREVIOUS ANALYSIS:
                    {{result_1}}
                    
                    Use Perplexity for targeted research and OpenAI for analysis.
                    Format findings as structured JSON with evidence and confidence scores.
                    """,
                    expected_output="Pain point analysis",
                    agent=self.agents['pain_point']
                )
            )
            
            # Task 3: Solution Templates
            tasks.append(
                Task(
                    description=f"""
                    Create solution templates based on identified pain points. Consider:
                    1. Company size: {lead.get('employees')}
                    2. Industry: {lead.get('industry')}
                    3. Technology stack: {lead.get('technologies')}
                    4. Current growth stage and challenges
                    5. Department-specific needs
                    
                    Company Domain: {domain}
                    
                    LEAD DATA:
                    {json.dumps(lead, indent=2)}
                    
                    ICP ANALYSIS:
                    {{result_1}}
                    
                    PAIN POINTS:
                    {{result_2}}
                    
                    Customize solutions for their specific context and challenges.
                    Include implementation considerations and expected outcomes.
                    """,
                    expected_output="Customized solution templates",
                    agent=self.agents['solution_templates']
                )
            )
            
            # Task 4: Offer Creation
            tasks.append(
                Task(
                    description=f"""
                    Generate personalized offer using all previous analysis. Include:
                    1. Value proposition tailored to their specific pain points
                    2. ROI calculations based on company size and industry
                    3. Implementation timeline considering their current stage
                    4. Risk mitigation strategies
                    5. Competitive differentiators
                    
                    Target Contact:
                    - Name: {lead.get('name')}
                    - Role: {lead.get('role')}
                    - Seniority: {lead.get('seniority')}
                    - Email Domain: {domain}
                    
                    LEAD DATA:
                    {json.dumps(lead, indent=2)}
                    
                    ICP ANALYSIS:
                    {{result_1}}
                    
                    PAIN POINTS:
                    {{result_2}}
                    
                    SOLUTION TEMPLATES:
                    {{result_3}}
                    
                    Create a compelling narrative that addresses their specific challenges
                    and demonstrates clear understanding of their context.
                    """,
                    expected_output="Personalized offer",
                    agent=self.agents['offer_creator']
                )
            )
        
        return tasks

    @property
    def crew(self):
        return Crew(
            agents=list(self.agents.values()),
            tasks=self.create_tasks(),
            process=Process[self.crew_config['process']['type']],
            verbose=self.crew_config['process']['verbose']
        )

    def calculate_costs(self, crew_usage_metrics, model="gpt-4o-mini", use_batch=False, use_cached=False):
        """
        Calculate the costs based on crew usage metrics and token pricing.
        
        Parameters:
        - crew_usage_metrics: Dictionary containing usage metrics
        - model: Model name (default: gpt-4o-mini)
        - use_batch: Whether to use Batch API pricing
        - use_cached: Whether to use cached prompt pricing
        """
        pricing = self.pricing_config.get(model)
        if not pricing:
            print(f"Warning: Unknown model {model}, using gpt-4o-mini pricing")
            pricing = self.pricing_config['gpt-4o-mini']
        
        prompt_tokens = crew_usage_metrics.get('prompt_tokens', 0)
        completion_tokens = crew_usage_metrics.get('completion_tokens', 0)
        
        # Determine input price based on batch/cache status
        if use_batch:
            input_price = pricing['batch_input_price']
            output_price = pricing['batch_output_price']
        elif use_cached:
            input_price = pricing['cached_input_price']
            output_price = pricing['output_price']
        else:
            input_price = pricing['input_price']
            output_price = pricing['output_price']
        
        # Calculate costs
        input_cost = (prompt_tokens / pricing['unit_of_tokens']) * input_price
        output_cost = (completion_tokens / pricing['unit_of_tokens']) * output_price
        total_cost = input_cost + output_cost
        
        return {
            'total_cost': round(total_cost, 6),
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'model': model,
            'pricing_type': 'batch' if use_batch else 'cached' if use_cached else 'standard'
        }

    def run(self):
        """Run the crew and calculate costs"""
        result = self.crew.kickoff()
        
        # Check if usage metrics exist
        if hasattr(self.crew, 'usage_metrics') and self.crew.usage_metrics:
            # Calculate and print costs for both standard and batch pricing
            standard_costs = self.calculate_costs(self.crew.usage_metrics)
            batch_costs = self.calculate_costs(self.crew.usage_metrics, use_batch=True)
            
            print("\nUsage Statistics:")
            print(f"Model: {standard_costs['model']}")
            print(f"Prompt Tokens: {standard_costs['prompt_tokens']:,}")
            print(f"Completion Tokens: {standard_costs['completion_tokens']:,}")
            
            print(f"\nStandard Pricing:")
            print(f"Input Cost: ${standard_costs['input_cost']:.6f}")
            print(f"Output Cost: ${standard_costs['output_cost']:.6f}")
            print(f"Total Cost: ${standard_costs['total_cost']:.6f}")
            
            print(f"\nBatch API Pricing (50% discount):")
            print(f"Input Cost: ${batch_costs['input_cost']:.6f}")
            print(f"Output Cost: ${batch_costs['output_cost']:.6f}")
            print(f"Total Cost: ${batch_costs['total_cost']:.6f}")
        else:
            print("\nNo usage metrics available for cost calculation")
        
        return result

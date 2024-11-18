# crew.py

from crewai import Agent, Crew, Process, Task, LLM
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
        
        # Load configurations
        config_dir = Path(__file__).parent / "config"
        
        # Load crew configuration
        with open(config_dir / "crew.yaml", 'r') as f:
            self.crew_config = yaml.safe_load(f)
            
        # Load ICP configuration
        with open(config_dir / "config.yaml", 'r') as f:
            self.icp_config = yaml.safe_load(f)
        
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

        # Initialize tools with error checking
        try:
            self.tools = {
                'proxycurl_tool': ProxycurlTool(llm=self.llm),
                'company_data_tool': CompanyDataTool(llm=self.llm),
                'news_tool': NewsTool(llm=self.llm),
                'reddit_tool': RedditTool(llm=self.llm),
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
        batch_size = self.crew_config.get('batch_size', 5)
        tasks = []
        
        # Create lead analysis tasks
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            tasks.append(
                Task(
                    description=f"""
                    Analyze this batch of leads and their companies for ICP fit. Follow these steps exactly:

                    1. Company Website Analysis:
                       a. Use CompanyDataTool.get_company_data(company_website) to analyze each company's website
                       b. Extract key company insights:
                          - Products and services offered
                          - Technologies mentioned on site
                          - Company mission and vision
                          - Self-reported company size
                          - Key clients or partners mentioned
                          - Industry focus and target market

                    2. Individual Analysis:
                       a. Use ProxycurlTool.get_linkedin_profile(linkedin_url) for each lead
                       b. Extract key individual insights:
                          - Career progression and experience
                          - Skills and expertise
                          - Decision-making authority
                          - Department size and scope
                    
                    3. Score each opportunity using combined data:
                       
                       Company Website Indicators (40%):
                       - Product/service alignment with our solution
                       - Technology stack mentions
                       - Target market overlap
                       - Company maturity indicators
                       - Client profile mentions
                       
                       Role Seniority (30%):
                       - Decision-making authority
                       - Budget control indicators
                       - Team size and scope
                       - Relevant experience
                       
                       Technical Fit (30%):
                       - Technology alignment
                       - Integration possibilities
                       - Existing tool mentions
                       - Digital maturity signals

                    LEADS:
                    {batch}
                    
                    SCORING CRITERIA:
                    {icp_criteria}
                    
                    4. For each opportunity, provide:
                       - Website analysis insights
                       - LinkedIn profile analysis
                       - Technical compatibility assessment
                       - Detailed scoring breakdown
                       - Final weighted score
                    
                    5. Store complete results in Airtable
                    
                    Return a comprehensive analysis summary for this batch.
                    """,
                    expected_output=f"Detailed analysis summary with website and LinkedIn insights for leads {i+1} to {min(i+batch_size, len(leads))}",
                    agent=self.agents['customer_icp']
                )
            )
        
        # Add remaining tasks
        tasks.extend([
            Task(
                description="Identify industry pain points using the provided keywords.",
                expected_output="A comprehensive list of industry pain points and trends.",
                agent=self.agents['pain_point']
            ),
            Task(
                description="Customize solution templates based on identified pain points.",
                expected_output="Customized solution templates that address identified pain points.",
                agent=self.agents['solution_templates']
            ),
            Task(
                description="Generate personalized offers and email drafts.",
                expected_output="Personalized offer documents and email drafts for each qualified lead.",
                agent=self.agents['offer_creator']
            )
        ])
        
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
        
        return result

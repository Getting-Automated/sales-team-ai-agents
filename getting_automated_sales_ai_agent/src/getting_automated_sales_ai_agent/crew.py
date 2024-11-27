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
        # print(f"\nDEBUG: Creating tasks with ICP config keys: {self.icp_config.keys()}")
        
        # Get the customer_icp section
        icp_config = self.icp_config.get('customer_icp', {})
        # print(f"DEBUG: Using ICP config: {json.dumps(icp_config, indent=2)}")
        tasks = []
        
        for lead in leads:
            # print(f"\nDEBUG: Processing lead: {json.dumps(lead, indent=2)}")
            # print(f"\nCreating tasks for lead: {lead.get('name')} at {lead.get('company')}")
            
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
            try:
                task_description = f"""
                Analyze this lead and their company for ICP fit. Follow these steps exactly:
                1. Company Website Analysis: Use CompanyDataTool for domain: {domain}
                2. Individual Analysis: Use ProxycurlTool for LinkedIn: {lead.get('linkedin_url')}
                3. Score this opportunity using the provided criteria
                4. Provide a detailed assessment of their tech stack and growth stage
                
                LEAD DATA:
                {json.dumps(lead, indent=2)}
                
                ICP PROFILE OVERVIEW:
                {icp_config.get('profile_overview', 'No profile overview available')}
                
                SCORING WEIGHTS:
                Individual: {icp_config.get('weights', {}).get('individual', 0)}%
                Company: {icp_config.get('weights', {}).get('company', 0)}%
                Technical: {icp_config.get('weights', {}).get('technical', 0)}%
                Market: {icp_config.get('weights', {}).get('market', 0)}%
                
                TARGET CRITERIA:
                Industries: {', '.join(icp_config.get('criteria', {}).get('industries', []))}
                Business Models: {', '.join(icp_config.get('criteria', {}).get('business_models', []))}
                Technologies: {', '.join(icp_config.get('criteria', {}).get('technologies', []))}
                Locations: {', '.join(icp_config.get('criteria', {}).get('locations', []))}
                Growth Stages: {', '.join(icp_config.get('criteria', {}).get('growth_stages', []))}
                
                ROLE REQUIREMENTS:
                Job Titles: {', '.join(icp_config.get('job_titles', []))}
                Decision Authority: {', '.join(icp_config.get('decision_making_authority', []))}
                Target Departments: {', '.join(icp_config.get('target_departments', []))}
                
                SIZE REQUIREMENTS:
                Employee Count: {icp_config.get('minimum_requirements', {}).get('employee_count_min', 0)} - {icp_config.get('minimum_requirements', {}).get('employee_count_max', 0)}
                """
                
                icp_analysis_task = Task(
                    description=task_description,
                    agent=self.agents['customer_icp_agent']
                )
                tasks.append(icp_analysis_task)
                
                # Task 2: Pain Point Analysis
                pain_point_task = Task(
                    description=f"""
                    Analyze the company's pain points based on their profile and industry:
                    1. Research common challenges in their industry
                    2. Identify specific pain points from their tech stack and growth stage
                    3. Prioritize pain points based on our solution's capabilities
                    
                    Company: {lead.get('company')}
                    Industry: {lead.get('industry')}
                    Tech Stack: {lead.get('technologies')}
                    """,
                    agent=self.agents['pain_point_agent']
                )
                tasks.append(pain_point_task)
                
                # Task 3: Solution Template Customization
                solution_task = Task(
                    description=f"""
                    Customize our solution templates based on:
                    1. The ICP analysis results
                    2. Identified pain points
                    3. Company's specific context and needs
                    
                    Focus on demonstrating clear value and ROI.
                    """,
                    agent=self.agents['solution_templates_agent']
                )
                tasks.append(solution_task)
                
                # Task 4: Email Campaign Generation
                email_task = Task(
                    description=f"""
                    Generate a personalized cold email sequence:
                    1. Create an initial email focusing on their specific pain points
                    2. Prepare two follow-up templates
                    3. Ensure each email is unique and builds on previous context
                    
                    Lead Context:
                    Name: {lead.get('name')}
                    Role: {lead.get('role')}
                    Company: {lead.get('company')}
                    Industry: {lead.get('industry')}
                    
                    Use the identified pain points and customized solution to craft compelling messages.
                    Keep emails concise, professional, and focused on value.
                    """,
                    agent=self.agents['email_campaign_agent']
                )
                tasks.append(email_task)
                
            except Exception as e:
                print(f"Error creating tasks for lead {lead.get('name')}: {str(e)}")
                continue
        
        return tasks

    @property
    def crew(self):
        # Get all agents except manager
        worker_agents = [
            agent for name, agent in self.agents.items()
            if name != 'manager'
        ]
        
        # Create manager agent with delegation enabled
        manager = Agent(
            role="Sales Process Manager",
            goal="Coordinate and oversee the entire sales evaluation and proposal process",
            backstory="You are an expert sales operations manager who coordinates complex B2B sales processes. You excel at orchestrating multiple specialists to evaluate prospects and create compelling outreach campaigns.",
            allow_delegation=True,  # Enable delegation
            verbose=self.crew_config['process']['verbose'],
            llm=self.llm
        )

        # Enable delegation for worker agents
        for agent in worker_agents:
            agent.allow_delegation = True
        
        # Create the crew with manager agent
        return Crew(
            agents=worker_agents,
            tasks=self.create_tasks(),
            process=Process[self.crew_config['process']['type']],
            manager_agent=manager,
            verbose=self.crew_config['process']['verbose']
        )

    def process_lead(self, lead_data):
        """Process a lead through the complete sales workflow"""
        results = {}
        
        # Step 1: Company Evaluation
        company_task = Task(
            description="""Evaluate the company against our criteria. Focus on:
            - Industry alignment
            - Company size and growth stage
            - Location and market presence
            - Technical infrastructure""",
            context={"lead_data": lead_data},
            agent=self.agents['company_evaluator']
        )
        company_result = self.crew.execute_task(company_task)
        results['company_evaluation'] = company_result
        
        # Step 2: Individual Evaluation
        individual_task = Task(
            description="""Evaluate the individual prospect. Consider:
            - Role and decision-making authority
            - Department and responsibilities
            - Professional background and experience
            - Potential influence in buying process""",
            context={"lead_data": lead_data},
            agent=self.agents['individual_evaluator']
        )
        individual_result = self.crew.execute_task(individual_task)
        results['individual_evaluation'] = individual_result
        
        # Only proceed if both evaluations are positive
        if "recommend proceeding" in company_result.lower() and "recommend proceeding" in individual_result.lower():
            # Step 3: Pain Point Analysis
            pain_point_task = Task(
                description="""Analyze industry and company-specific pain points. Focus on:
                - Common challenges in their industry
                - Specific issues based on company size
                - Technical and operational bottlenecks
                - Growth-related pain points""",
                context={
                    "lead_data": lead_data,
                    "company_evaluation": company_result,
                    "individual_evaluation": individual_result
                },
                agent=self.agents['pain_point_analyst']
            )
            pain_points = self.crew.execute_task(pain_point_task)
            results['pain_points'] = pain_points
            
            # Step 4: Create Customized Offer
            offer_task = Task(
                description="""Create a customized offer based on all analyses. Include:
                - Specific solutions for identified pain points
                - Value propositions aligned with their needs
                - ROI calculations and benefits
                - Implementation approach""",
                context={
                    "lead_data": lead_data,
                    "company_evaluation": company_result,
                    "individual_evaluation": individual_result,
                    "pain_points": pain_points
                },
                agent=self.agents['offer_creator']
            )
            offer = self.crew.execute_task(offer_task)
            results['offer'] = offer
            
            # Step 5: Generate Email Campaign
            campaign_task = Task(
                description="""Create a multi-step email campaign sequence that:
                - Personalizes messaging based on the individual's role
                - Addresses specific pain points identified
                - Presents the customized offer effectively
                - Includes follow-up strategy and timing""",
                context={
                    "lead_data": lead_data,
                    "company_evaluation": company_result,
                    "individual_evaluation": individual_result,
                    "pain_points": pain_points,
                    "offer": offer
                },
                agent=self.agents['email_campaign']
            )
            campaign = self.crew.execute_task(campaign_task)
            results['email_campaign'] = campaign
            
            # Store results in Airtable
            try:
                self.agents['airtable_tool']._run('create', 'CampaignsTable', {
                    'lead_name': lead_data.get('name'),
                    'company': lead_data.get('company'),
                    'evaluations': {
                        'company': company_result,
                        'individual': individual_result
                    },
                    'pain_points': pain_points,
                    'offer': offer,
                    'campaign': campaign,
                    'status': 'ready_to_send'
                })
            except Exception as e:
                print(f"Error storing campaign in Airtable: {str(e)}")
            
            return results
        else:
            return {
                'company_evaluation': company_result,
                'individual_evaluation': individual_result,
                'status': 'Lead does not meet criteria. No further action taken.'
            }

    def calculate_costs(self, crew_usage_metrics, model="gpt-4o", use_batch=False, use_cached=False):
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
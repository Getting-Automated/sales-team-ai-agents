# crew.py

from crewai import Agent, Crew, Process, Task, LLM
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import yaml
import json
from litellm import completion
from datetime import datetime

# Import tools
from .tools.proxycurl_tool import ProxycurlTool
from .tools.company_data_tool import CompanyDataTool
from .tools.reddit_tool import RedditTool
from .tools.airtable_tool import AirtableTool
from .tools.perplexity_tool import PerplexityTool
from .tools.openai_tool import OpenAITool

# Import agents
from .agents.pain_point_agent import get_pain_point_agent
from .agents.email_campaign_agent import get_email_campaign_agent

# Import token tracker
from .utils.token_tracker import TokenTracker

class GettingAutomatedSalesAiAgent:
    """GettingAutomatedSalesAiAgent crew"""

    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize token tracker
        self.token_tracker = TokenTracker()
        
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
        
        # Initialize LLM using CrewAI's LLM class with provider prefix and token tracking
        self.llm = LLM(
            model="openai/gpt-4o",
            temperature=0.7,
            api_key=os.getenv('OPENAI_API_KEY'),
            callbacks=[self.token_tracker.callback]  # Add token tracking callback
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
        try:
            # Initialize agents dictionary
            agents = {}
            
            # Initialize manager agent without tools
            manager_config = self.crew_config['manager']
            self.manager = Agent(
                role=manager_config['role'],
                goal=manager_config['goal'],
                backstory=manager_config['backstory'],
                llm=self.llm,
                allow_delegation=True,
                memory=True
            )
                
            # Create data manager agent
            agents['data_manager'] = Agent(
                role=self.crew_config['data_manager']['role'],
                goal=self.crew_config['data_manager']['goal'],
                backstory=self.crew_config['data_manager']['backstory'],
                tools=[self.tools['airtable_tool']],
                llm=self.llm
            )
            
            # Create data enricher agent
            agents['data_enricher'] = Agent(
                role=self.crew_config['data_enricher']['role'],
                goal=self.crew_config['data_enricher']['goal'],
                backstory=self.crew_config['data_enricher']['backstory'],
                tools=[self.tools['proxycurl_tool']],
                llm=self.llm
            )
            
            # Create individual evaluator agent
            agents['individual_evaluator'] = Agent(
                role=self.crew_config['individual_evaluator']['role'],
                goal=self.crew_config['individual_evaluator']['goal'],
                backstory=self.crew_config['individual_evaluator']['backstory'],
                tools=[self.tools['openai_tool']],
                llm=self.llm
            )
            
            # Create company evaluator agent
            agents['company_evaluator'] = Agent(
                role=self.crew_config['company_evaluator']['role'],
                goal=self.crew_config['company_evaluator']['goal'],
                backstory=self.crew_config['company_evaluator']['backstory'],
                tools=[self.tools['company_data_tool'], self.tools['perplexity_tool']],
                llm=self.llm
            )

            # Add pain point identification agent
            agents['pain_point_agent'] = Agent(
                role=self.crew_config['pain_point_agent']['role'],
                goal=self.crew_config['pain_point_agent']['goal'],
                backstory=self.crew_config['pain_point_agent']['backstory'],
                tools=[self.tools['perplexity_tool'], self.tools['openai_tool']],  
                llm=self.llm,
                verbose=self.crew_config['pain_point_agent']['verbose']
            )
            
            # Add email campaign generation agent
            agents['email_campaign_agent'] = Agent(
                role=self.crew_config['email_campaign_agent']['role'],
                goal=self.crew_config['email_campaign_agent']['goal'],
                backstory=self.crew_config['email_campaign_agent']['backstory'],
                tools=[self.tools['openai_tool']],  
                llm=self.llm,
                verbose=self.crew_config['email_campaign_agent']['verbose']
            )
            
            return agents
            
        except KeyError as e:
            print(f"Error initializing agents: Missing configuration for {str(e)}")
            raise
        except Exception as e:
            print(f"Error initializing agents: {str(e)}")
            raise

    def create_tasks(self):
        """Create tasks for processing leads"""
        if not self.inputs.get('leads'):
            raise ValueError("No leads data provided to analyze")
        
        tasks = []
        for lead in self.inputs['leads']:
            # Use email as unique identifier
            lead_id = f"LEAD_{lead.get('email', '').replace('@', '_at_').replace('.', '_dot_')}"
            
            # Create initial task context
            task_context = {
                'description': f"Context for lead {lead.get('name')}",
                'expected_output': "Lead and configuration data",
                'lead': lead,
                'config': self.icp_config,
                'lead_id': lead_id,
                'airtable_record_id': None  # Will be updated after storage task
            }
            
            # Store Lead Task - Initial storage without Proxycurl data
            store_task = Task(
                description=f"""
                Store or update the following lead data in Airtable:

                Lead Data:
                - Email: {lead.get('email')}
                - Name: {lead.get('name')}
                - Company: {lead.get('company')}
                - Role: {lead.get('role')}
                - LinkedIn URL: {lead.get('linkedin_url', '')}
                - Company LinkedIn: {lead.get('company_linkedin_url', '')}
                - Raw Data: {json.dumps(lead)}

                Steps:
                1. First, search for this exact email in Airtable:
                   action: search
                   table_name: Leads
                   search_field: Email
                   search_value: {lead.get('email')}
                
                2. If not found, create a new record with these exact values:
                   action: create
                   table_name: Leads
                   data:
                     Email: {lead.get('email')}
                     Name: {lead.get('name')}
                     Company: {lead.get('company')}
                     Role: {lead.get('role')}
                     LinkedIn URL: {lead.get('linkedin_url', '')}
                     Company LinkedIn: {lead.get('company_linkedin_url', '')}
                     Individual Evaluation Status: Not Started
                     Company Evaluation Status: Not Started
                     Raw Data: {json.dumps(lead)}
                
                3. Return the Airtable record ID and current evaluation statuses.
                """,
                expected_output="Airtable record ID and evaluation statuses",
                agent=self.agents['data_manager'],
                context=[task_context]
            )
            tasks.append(store_task)

            # Proxycurl Enrichment Task
            proxycurl_task = Task(
                description=f"""
                Enrich the lead data using the proxycurl_tool.
                
                LinkedIn URL to analyze: {lead.get('linkedin_url', '')}
                
                Steps:
                1. Use the proxycurl_tool to fetch data for the LinkedIn URL above
                2. If the URL is empty or invalid, return an empty result
                3. Return the enriched data in this exact JSON format:
                {{
                    "success": true/false,
                    "data": <complete proxycurl response>,
                    "error": "<error message if any>"
                }}
                
                Lead context:
                - Name: {lead.get('name')}
                - Company: {lead.get('company')}
                - Role: {lead.get('role')}
                """,
                expected_output="Enriched lead data from Proxycurl in JSON format",
                agent=self.agents['data_enricher'],
                context=[store_task]
            )
            tasks.append(proxycurl_task)

            # Update Proxycurl Data Task
            update_proxycurl_task = Task(
                description=f"""
                Store the COMPLETE Proxycurl Result in Airtable exactly as received.
                
                Steps:
                1. Get the record ID from the store_task context
                2. Get the Proxycurl data from proxycurl_task context
                3. Update the Airtable record with:
                   action: update
                   table_name: Leads
                   record_id: <from store_task>
                   data:
                     Proxycurl Result: <complete proxycurl JSON response>
                     Enrichment Status: <"Success" or "Failed">
                     Last Enriched: <current date in YYYY-MM-DD format>
                
                IMPORTANT:
                - Store the COMPLETE JSON response as received
                - Do not modify or parse the data
                - Include success/failure status
                """,
                expected_output="Updated Airtable record with complete Proxycurl JSON data",
                agent=self.agents['data_manager'],
                context=[store_task, proxycurl_task]
            )
            tasks.append(update_proxycurl_task)

            # Individual Evaluation Task
            indiv_eval_task = Task(
                description=f"""
                {self.crew_config['individual_evaluator']['backstory']}
                
                Goal: {self.crew_config['individual_evaluator']['goal']}
                
                IMPORTANT: The Proxycurl data is in your context from proxycurl_task.output.
                The data will be in this format:
                {{
                    "success": true/false,
                    "data": <complete proxycurl response>,
                    "error": "<error message if any>"
                }}
                
                DO NOT try to fetch new data from LinkedIn directly.
                
                Evaluate {lead.get('name')} from {lead.get('company')} using:
                1. Initial Data:
                   - Name: {lead.get('name')}
                   - Company: {lead.get('company')}
                   - Role: {lead.get('role')}
                   - LinkedIn: {lead.get('linkedin_url', '')}
                
                2. Enriched Data:
                   Extract these details from proxycurl_task.output.data:
                   
                   a) Role and Seniority:
                      - Current title and level
                      - Years of experience
                      - Career progression
                   
                   b) Decision-Making Authority:
                      - Position in organization
                      - Team size and scope
                      - Budget responsibility indicators
                   
                   c) Department and Function:
                      - Current department
                      - Primary function
                      - Areas of responsibility
                   
                   d) Skills and Experience:
                      - Technical skills
                      - Industry expertise
                      - Relevant certifications
                
                Compare against ICP criteria:
                - Target Roles: {', '.join(self.icp_config.get('target_roles', []))}
                - Departments: {', '.join(self.icp_config.get('departments', []))}
                - Seniority Levels: {', '.join(self.icp_config.get('seniority_levels', []))}
                - Required Skills: {', '.join(self.icp_config.get('required_skills', []))}
                
                First, check if proxycurl_task.output.success is true.
                If true, analyze the data in proxycurl_task.output.data.
                If false, note the error and evaluate based on available information.
                
                Provide your evaluation in this exact JSON format:
                {{
                    "overall_score": <number 0-100>,
                    "role_match": {{
                        "score": <number 0-100>,
                        "analysis": "<detailed analysis of role match>"
                    }},
                    "authority_match": {{
                        "score": <number 0-100>,
                        "analysis": "<detailed analysis of authority match>"
                    }},
                    "department_match": {{
                        "score": <number 0-100>,
                        "analysis": "<detailed analysis of department match>"
                    }},
                    "skills_match": {{
                        "score": <number 0-100>,
                        "analysis": "<detailed analysis of skills match>"
                    }},
                    "detailed_analysis": "<comprehensive analysis of all factors>",
                    "recommendation": "<clear recommendation for proceeding with this lead>"
                }}
                """,
                expected_output="Individual evaluation report with ICP alignment score in JSON format",
                agent=self.agents['individual_evaluator'],
                context=[store_task, proxycurl_task, update_proxycurl_task]
            )
            tasks.append(indiv_eval_task)

            # Update Individual Evaluation Task
            update_indiv_task = Task(
                description=f"""
                Update the lead record in Airtable with the individual evaluation results.
                
                Use the evaluation results from the previous task to update these fields:
                1. Individual Score: Convert score to a number (e.g., "90/100" becomes 90)
                2. Individual Analysis
                3. Individual Evaluation Status: Set to "Completed"
                4. Role Match Score: Convert score to a number (e.g., "High" = 90)
                5. Authority Match Score: Convert score to a number (e.g., "High" = 90)
                6. Department Match Score: Convert score to a number (e.g., "High" = 90)
                7. Skills Match Score: Convert score to a number (e.g., "High" = 90)
                8. Lead Tier: Must be exactly one of ["High", "Medium", "Low"]
                9. Last Evaluated: Use current date in ISO format (YYYY-MM-DD)
                
                Score Conversion Guide:
                - "High" or "Strong" = 90
                - "Medium" or "Moderate" = 70
                - "Low" or "Weak" = 30
                
                Airtable record ID is available in the task context.

                Validate that the record actually get updated in Airtable before proceeding.
                """,
                expected_output="Updated Airtable record with individual evaluation",
                agent=self.agents['data_manager'],
                context=[store_task, indiv_eval_task]
            )
            tasks.append(update_indiv_task)
            
            # Company Evaluation Task
            company_eval_task = Task(
                description=f"""
                {self.crew_config['company_evaluator']['backstory']}
                
                Goal: {self.crew_config['company_evaluator']['goal']}
                
                Evaluate company {lead.get('company')} against ICP criteria:
                - Target Industries: {', '.join(self.icp_config.get('target_industries', []))}
                - Industries: {', '.join(self.icp_config.get('industries', []))}
                - Business Models: {', '.join(self.icp_config.get('business_models', []))}
                - Company Size: {self.icp_config.get('company_size', {})}
                - Technologies: {', '.join(self.icp_config.get('technologies', []))}
                - Growth Stages: {', '.join(self.icp_config.get('growth_stages', []))}
                - Employee Count Range: {self.icp_config.get('minimum_requirements', {}).get('employee_count_min')} - {self.icp_config.get('minimum_requirements', {}).get('employee_count_max')}
                
                Company Data: {json.dumps(lead, indent=2)}
                
                1. Industry alignment
                2. Company size match
                3. Location/market presence
                4. Growth indicators
                5. Technology stack
                6. Business model alignment
                
                Provide:
                1. Overall company ICP alignment score (0-100)
                2. Detailed analysis of company fit
                3. Specific insights about growth potential
                4. Recommendation for engagement strategy
                
                Base your evaluation on both the initial company data and the enriched Proxycurl data.
                """,
                expected_output="Company evaluation report with ICP alignment score",
                agent=self.agents['company_evaluator'],
                context=[store_task, update_proxycurl_task, indiv_eval_task]
            )
            tasks.append(company_eval_task)

            # Update Company Evaluation Task
            update_company_task = Task(
                description=f"""
                Update the lead record in Airtable with the company evaluation results.
                
                Use the evaluation results from the previous task to update these fields:
                1. Company Score: Convert score to a number (e.g., "85/100" becomes 85)
                2. Company Analysis
                3. Company Evaluation Status: Set to "Completed"
                4. Industry Match Score: Convert score to a number (e.g., "90/100" becomes 90)
                5. Size Match Score: Convert score to a number (e.g., "85/100" becomes 85)
                6. Location Match Score: Convert score to a number (e.g., "80/100" becomes 80)
                7. Growth Match Score: Convert score to a number (e.g., "88/100" becomes 88)
                8. Last Evaluated: Use current date in ISO format (YYYY-MM-DD)
                
                All scores should be numbers between 0 and 100, not strings.
                Dates should be in ISO format (YYYY-MM-DD).
                
                Airtable record ID is available in the task context.

                Ensure that you check with the Data Manager that this record gets updated within Airtable.
                """,
                expected_output="Updated Airtable record with company evaluation",
                agent=self.agents['data_manager'],
                context=[store_task, company_eval_task]
            )
            tasks.append(update_company_task)
        
        # Pain Point Analysis Task (for qualified leads)
        pain_point_task = Task(
            description=f"""
            {self.crew_config['pain_point_agent']['backstory']}
            
            Goal: {self.crew_config['pain_point_agent']['goal']}
            
            Analyze pain points for {lead.get('company')} based on:
            1. Individual evaluation results from previous task
            2. Company evaluation results from previous task
            3. Industry context
            4. Company size and growth stage
            5. Technology stack
            
            Review the evaluation results from the individual and company evaluation tasks in your context.
            
            Provide:
            1. List of identified pain points
            2. Priority ranking for each pain point
            3. Evidence supporting each pain point
            4. Recommendations for addressing each pain point
            
            Base your analysis on the evaluation results and enriched data.
            """,
            expected_output="Pain point analysis with prioritized recommendations",
            agent=self.agents['pain_point_agent'],
            context=[store_task, indiv_eval_task, company_eval_task]
        )
        tasks.append(pain_point_task)

        # Email Campaign Task
        email_campaign_task = Task(
            description=f"""
            {self.crew_config['email_campaign_agent']['backstory']}
            
            Goal: {self.crew_config['email_campaign_agent']['goal']}
            
            Generate a personalized email campaign for {lead.get('name')} at {lead.get('company')} using:
            1. Individual evaluation insights from previous task
            2. Company evaluation insights from previous task
            3. Identified pain points from previous task
            4. Our solution's value proposition
            
            Lead Context:
            - Role: {lead.get('role')}
            - Industry: {lead.get('industry')}
            - Company Size: {lead.get('employees')}
            
            Review the pain points analysis from the previous task in your context.
            
            Create:
            1. Initial outreach email
            2. Follow-up sequence (2-3 emails)
            3. Specific value propositions for each email
            4. Call-to-action suggestions
            
            Ensure emails are:
            - Personalized to the lead's context
            - Address specific pain points
            - Include relevant social proof
            - Have clear next steps
            """,
            expected_output="Personalized email campaign sequence",
            agent=self.agents['email_campaign_agent'],
            context=[store_task, pain_point_task, indiv_eval_task, company_eval_task]
        )
        tasks.append(email_campaign_task)

        # Store Email Campaign Task
        store_campaign_task = Task(
            description=f"""
            Store the email campaign in Airtable.
            
            Update the lead record with:
            1. Email Campaign: Full campaign sequence
            2. Campaign Status: Ready
            3. Last Updated: Current date
            
            Airtable record ID is available in the task context.
            """,
            expected_output="Updated Airtable record with email campaign",
            agent=self.agents['data_manager'],
            context=[store_task, email_campaign_task]
        )
        tasks.append(store_campaign_task)
        
        
        return tasks

    @property
    def crew(self):
        """Create the crew with tasks"""
        print("\nCreating crew...")
        
        # Get list of worker agents (excluding manager)
        worker_agents = list(self.agents.values())
        
        # Use default process settings since process config is commented out
        process_type = Process.hierarchical
        verbose = True
        
        return Crew(
            agents=worker_agents,
            tasks=self.create_tasks(),
            process=process_type,
            manager_agent=self.manager,
            verbose=verbose
        )

    def run(self):
        """Execute the crew's tasks and return results"""
        try:
            # Create and run the crew
            crew_instance = self.crew
            results = crew_instance.kickoff()
            
            # Save token usage log
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_path = log_dir / f"token_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.token_tracker.save_usage_log(str(log_path))
            
            print("\nToken Usage Summary:")
            print(json.dumps(self.token_tracker.get_usage_summary(), indent=2))
            
            return results
            
        except Exception as e:
            print(f"Error executing crew tasks: {str(e)}")
            raise
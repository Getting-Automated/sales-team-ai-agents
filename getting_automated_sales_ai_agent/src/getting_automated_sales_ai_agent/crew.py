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
                verbose=self.crew_config['process']['verbose'],
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
            
            return agents
            
        except KeyError as e:
            print(f"Error initializing agents: Missing configuration for {str(e)}")
            raise
        except Exception as e:
            print(f"Error initializing agents: {str(e)}")
            raise

    def create_tasks(self):
        """Create tasks for processing leads"""
        tasks = []
        leads = self.inputs.get('leads', [])
        
        print(f"\nCreating tasks for {len(leads)} leads")
        
        for lead_id, lead in enumerate(leads):
            print(f"\nProcessing lead {lead_id + 1}/{len(leads)}:")
            print(f"Name: {lead.get('name')}")
            print(f"Email: {lead.get('email')}")
            print(f"Company: {lead.get('company')}")
            
            # Create initial task context
            task_context = {
                'description': f"Context for lead {lead.get('name')}",
                'expected_output': "Lead and configuration data",
                'lead': lead,
                'config': self.icp_config,
                'lead_id': lead_id,
                'airtable_record_id': None  # Will be updated after storage task
            }
            
            # Use email as unique identifier
            lead_id = f"LEAD_{lead.get('email', '').replace('@', '_at_').replace('.', '_dot_')}"
            
            # Store Lead Task - Initial storage and status check
            store_task = Task(
                description=f"""
                Check if this lead needs processing and store/update their data in Airtable.

                Steps:
                1. First, search for this exact email in Airtable:
                   action: search
                   table_name: Leads
                   search_field: Email
                   search_value: {lead.get('email')}
                
                3. If not found, create a new record with:
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
                   
                   Then return: {{"status": "process", "record_id": "<new_record_id>"}}
                """,
                expected_output="JSON with status and record info",
                agent=self.agents['data_manager'],
                context=[task_context]
            )
            tasks.append(store_task)

            # Only continue with remaining tasks if the store task output indicates processing
            task_output = store_task.output if hasattr(store_task, 'output') else None
            if isinstance(task_output, dict) and task_output.get('status') == 'skip':
                print(f"Skipping lead {lead.get('email')}: {task_output.get('message')}")
                continue

            # Proxycurl Enrichment Task
            proxycurl_task = Task(
                description=f"""
                Enrich the lead data using the proxycurl_tool.
                
                LinkedIn URL to analyze: {lead.get('linkedin_url', '')}
                
                Steps:
                1. Use the proxycurl_tool to fetch data for the LinkedIn URL above
                2. If the URL is empty or invalid, return an empty result
                3. Return the enriched data in a structured JSON format
                
                Lead context:
                - Name: {lead.get('name')}
                - Company: {lead.get('company')}
                - Role: {lead.get('role')}

                Ensure that your next step is to store the enriched data in Airtable in the Proxycurl Result field
                """,
                expected_output="Enriched lead data from Proxycurl",
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
                2. Update the Airtable record with:
                   action: update
                   table_name: Leads
                   data:
                     Proxycurl Result: <insert the ENTIRE Proxycurl JSON response as a string>
                
                IMPORTANT:
                - Do NOT parse or modify the Proxycurl data
                - Store the COMPLETE JSON response as a single string
                - Do NOT extract individual fields
                - The data should be stored exactly as received from the Proxycurl tool
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
                
                Use the enriched Proxycurl data from the previous task to evaluate:
                1. Role and seniority alignment
                2. Decision-making authority
                3. Department and function match
                4. Skills and experience match
                
                Provide:
                1. Overall ICP alignment score (0-100)
                2. Detailed analysis of fit against each criterion
                3. Recommendation for proceeding with this lead
                
                Base your evaluation on both the initial lead data and the enriched Proxycurl data.
                """,
                expected_output="Individual evaluation report with ICP alignment score",
                agent=self.agents['individual_evaluator'],
                context=[store_task, update_proxycurl_task]
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
        
        return tasks

    @property
    def crew(self):
        """Create and return the crew with hierarchical process"""
        # Get list of worker agents (excluding manager)
        worker_agents = list(self.agents.values())
        
        return Crew(
            agents=worker_agents,
            tasks=self.create_tasks(),
            process=Process.hierarchical,
            manager_agent=self.manager,
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
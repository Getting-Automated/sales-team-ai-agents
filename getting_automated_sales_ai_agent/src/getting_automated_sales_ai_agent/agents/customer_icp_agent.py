# agents/customer_icp_agent.py

from crewai import Agent
from ..tools.proxycurl_tool import ProxycurlTool
from ..tools.company_data_tool import CompanyDataTool
from ..tools.airtable_tool import AirtableTool
from ..tools.openai_tool import OpenAITool
import json

def customer_icp_agent_logic(self):
    # Access inputs
    lead_list = self.inputs.get('lead_list', [])
    customer_icp = self.config.get('customer_icp', {})
    use_case_type = self.config.get('use_case_type', [])
    if not lead_list:
        return "No leads provided."

    if not customer_icp:
        return "Customer ICP not provided."

    for lead in lead_list:
        # Check if the lead's use case matches the specified use_case_type
        lead_use_case = lead.get('use_case')
        if use_case_type and lead_use_case not in use_case_type:
            self.logger.info(f"Lead {lead.get('name')} does not match use case type. Skipping.")
            continue

        linkedin_url = lead.get('linkedin_url')
        if not linkedin_url:
            self.logger.warning("LinkedIn URL missing in lead data. Skipping.")
            continue

        # Get individual profile using ProxycurlTool
        individual_profile = self.proxycurl_tool._run(linkedin_url)
        if 'error' in individual_profile:
            self.logger.error(f"Error fetching profile for {lead.get('name')}: {individual_profile['error']}")
            continue

        # Merge individual profile with lead data from CSV
        individual_profile.update(lead)

        # Extract company domain
        company_domain = individual_profile.get('company_domain') or individual_profile.get('company', {}).get('website')
        if not company_domain:
            self.logger.warning(f"Company domain not found for lead {lead.get('name')}. Skipping.")
            continue

        # Get company data using CompanyDataTool
        company_profile = self.company_data_tool._run(company_domain)
        if 'error' in company_profile:
            self.logger.error(f"Error fetching company data for {lead.get('company_name')}: {company_profile['error']}")
            continue

        # Prepare analysis prompt using expanded Customer ICP
        analysis_prompt = f"""
As an expert sales analyst, evaluate the following lead against our Ideal Customer Profile (ICP). Consider each criterion carefully.

**Customer ICP:**
{json.dumps(customer_icp, indent=2)}

**Lead Profile:**
- Name: {lead.get('name')}
- Role: {lead.get('role')}
- Seniority: {lead.get('seniority')}
- Departments: {lead.get('departments')}
- Location: {lead.get('location')}

**Company Details:**
- Company: {lead.get('company')}
- Industry: {lead.get('industry')}
- Company Size: {lead.get('company_size')} employees
- Annual Revenue: {lead.get('annual_revenue')}
- Technologies Used: {lead.get('technologies')}
- Focus Areas: {lead.get('keywords')}
- Company Description: {lead.get('seo_description')}

**Online Presence:**
- LinkedIn: {lead.get('linkedin_url')}
- Company LinkedIn: {lead.get('company_linkedin')}
- Company Website: {lead.get('company_website')}

**Evaluation Instructions:**
1. ICP Alignment:
   - Job Level Match: {customer_icp.get('job_levels', [])}
   - Department Match: {customer_icp.get('departments', [])}
   - Company Size Match: {customer_icp.get('company_size', [])}
   - Industry Match: {customer_icp.get('industries', [])}

2. Technical Analysis:
   - Evaluate their tech stack compatibility
   - Identify potential integration points
   - Assess technical maturity

3. Business Context:
   - Analyze company scale and growth indicators
   - Identify potential pain points based on industry and size
   - Evaluate decision-making authority

Return a JSON object with the following structure:
{
    "lead_score": 1-10,
    "lead_tier": "A/B/C",
    "justification": "Detailed explanation of the scoring and tier assignment",
    "matching_criteria": [
        "Specific ICP criteria that match",
        "e.g., Company size within target range",
        "e.g., Decision maker in target department",
        "e.g., Tech stack compatibility"
    ],
    "technical_fit": {
        "score": 1-10,
        "analysis": "Detailed analysis of their current tech stack, integration potential, and technical maturity",
        "tech_stack_details": {
            "current_systems": ["List of current systems"],
            "integration_points": ["Potential integration points"],
            "technical_maturity": "Assessment of technical sophistication"
        }
    },
    "company_context": {
        "growth_stage": "Current company growth stage",
        "market_position": "Position in their market",
        "decision_makers": ["Relevant decision makers identified"],
        "budget_indicators": ["Indicators of budget availability"]
    },
    "next_steps": [
        "Specific actions based on ICP match",
        "e.g., Schedule technical assessment",
        "e.g., Connect with identified decision makers",
        "e.g., Prepare customized demo"
    ]
}
"""

        # Use OpenAITool for analysis
        try:
            analysis_result = self.openai_tool._run(
                prompt=analysis_prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse the JSON response
            try:
                # Handle potential text before or after JSON
                json_start = analysis_result.find('{')
                json_end = analysis_result.rfind('}') + 1
                if json_start >= 0 and json_end > 0:
                    analysis_json = analysis_result[json_start:json_end]
                    analysis = json.loads(analysis_json)
                else:
                    raise ValueError("No JSON found in response")
                
            except json.JSONDecodeError as e:
                print(f"Error parsing analysis result for lead {lead.get('name')}: {e}")
                print(f"Raw response: {analysis_result}")
                continue

            # Prepare data for Airtable
            lead_data = {
                'Name': lead.get('name'),
                'Email': lead.get('email'),
                'Company': lead.get('company'),
                'Role': lead.get('role'),
                'LeadScore': analysis.get('lead_score'),
                'LeadTier': analysis.get('lead_tier'),
                'Justification': analysis.get('justification'),
                'MatchingCriteria': json.dumps(analysis.get('matching_criteria', [])),
                'TechnicalFit': json.dumps(analysis.get('technical_fit', {})),
                'CompanyContext': json.dumps(analysis.get('company_context', {})),
                'NextSteps': json.dumps(analysis.get('next_steps', [])),
                'CompanySize': lead.get('company_size'),
                'Technologies': lead.get('technologies'),
                'AnnualRevenue': lead.get('annual_revenue'),
                'Location': lead.get('location'),
                'EnrichedProfile': json.dumps(lead)
            }

            # Store data in Airtable
            airtable_result = self.airtable_tool._run('create', 'LeadsTable', data=lead_data)
            if isinstance(airtable_result, dict) and 'error' in airtable_result:
                print(f"Error storing data in Airtable for lead {lead.get('name')}: {airtable_result['error']}")
            else:
                print(f"Lead data stored successfully for lead {lead.get('name')}.")

        except Exception as e:
            print(f"Error analyzing lead {lead.get('name')}: {str(e)}")
            continue

    return "Lead analysis completed and data stored in Airtable."

def get_customer_icp_agent(config, tools, llm):
    agent_conf = config['customer_icp_agent']
    agent_instance = Agent(
        llm=llm,
        tools=tools,
        **agent_conf
    )
    # Assign custom logic to the agent's run method
    agent_instance.run = customer_icp_agent_logic.__get__(agent_instance, Agent)
    return agent_instance

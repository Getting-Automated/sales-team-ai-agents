# agents/customer_icp_agent.py

from crewai import Agent, LLM
from tools.proxycurl_tool import ProxycurlTool
from tools.company_data_tool import CompanyDataTool
from tools.airtable_tool import AirtableTool
import os
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

**Individual Profile:**
{json.dumps(individual_profile, indent=2)}

**Company Profile:**
{json.dumps(company_profile, indent=2)}

**Evaluation Instructions:**
- **Job Level:** Does the lead's job title match any of the specified job levels?
- **Technical Expertise:** Is the lead technical or non-technical?
- **Department:** Is the lead part of the specified departments?
- **Company Technologies:** Does the company use or show interest in the specified technologies?
- **Company Challenges:** Is the company facing any of the specified challenges?

**Provide a comprehensive analysis considering the above points.**

**Response Format:**
{{
    "lead_score": ...,        # Integer between 0 and 100
    "lead_tier": "...",       # "High", "Medium", or "Low"
    "justification": "...",   # Detailed explanation of the evaluation
    "matching_criteria": {{   # Details of which criteria matched
        "job_level": "...",
        "technical_expertise": "...",
        "department": "...",
        "company_technologies": "...",
        "company_challenges": "..."
    }}
}}
"""

        # Analyze profiles using the agent's LLM
        analysis_result = self.llm.complete(analysis_prompt)
        try:
            # OpenAI's API may return extra text, so we attempt to extract the JSON part
            json_start = analysis_result.find('{')
            json_end = analysis_result.rfind('}') + 1
            analysis_json = analysis_result[json_start:json_end]
            analysis = json.loads(analysis_json)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing analysis result for lead {lead.get('name')}: {e}")
            continue

        # Prepare data for Airtable
        lead_data = {
            'Name': individual_profile.get('full_name') or individual_profile.get('name'),
            'Email': individual_profile.get('email'),
            'Company': individual_profile.get('company', {}).get('name') or individual_profile.get('company_name'),
            'Role': individual_profile.get('occupation') or individual_profile.get('role'),
            'LeadScore': analysis.get('lead_score'),
            'LeadTier': analysis.get('lead_tier'),
            'Justification': analysis.get('justification'),
            'MatchingCriteria': analysis.get('matching_criteria'),
            'EnrichedIndividualProfile': individual_profile,
            'EnrichedCompanyProfile': company_profile,
        }

        # Store data in Airtable using AirtableTool
        airtable_result = self.airtable_tool._run('create', 'LeadsTable', data=lead_data)
        if isinstance(airtable_result, dict) and 'error' in airtable_result:
            self.logger.error(f"Error storing data in Airtable for lead {lead.get('name')}: {airtable_result['error']}")
        else:
            self.logger.info(f"Lead data stored successfully for lead {lead.get('name')}.")

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

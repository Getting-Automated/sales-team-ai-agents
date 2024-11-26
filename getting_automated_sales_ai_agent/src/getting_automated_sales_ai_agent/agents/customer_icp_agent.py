# agents/customer_icp_agent.py

from crewai import Agent
from ..tools.proxycurl_tool import ProxycurlTool
from ..tools.company_data_tool import CompanyDataTool
from ..tools.airtable_tool import AirtableTool
from ..tools.openai_tool import OpenAITool
import json
from pathlib import Path
from datetime import datetime

def calculate_icp_score(self, lead_data, config):
    """Calculate ICP score based on category weights."""
    weights = config.get('weights', {
        'individual': 25,
        'company': 25,
        'technical': 25,
        'market': 25
    })
    
    # Normalize weights to percentages
    total_weight = sum(weights.values())
    normalized_weights = {k: (v / total_weight) * 100 for k, v in weights.items()}
    
    # Calculate score based on weights only
    total_score = sum(normalized_weights.values()) / len(normalized_weights)

    return {
        'total': round(total_score, 1),
        'breakdown': {
            'individual': round(normalized_weights['individual'], 1),
            'company': round(normalized_weights['company'], 1),
            'technical': round(normalized_weights['technical'], 1),
            'market': round(normalized_weights['market'], 1)
        }
    }

def get_recommendation(self, score):
    """Get recommendation based on ICP score."""
    if score >= 75:
        return {
            'recommendation': 'High-priority prospect - Perfect ICP match with strong potential for success. Immediate engagement recommended.',
            'priority': 'high'
        }
    elif score >= 50:
        return {
            'recommendation': 'Moderate fit - Good potential but may need specific focus areas. Consider targeted engagement strategy.',
            'priority': 'medium'
        }
    else:
        return {
            'recommendation': 'Low fit - Significant gaps in alignment. May not be ideal target at this time.',
            'priority': 'low'
        }

def customer_icp_agent_logic(self):
    """Main logic for customer ICP evaluation."""
    # Load ICP configuration
    config_path = Path(__file__).parent.parent / 'configs' / 'icp_config.json'
    if not config_path.exists():
        return "ICP configuration not found. Please set up the configuration using the web UI first."
    
    with open(config_path) as f:
        icp_config = json.load(f)
    
    # Access inputs
    lead_list = self.inputs.get('lead_list', [])
    if not lead_list:
        return "No leads provided."

    results = []
    for lead in lead_list:
        # Get individual profile using ProxycurlTool
        linkedin_url = lead.get('linkedin_url')
        if not linkedin_url:
            self.logger.warning("LinkedIn URL missing in lead data. Skipping.")
            continue

        individual_profile = self.proxycurl_tool._run(linkedin_url)
        if 'error' in individual_profile:
            self.logger.error(f"Error fetching profile for {lead.get('name')}: {individual_profile['error']}")
            continue

        # Merge individual profile with lead data
        lead_data = {**lead, **individual_profile}

        # Get company data
        company_domain = individual_profile.get('company_domain') or individual_profile.get('company', {}).get('website')
        if company_domain:
            company_profile = self.company_data_tool._run(company_domain)
            if not isinstance(company_profile, dict) or 'error' not in company_profile:
                lead_data.update(company_profile)

        # Calculate ICP score
        score_result = self.calculate_icp_score(lead_data, icp_config)
        recommendation = self.get_recommendation(score_result['total'])

        results.append({
            'lead': lead_data,
            'score': score_result,
            'recommendation': recommendation
        })

        # Store in Airtable
        try:
            self.airtable_tool._run('create', 'LeadsTable', data={
                'name': lead_data.get('name'),
                'company': lead_data.get('company'),
                'role': lead_data.get('role'),
                'department': lead_data.get('department'),
                'company_size': lead_data.get('company_size'),
                'industry': lead_data.get('industry'),
                'lead_score': round(score_result['total'], 2),
                'lead_tier': recommendation['priority'],
                'score_breakdown': score_result['breakdown'],
                'enriched_profile': lead_data
            })
        except Exception as e:
            self.logger.error(f"Error storing data in Airtable: {str(e)}")

    return {
        'evaluated_leads': results,
        'total_leads': len(results),
        'timestamp': datetime.now().isoformat()
    }

def get_customer_icp_agent(config, tools, llm):
    agent_conf = config['customer_icp_agent']
    agent_instance = Agent(
        llm=llm,
        tools=tools,
        **agent_conf
    )
    # Assign custom logic to the agent's run method
    agent_instance.run = customer_icp_agent_logic.__get__(agent_instance, Agent)
    agent_instance.calculate_icp_score = calculate_icp_score.__get__(agent_instance, Agent)
    agent_instance.get_recommendation = get_recommendation.__get__(agent_instance, Agent)
    return agent_instance

from crewai import Agent
from ..tools.company_data_tool import CompanyDataTool
from ..tools.perplexity_tool import PerplexityTool
from ..tools.openai_tool import OpenAITool

def calculate_technical_score(tech_data, config):
    """Calculate technical alignment score."""
    weights = {
        'tech_stack_match': 0.4,
        'integration_feasibility': 0.3,
        'infrastructure_compatibility': 0.3
    }
    
    scores = {
        'tech_stack_match': 0,
        'integration_feasibility': 0,
        'infrastructure_compatibility': 0
    }
    
    # Tech stack matching
    target_technologies = set(config['tags'].get('technologies', []))
    current_technologies = set(tech_data.get('technologies', []))
    
    if target_technologies:
        tech_match_percentage = len(current_technologies.intersection(target_technologies)) / len(target_technologies) * 100
        scores['tech_stack_match'] = tech_match_percentage
    
    # Integration feasibility (based on standard integrations)
    standard_integrations = tech_data.get('standard_integrations', [])
    if standard_integrations:
        scores['integration_feasibility'] = 100 if len(standard_integrations) > 0 else 50
    
    # Infrastructure compatibility
    cloud_ready = tech_data.get('cloud_ready', False)
    api_enabled = tech_data.get('api_enabled', False)
    
    if cloud_ready and api_enabled:
        scores['infrastructure_compatibility'] = 100
    elif cloud_ready or api_enabled:
        scores['infrastructure_compatibility'] = 75
    else:
        scores['infrastructure_compatibility'] = 25
    
    # Calculate weighted score
    total_score = sum(score * weights[key] for key, score in scores.items())
    
    return {
        'total': round(total_score, 1),
        'breakdown': {k: round(v, 1) for k, v in scores.items()}
    }

def get_technical_evaluator(config, tools, llm):
    """Create a technical evaluator agent."""
    return Agent(
        role="Technical Stack Analyst",
        goal="Evaluate technical alignment and integration potential with prospect's infrastructure",
        backstory="You are a technical architect with deep expertise in enterprise systems and integration. You assess technical stacks and identify opportunities for seamless integration.",
        tools=[
            tools['company_data_tool'],
            tools['perplexity_tool'],
            tools['openai_tool']
        ],
        llm=llm,
        verbose=config['process']['verbose']
    )

from crewai import Agent
from ..tools.proxycurl_tool import ProxycurlTool
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool

def calculate_individual_score(individual_data, config):
    """Calculate individual-level ICP score."""
    # Get individual weight from config
    individual_weight = config['weights'].get('individual', 39)  # Default to 39 if not found
    
    # Define component weights (normalized to total 100%)
    weights = {
        'role_match': 0.3 * individual_weight,
        'authority_match': 0.3 * individual_weight,
        'department_match': 0.2 * individual_weight,
        'skills_match': 0.2 * individual_weight
    }
    
    scores = {
        'role_match': 0,
        'authority_match': 0,
        'department_match': 0,
        'skills_match': 0
    }
    
    # Role matching
    if individual_data.get('job_title') in config['job_titles']:
        scores['role_match'] = 100
    
    # Authority matching - use decision_making_authority consistently
    if individual_data.get('decision_making_authority') in config['decision_making_authority']:
        scores['authority_match'] = 100
    
    # Department matching
    if individual_data.get('department') in config['target_departments']:
        scores['department_match'] = 100
    
    # Skills matching
    individual_skills = set(individual_data.get('skills', []))
    required_skills = set(config['required_skills'])
    if required_skills:
        skill_match_percentage = len(individual_skills.intersection(required_skills)) / len(required_skills) * 100
        scores['skills_match'] = skill_match_percentage
    
    # Calculate weighted score
    total_score = sum(score * weights[key] for key, score in scores.items())
    
    return {
        'total': round(total_score, 1),
        'breakdown': {k: round(v, 1) for k, v in scores.items()}
    }

def get_individual_evaluator(config, tools, llm):
    """Create an individual evaluator agent."""
    return Agent(
        role="Individual Fit Analyst",
        goal="Analyze individual-level ICP fit focusing on role alignment and decision-making authority",
        backstory="You are a talent assessment specialist who evaluates individual stakeholders within organizations. You analyze their roles, influence, and potential impact on purchasing decisions.",
        tools=[
            tools['proxycurl_tool'],
            tools['openai_tool'],
            tools['airtable_tool']
        ],
        llm=llm,
        verbose=config['process']['verbose']
    )

def evaluate_individual(task):
    """Evaluate an individual based on ICP criteria."""
    # Get first context item since we're passing a list
    context = task.context[0] if task.context else {}
    lead = context.get('lead', {})
    icp_config = context.get('icp_config', {})
    
    individual_data = {
        'job_title': lead.get('role', ''),
        'decision_making_authority': 'Final Decision Maker' if any(title in lead.get('role', '').lower() for title in ['cto', 'cio', 'coo', 'director']) else 'Key Influencer',
        'department': next((dept for dept in icp_config['target_departments'] if dept.lower() in lead.get('role', '').lower()), ''),
        'skills': []  # Skills would need to be extracted from LinkedIn or other sources
    }
    
    score = calculate_individual_score(individual_data, icp_config)
    
    return {
        'name': lead.get('name', ''),
        'score': score,
        'data': individual_data
    }

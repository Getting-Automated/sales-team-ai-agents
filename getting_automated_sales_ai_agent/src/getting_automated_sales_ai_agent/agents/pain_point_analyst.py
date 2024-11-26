from crewai import Agent
from ..tools.perplexity_tool import PerplexityTool
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool

def analyze_pain_points(company_data, individual_data, tech_data, config):
    """Analyze and score pain points."""
    pain_point_categories = {
        'technical': [],
        'operational': [],
        'growth': [],
        'market': []
    }
    
    # Technical pain points
    if tech_data.get('legacy_systems', []):
        pain_point_categories['technical'].append({
            'type': 'Legacy System Constraints',
            'severity': 'high',
            'impact': 'Limits innovation and integration capabilities'
        })
    
    # Operational pain points
    if company_data.get('employee_count', 0) > company_data.get('optimal_team_size', 0):
        pain_point_categories['operational'].append({
            'type': 'Resource Scaling',
            'severity': 'medium',
            'impact': 'Efficiency and coordination challenges'
        })
    
    # Growth pain points
    current_stage = company_data.get('growth_stage')
    if current_stage in config['tags'].get('growth_stages', []):
        pain_point_categories['growth'].append({
            'type': f'{current_stage} Growth Challenges',
            'severity': 'high',
            'impact': 'Scaling and expansion limitations'
        })
    
    # Market pain points
    for criteria in config['negative_criteria']:
        if criteria in company_data.get('challenges', []):
            pain_point_categories['market'].append({
                'type': criteria,
                'severity': 'high',
                'impact': 'Market position at risk'
            })
    
    return pain_point_categories

def get_pain_point_analyst(config, tools, llm):
    """Create a pain point analyst agent."""
    return Agent(
        role="Pain Point Analyst",
        goal="Identify and validate specific pain points across technical, operational, and business dimensions",
        backstory="You are a business consultant specializing in identifying organizational challenges. You excel at uncovering both obvious and hidden pain points that impact business performance.",
        tools=[
            tools['perplexity_tool'],
            tools['openai_tool'],
            tools['airtable_tool']
        ],
        llm=llm,
        verbose=config['process']['verbose']
    )

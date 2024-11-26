from crewai import Agent
from ..tools.company_data_tool import CompanyDataTool
from ..tools.perplexity_tool import PerplexityTool
from ..tools.airtable_tool import AirtableTool

def calculate_company_score(company_data, config):
    """Calculate company-level ICP score."""
    # Get company weight from config
    company_weight = config['weights'].get('company', 37)  # Default to 37 if not found
    
    # Define component weights (normalized to total 100%)
    weights = {
        'industry_match': 0.25 * company_weight,
        'size_match': 0.25 * company_weight,
        'location_match': 0.25 * company_weight,
        'growth_match': 0.25 * company_weight
    }
    
    scores = {
        'industry_match': 0,
        'size_match': 0,
        'location_match': 0,
        'growth_match': 0
    }
    
    # Industry matching
    if company_data.get('industry') in config['criteria']['industries']:
        scores['industry_match'] = 100
    
    # Size matching
    emp_count = company_data.get('employee_count', 0)
    min_emp = config['minimum_requirements'].get('employee_count_min', 0)
    max_emp = config['minimum_requirements'].get('employee_count_max', float('inf'))
    
    if min_emp <= emp_count <= max_emp:
        scores['size_match'] = 100
    
    # Location matching
    if company_data.get('location') in config['criteria']['locations']:
        scores['location_match'] = 100
    
    # Growth stage matching
    if company_data.get('growth_stage') in config['criteria']['growth_stages']:
        scores['growth_match'] = 100
    
    # Calculate weighted score
    total_score = sum(score * weights[key] for key, score in scores.items())
    
    return {
        'total': round(total_score, 1),
        'breakdown': {k: round(v, 1) for k, v in scores.items()}
    }

def get_company_evaluator(tools, llm, task):
    """Create a company evaluator agent."""
    icp_config = task.context.get('icp_config', {})
    return Agent(
        role="Company Fit Analyst",
        goal="Analyze company-level ICP fit based on size, industry, business model, and market presence",
        backstory="You are an expert business analyst specializing in company evaluation. You assess organizations based on their market position, growth trajectory, and alignment with target profiles.",
        tools=[
            tools['company_data_tool'],
            tools['perplexity_tool'],
            tools['airtable_tool']
        ],
        llm=llm,
        verbose=icp_config['process']['verbose']
    )

def evaluate_company(task):
    """Evaluate a company based on ICP criteria."""
    # Get first context item since we're passing a list
    context = task.context[0] if task.context else {}
    lead = context.get('lead', {})
    icp_config = context.get('icp_config', {})
    
    company_data = {
        'industry': lead.get('industry', ''),
        'employee_count': lead.get('employees', 0),
        'location': lead.get('company_location', ''),
        'growth_stage': 'Enterprise' if lead.get('employees', 0) > 250 else 'SMB'
    }
    
    score = calculate_company_score(company_data, icp_config)
    
    return {
        'company_name': lead.get('company', ''),
        'score': score,
        'data': company_data
    }

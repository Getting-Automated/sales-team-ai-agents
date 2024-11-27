from crewai import Agent
from ..tools.company_data_tool import CompanyDataTool
from ..tools.perplexity_tool import PerplexityTool
from ..tools.airtable_tool import AirtableTool
from datetime import datetime

class CompanyEvaluation:
    """Company-level evaluation logic"""
    
    @staticmethod
    def calculate_score(company_data, config):
        """Calculate company-level ICP score with detailed breakdown"""
        company_weight = config['weights'].get('company', 37)
        
        weights = {
            'industry_match': 0.25 * company_weight,
            'size_match': 0.25 * company_weight,
            'location_match': 0.25 * company_weight,
            'growth_match': 0.25 * company_weight
        }
        
        scores = {
            'industry_match': 100 if company_data.get('industry') in config['criteria']['industries'] else 0,
            'size_match': 100 if (
                config['minimum_requirements'].get('employee_count_min', 0) <= 
                company_data.get('employee_count', 0) <= 
                config['minimum_requirements'].get('employee_count_max', float('inf'))
            ) else 0,
            'location_match': 100 if company_data.get('location') in config['criteria']['locations'] else 0,
            'growth_match': 100 if company_data.get('growth_stage') in config['criteria']['growth_stages'] else 0
        }
        
        total_score = sum(score * (weights[key]/100) for key, score in scores.items())
        
        return {
            'total': round(total_score, 1),
            'breakdown': {
                k: {
                    'score': round(v, 1),
                    'weight': round(weights[k], 1)
                } for k, v in scores.items()
            }
        }
    
    @staticmethod
    def enrich_company_data(company_data, tools):
        """Enrich company data with additional research"""
        enriched_data = company_data.copy()
        
        try:
            # Get company info from CompanyDataTool
            if company_data.get('domain'):
                company_info = tools['company_data_tool'].get_company_info(company_data['domain'])
                enriched_data.update({
                    'tech_stack': company_info.get('technologies', []),
                    'funding_info': company_info.get('funding'),
                    'employee_growth': company_info.get('employee_growth'),
                    'company_details': company_info
                })
            
            # Get market research from Perplexity
            market_queries = [
                f"Latest market position and growth stage of {company_data['name']} in {company_data['industry']}",
                f"Recent news and developments about {company_data['name']} related to automation and technology",
                f"Competitive landscape for {company_data['name']} in {company_data['industry']}"
            ]
            
            market_research = {}
            for query in market_queries:
                try:
                    result = tools['perplexity_tool'].research(query)
                    market_research[query] = result
                except Exception as e:
                    print(f"Error in market research query: {str(e)}")
            
            enriched_data.update({
                'market_research': market_research,
                'market_position': market_research.get(market_queries[0], {}).get('market_position'),
                'growth_indicators': market_research.get(market_queries[0], {}).get('growth_indicators'),
                'competitive_context': market_research.get(market_queries[2], {})
            })
            
        except Exception as e:
            print(f"Error enriching company data: {str(e)}")
        
        return enriched_data

def evaluate_company(task):
    """Evaluate a company based on ICP criteria"""
    context = task.context[0] if isinstance(task.context, list) else task.context
    lead = context.get('lead', {})
    config = context.get('config', {}).get('customer_icp', {})
    tools = task.agent.tools
    
    try:
        # Search for existing lead
        search_result = tools['airtable_tool']._run(
            action="search",
            table_name="Leads",
            search_field="Email",
            search_value=lead.get('email')
        )
        
        airtable_record_id = None
        if search_result.get('record'):
            airtable_record_id = search_result['record_id']
        
        # Prepare initial company data
        company_data = {
            'name': lead.get('company', ''),
            'industry': lead.get('industry', ''),
            'company_size': lead.get('employees', 0),
            'revenue': lead.get('revenue', 0),
            'location': lead.get('company_location', ''),
            'technologies': lead.get('technologies', []),
            'company_linkedin_url': lead.get('company_linkedin_url', '')
        }
        
        # Enrich data
        enriched_data = CompanyEvaluation.enrich_company_data(company_data, tools)
        
        # Calculate score
        score = CompanyEvaluation.calculate_score(enriched_data, config)
        
        result = {
            'company_name': company_data['name'],
            'score': score,
            'enriched_data': enriched_data
        }
        
        # Update Airtable record with company evaluation results
        if airtable_record_id:
            tools['airtable_tool']._run(
                action="update",
                table_name="Leads",
                record_id=airtable_record_id,
                data={
                    'Company Score': score['total'],
                    'Industry Match Score': score['breakdown']['industry_match']['score'],
                    'Size Match Score': score['breakdown']['size_match']['score'],
                    'Location Match Score': score['breakdown']['location_match']['score'],
                    'Growth Match Score': score['breakdown']['growth_match']['score'],
                    'Company Analysis': str(score['breakdown']),
                    'Enriched Company Data': str(enriched_data),
                    'Company Evaluation Status': "Completed",
                    'Last Evaluated': datetime.now().strftime("%Y-%m-%d")
                }
            )
        
        return result
        
    except Exception as e:
        print(f"Error in company evaluation: {str(e)}")
        return {
            'error': str(e),
            'company_name': lead.get('company', 'Unknown'),
            'partial_data': company_data
        }

def get_company_evaluator(config, tools, llm):
    """Create a company evaluator agent"""
    return Agent(
        role="Company Fit Analyst",
        goal="Analyze company-level ICP fit based on size, industry, and market presence",
        backstory="""You are an expert business analyst specializing in company evaluation. 
        You assess organizations based on their market position, growth trajectory, technical 
        infrastructure, and alignment with target profiles.""",
        tools=[
            tools['company_data_tool'],
            tools['perplexity_tool'],
            tools['airtable_tool']
        ],
        llm=llm,
        verbose=config['process']['verbose']
    )

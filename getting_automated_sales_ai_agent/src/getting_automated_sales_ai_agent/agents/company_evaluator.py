from crewai import Agent
from ..tools.company_data_tool import CompanyDataTool
from ..tools.perplexity_tool import PerplexityTool
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

def get_company_evaluator(config, tools, llm):
    """Create a company evaluator agent"""
    class CompanyEvaluator(Agent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.company_data_tool = tools['company_data_tool']
            self.perplexity_tool = tools['perplexity_tool']

        def evaluate(self, task):
            """
            Evaluate a company against ICP criteria.
            Returns evaluation results without handling Airtable operations.
            """
            try:
                # Extract company data from task context
                lead_data = task.context[0].output.get('lead_data', {})
                company_data = {
                    'name': lead_data.get('company'),
                    'website': lead_data.get('company_website'),
                    'linkedin_url': lead_data.get('company_linkedin_url'),
                    'industry': lead_data.get('industry'),
                    'technologies': lead_data.get('technologies'),
                    'employees': lead_data.get('employees'),
                    'revenue': lead_data.get('revenue'),
                    'location': lead_data.get('company_location'),
                    'keywords': lead_data.get('keywords')
                }
                
                # Analyze company using Perplexity for market research
                market_analysis = self.perplexity_tool.research(
                    query=f"Analyze {company_data['name']} in terms of: "
                          f"1. Market position and growth trajectory "
                          f"2. Technology adoption and innovation "
                          f"3. Industry challenges and opportunities "
                          f"4. Recent company developments"
                )
                
                # Analyze company fit using Company Data Tool
                company_analysis = self.company_data_tool.analyze(
                    company_data=company_data,
                    analysis_type="icp_fit"
                )
                
                # Combine analyses into final evaluation
                evaluation = {
                    'company_name': company_data['name'],
                    'market_analysis': market_analysis,
                    'company_analysis': company_analysis,
                    'icp_alignment_score': company_analysis.get('alignment_score', 0),
                    'recommendation': company_analysis.get('recommendation', ''),
                    'key_factors': company_analysis.get('key_factors', []),
                    'evaluation_timestamp': datetime.now().isoformat()
                }
                
                return {
                    'status': 'success',
                    'evaluation': evaluation,
                    'message': 'Company evaluation completed successfully'
                }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Error evaluating company: {str(e)}'
                }

    return CompanyEvaluator(
        role="Company Fit Analyst",
        goal="Analyze company-level ICP fit based on size, industry, and market presence",
        backstory="""You are an expert business analyst specializing in company evaluation. 
        You assess organizations based on their market position, growth trajectory, technical 
        infrastructure, and alignment with target profiles.""",
        tools=[
            tools['company_data_tool'],
            tools['perplexity_tool']
        ],
        llm=llm,
        verbose=config['process']['verbose']
    )

from crewai import Agent
from ..tools.proxycurl_tool import ProxycurlTool
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool

class IndividualEvaluation:
    """Individual-level evaluation logic"""
    
    @staticmethod
    def calculate_score(individual_data, config):
        """Calculate individual-level ICP score with detailed breakdown"""
        individual_weight = config['weights'].get('individual', 39)
        
        weights = {
            'role_match': 0.3 * individual_weight,
            'authority_match': 0.3 * individual_weight,
            'department_match': 0.2 * individual_weight,
            'skills_match': 0.2 * individual_weight
        }
        
        # Enhanced role matching with title analysis
        role = individual_data.get('job_title', '').lower()
        scores = {
            'role_match': 100 if any(title.lower() in role for title in config['job_titles']) else 0,
            'authority_match': 100 if any(title in role for title in ['cto', 'cio', 'coo', 'director', 'vp', 'head']) 
                             else 50 if any(title in role for title in ['manager', 'lead']) else 0,
            'department_match': 100 if any(dept.lower() in role for dept in config['target_departments']) else 0,
            'skills_match': 0
        }
        
        # Skills matching if available
        if individual_data.get('skills'):
            required_skills = set(config.get('required_skills', []))
            if required_skills:
                skill_match = len(set(individual_data['skills']).intersection(required_skills)) / len(required_skills) * 100
                scores['skills_match'] = skill_match
        
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
    def enrich_individual_data(individual_data, tools):
        """Enrich individual data with LinkedIn and other sources"""
        enriched_data = individual_data.copy()
        
        try:
            if individual_data.get('linkedin_url'):
                linkedin_data = tools['proxycurl_tool'].get_profile(individual_data['linkedin_url'])
                
                enriched_data.update({
                    'skills': linkedin_data.get('skills', []),
                    'experience': linkedin_data.get('experiences', []),
                    'education': linkedin_data.get('education', []),
                    'certifications': linkedin_data.get('certifications', []),
                    'full_profile': linkedin_data
                })
                
                # Extract additional insights using OpenAI
                profile_insights = tools['openai_tool']._run(
                    f"""Analyze this professional profile and extract key insights about:
                    1. Decision making authority level
                    2. Technical expertise level
                    3. Relevant experience in our target areas
                    4. Potential pain points based on role and industry
                    
                    Profile: {linkedin_data}
                    """
                )
                
                enriched_data['profile_insights'] = profile_insights
                
        except Exception as e:
            print(f"Error enriching individual data: {str(e)}")
        
        return enriched_data

def evaluate_individual(task):
    """Evaluate an individual based on ICP criteria"""
    context = task.context[0] if isinstance(task.context, list) else task.context
    lead = context.get('lead', {})
    config = context.get('config', {}).get('customer_icp', {})
    tools = task.agent.tools
    
    try:
        # Prepare initial individual data
        individual_data = {
            'name': lead.get('name', ''),
            'job_title': lead.get('role', ''),
            'linkedin_url': lead.get('linkedin_url', ''),
            'email': lead.get('email', ''),
            'department': lead.get('department', '')
        }
        
        # Enrich data
        enriched_data = IndividualEvaluation.enrich_individual_data(individual_data, tools)
        
        # Calculate score
        score = IndividualEvaluation.calculate_score(enriched_data, config)
        
        result = {
            'name': individual_data['name'],
            'score': score,
            'enriched_data': enriched_data
        }
        
        # Store in Airtable for tracking
        tools['airtable_tool'].create_record('Individual_Evaluations', {
            'Name': individual_data['name'],
            'Score': score['total'],
            'Details': str(score['breakdown']),
            'EnrichedData': str(enriched_data)
        })
        
        return result
        
    except Exception as e:
        print(f"Error in individual evaluation: {str(e)}")
        return {
            'error': str(e),
            'name': lead.get('name', 'Unknown'),
            'partial_data': individual_data
        }

def get_individual_evaluator(config, tools, llm):
    """Create an individual evaluator agent"""
    return Agent(
        role="Individual Fit Analyst",
        goal="Analyze individual-level ICP fit focusing on role, authority, and expertise",
        backstory="""You are a talent assessment specialist who evaluates individual stakeholders 
        within organizations. You analyze their roles, influence, technical expertise, and potential 
        impact on purchasing decisions.""",
        tools=[
            tools['proxycurl_tool'],
            tools['openai_tool'],
            tools['airtable_tool']
        ],
        llm=llm,
        verbose=config['process']['verbose']
    )

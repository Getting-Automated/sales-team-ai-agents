from crewai import Agent
from ..tools.proxycurl_tool import ProxycurlTool
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool
from datetime import datetime

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
        
        # Update or create Airtable record
        airtable_data = {
            'Name': individual_data['name'],
            'Email': individual_data['email'],
            'Company': lead.get('company', ''),
            'Role': individual_data['job_title'],
            'Individual Score': score['total'],
            'Role Match Score': score['breakdown']['role_match']['score'],
            'Authority Match Score': score['breakdown']['authority_match']['score'],
            'Department Match Score': score['breakdown']['department_match']['score'],
            'Skills Match Score': score['breakdown']['skills_match']['score'],
            'Individual Analysis': str(score['breakdown']),
            'Enriched Individual Data': str(enriched_data),
            'Individual Evaluation Status': "Completed",
            'Last Evaluated': datetime.now().strftime("%Y-%m-%d")
        }
        
        if airtable_record_id:
            # Update existing record
            tools['airtable_tool']._run(
                action="update",
                table_name="Leads",
                record_id=airtable_record_id,
                data=airtable_data
            )
        else:
            # Create new record
            created_record = tools['airtable_tool']._run(
                action="create",
                table_name="Leads",
                data=airtable_data
            )
            airtable_record_id = created_record.get('record_id')
        
        # Update the task context with the Airtable record ID
        context['airtable_record_id'] = airtable_record_id
        task.context = [context]
        
        return result
        
    except Exception as e:
        print(f"Error in individual evaluation: {str(e)}")
        return {
            'error': str(e),
            'name': lead.get('name', 'Unknown'),
            'partial_data': individual_data
        }

def create_individual_evaluator(config, llm):
    """Create an agent that evaluates individual leads"""
    return Agent(
        role=config['individual_evaluator']['role'],
        goal=config['individual_evaluator']['goal'],
        backstory=config['individual_evaluator']['backstory'],
        tools=[
            ProxycurlTool(),
            OpenAITool(),
            AirtableTool()
        ],
        allow_delegation=False,
        verbose=config['process']['verbose'],
        llm=llm
    )

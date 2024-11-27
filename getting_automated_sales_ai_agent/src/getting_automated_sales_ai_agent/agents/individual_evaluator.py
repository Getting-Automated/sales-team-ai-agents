from crewai import Agent
from ..tools.openai_tool import OpenAITool
from datetime import datetime
import json

class IndividualEvaluation:
    """Individual-level evaluation logic"""
    
    @staticmethod
    def calculate_score(individual_data, config):
        """Calculate individual-level ICP score with detailed breakdown"""
        try:
            # Extract OpenAI analysis results
            analysis = individual_data.get('analysis', {})
            
            # Get scores from the analysis
            scores = {
                'role_match': float(analysis.get('role_match_score', 0)),
                'authority_match': float(analysis.get('authority_match_score', 0)),
                'department_match': float(analysis.get('department_match_score', 0)),
                'skills_match': float(analysis.get('skills_match_score', 0))
            }
            
            # Apply weights
            individual_weight = config['weights'].get('individual', 39)
            weights = {
                'role_match': 0.3 * individual_weight,
                'authority_match': 0.3 * individual_weight,
                'department_match': 0.2 * individual_weight,
                'skills_match': 0.2 * individual_weight
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
        except Exception as e:
            print(f"Error calculating score: {str(e)}")
            return {
                'total': 0,
                'breakdown': {
                    'error': str(e)
                }
            }

class IndividualEvaluator(Agent):
    def evaluate(self, task):
        """
        Evaluate an individual lead against ICP criteria.
        Returns evaluation results without handling Airtable operations.
        """
        try:
            # Extract lead data and enriched data from task context
            lead_data = task.context[0].output.get('lead_data', {})
            proxycurl_data = task.context[1].output.get('proxycurl_data', {})
            
            # Analyze lead using OpenAI
            analysis_prompt = f"""
            Analyze this lead's fit with our ICP criteria:
            
            Lead Information:
            {json.dumps(lead_data, indent=2)}
            
            LinkedIn Data:
            {json.dumps(proxycurl_data, indent=2)}
            
            Evaluate their fit against our ICP criteria:
            1. Role and Title Match
            2. Decision Making Authority
            3. Department Alignment
            4. Skills and Experience
            
            For each criterion:
            - Analyze the available information
            - Provide specific evidence from their profile
            - Explain your reasoning
            - Assign a score (0-100)
            
            Provide a JSON response with these exact keys:
            {{
                "role_match_score": <score>,
                "authority_match_score": <score>,
                "department_match_score": <score>,
                "skills_match_score": <score>,
                "overall_score": <weighted average of scores>,
                "lead_tier": "<High/Medium/Low based on overall score>",
                "analysis": "<detailed explanation of evaluation>"
            }}
            """
            
            evaluation_results = self.openai_tool.analyze(
                prompt=analysis_prompt,
                max_tokens=1500
            )
            
            return {
                'status': 'success',
                'evaluation': evaluation_results,
                'message': 'Individual evaluation completed successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error evaluating individual lead: {str(e)}'
            }

def create_individual_evaluator(config, llm):
    """Create an agent that evaluates individual leads"""
    return IndividualEvaluator(
        role=config['individual_evaluator']['role'],
        goal=config['individual_evaluator']['goal'],
        backstory=config['individual_evaluator']['backstory'],
        tools=[OpenAITool()],
        allow_delegation=False,
        verbose=config['process']['verbose'],
        llm=llm
    )

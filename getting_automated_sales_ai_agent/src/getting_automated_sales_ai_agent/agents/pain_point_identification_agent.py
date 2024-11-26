# agents/pain_point_agent.py

from crewai import Agent
from langchain_openai import ChatOpenAI
from ..tools.perplexity_tool import PerplexityTool
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool
import json
from datetime import datetime

def pain_point_agent_logic(self):
    """Identify pain points using comprehensive company context and targeted research"""
    lead_data = self.inputs.get('lead', {})
    icp_analysis = self.inputs.get('icp_analysis', {})
    company_data = self.inputs.get('company_data', {})
    
    # Basic company info
    company = lead_data.get('company', '')
    industry = lead_data.get('industry', '')
    technologies = lead_data.get('technologies', '')
    employees = lead_data.get('employees', '')
    revenue = lead_data.get('revenue', '')
    
    # Company description data
    seo_description = lead_data.get('seo_description', '')
    keywords = lead_data.get('keywords', '')
    departments = lead_data.get('departments', '')
    
    # Build rich company context
    company_context = {
        'size_category': 'mid_market' if isinstance(employees, str) and '100' <= employees <= '1000' else 'enterprise' if employees > '1000' else 'smb',
        'tech_maturity': icp_analysis.get('tech_stack_assessment', 'unknown'),
        'growth_stage': icp_analysis.get('company_stage', 'unknown'),
        'market_position': company_data.get('market_position', 'unknown'),
        'current_tools': technologies.split(',') if isinstance(technologies, str) else [],
        'description': seo_description,
        'key_focus_areas': keywords.split(',') if isinstance(keywords, str) else [],
        'departments': departments.split(',') if isinstance(departments, str) else []
    }
    
    # Research queries with company description context
    research_queries = [
        f"""What are the specific operational challenges for {company_context['size_category']} 
        companies in {industry} with {employees} employees?
        Company Description: {company_context['description']}""",
        
        f"""What technology integration and scaling issues do {company_context['size_category']} 
        companies face when using {', '.join(company_context['current_tools'])}?
        Key Focus Areas: {', '.join(company_context['key_focus_areas'])}""",
        
        f"""What are the main growth bottlenecks for {company_context['size_category']} 
        {industry} companies transitioning from {company_context['growth_stage']}?
        Departments: {', '.join(company_context['departments'])}""",
        
        f"""Recent challenges or problems reported by {company} or similar 
        {company_context['size_category']} companies in {industry} focusing on:
        {company_context['description']}"""
    ]
    
    # Gather research using Perplexity
    research_results = []
    for query in research_queries:
        try:
            result = self.perplexity_tool._run(query, focus='business')
            if isinstance(result, str) and not result.startswith('Error'):
                research_results.append({
                    'query': query,
                    'findings': result
                })
            else:
                print(f"Warning: Skipping invalid research result for query: {query}")
        except Exception as e:
            print(f"Error during research query: {str(e)}")
            continue
    
    # Combine research results for analysis
    combined_research = "\n\n".join([
        f"Research Query: {result['query']}\nFindings: {result['findings']}"
        for result in research_results
    ])
    
    # Analysis prompt for OpenAI with comprehensive context
    analysis_prompt = f"""
    Analyze pain points for {company} using the following detailed context and research:
    
    COMPANY PROFILE:
    - Company: {company}
    - Description: {company_context['description']}
    - Key Focus Areas: {', '.join(company_context['key_focus_areas'])}
    - Size: {company_context['size_category']} ({employees} employees)
    - Revenue: {revenue}
    - Industry: {industry}
    - Departments: {', '.join(company_context['departments'])}
    
    TECHNICAL CONTEXT:
    - Growth Stage: {company_context['growth_stage']}
    - Tech Maturity: {company_context['tech_maturity']}
    - Current Tools: {', '.join(company_context['current_tools'])}
    - Market Position: {company_context['market_position']}
    
    ICP ANALYSIS INSIGHTS:
    {json.dumps(icp_analysis, indent=2)}
    
    COMPANY DATA INSIGHTS:
    {json.dumps(company_data, indent=2)}
    
    RESEARCH FINDINGS:
    {combined_research}
    
    Based on this comprehensive context, identify:
    1. Mid-market specific challenges they're likely facing given their description and focus areas
    2. Growth bottlenecks at their current stage and scale
    3. Technology gaps and integration issues specific to their current stack
    4. Operational inefficiencies across their identified departments
    5. Resource constraints typical for their size and industry position
    6. Competitive pressures in their specific market segment
    
    Format as JSON with these keys:
    - mid_market_challenges: Array of size-specific challenges
    - growth_bottlenecks: Array of stage-specific growth issues
    - tech_gaps: Array of technology-related challenges
    - operational_issues: Object with department-specific problems
    - resource_constraints: Array of resource-related challenges
    - competitive_pressures: Array of market segment challenges
    - evidence: Object with sources and citations
    - confidence_score: Object with scores per category
    - context_relevance: Brief explanation of how company description influenced findings
    """
    
    # Analyze with OpenAI
    try:
        analysis_result = self.openai_tool._run(
            prompt=analysis_prompt,
            max_tokens=2500,
            temperature=0.5
        )
        
        analysis = json.loads(analysis_result)
        
        # Store in Airtable
        airtable_data = {
            'Company': company,
            'Industry': industry,
            'SpecificChallenges': json.dumps(analysis.get('specific_challenges', [])),
            'IndustryChallenges': json.dumps(analysis.get('industry_challenges', [])),
            'TechStackIssues': json.dumps(analysis.get('tech_stack_issues', [])),
            'GrowthObstacles': json.dumps(analysis.get('growth_obstacles', [])),
            'CompetitivePressures': json.dumps(analysis.get('competitive_pressures', [])),
            'Evidence': json.dumps(analysis.get('evidence', {})),
            'ConfidenceScores': json.dumps(analysis.get('confidence_score', {})),
            'DateAnalyzed': datetime.now().isoformat()
        }
        
        self.airtable_tool._run('create', 'PainPointsAnalysis', airtable_data)
        
        return json.dumps(analysis, indent=2)
        
    except Exception as e:
        print(f"Error in pain point analysis: {str(e)}")
        return f"Error during analysis: {str(e)}"

def get_pain_point_agent(config, tools, llm):
    agent_conf = config['pain_point_agent']
    agent_instance = Agent(
        llm=llm,
        tools=tools,
        **agent_conf
    )
    # Assign custom logic to the agent's run method
    agent_instance.run = pain_point_agent_logic.__get__(agent_instance, Agent)
    return agent_instance

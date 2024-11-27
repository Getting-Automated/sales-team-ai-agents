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
    
    RESEARCH FINDINGS:
    {combined_research}
    
    Based on this context, identify and categorize pain points into:
    1. Technical Challenges
    2. Operational Inefficiencies
    3. Process Bottlenecks
    4. Automation Opportunities
    
    For each pain point:
    - Describe the specific challenge
    - Rate potential impact (high/medium/low)
    - Assess implementation complexity
    - Suggest practical solutions
    """
    
    try:
        # Get detailed pain point analysis
        analysis_result = self.openai_tool._run(analysis_prompt)
        
        # Store results in Airtable for tracking
        airtable_data = {
            'Company': company,
            'Industry': industry,
            'Analysis_Date': datetime.now().isoformat(),
            'Pain_Points': analysis_result,
            'Research_Context': combined_research
        }
        self.airtable_tool._run(json.dumps(airtable_data))
        
        return {
            'company': company,
            'analysis_date': datetime.now().isoformat(),
            'pain_points': analysis_result,
            'research_context': research_results
        }
        
    except Exception as e:
        print(f"Error in pain point analysis: {str(e)}")
        return {
            'error': str(e),
            'partial_research': research_results
        }

def get_pain_point_agent(config, tools, llm):
    """Create a pain point identification agent with research capabilities"""
    return Agent(
        role='Pain Point Identification Specialist',
        goal='Identify and analyze company pain points through comprehensive research and context analysis',
        backstory="""You are an expert business analyst specializing in identifying operational, 
        technical, and process-related challenges in organizations. You combine industry research, 
        technical assessment, and business context to uncover actionable pain points and 
        automation opportunities.""",
        tools=[
            tools['perplexity_tool'],
            tools['openai_tool'],
            tools['airtable_tool']
        ],
        llm=llm,
        verbose=config['process']['verbose']
    )

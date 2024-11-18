from crewai import Agent
from langchain_community.llms import OpenAI
from ..tools.airtable_tool import AirtableTool
from ..tools.openai_tool import OpenAITool
import os
import json

def offer_creator_agent_logic(self):
    """
    Agent logic for either finding the best offer or evaluating a specific offer.
    """
    mode = self.inputs.get('mode', 'find-best')
    leads = self.inputs.get('lead_list', [])
    offer_id = self.inputs.get('offer_id')
    
    if not leads:
        return "No leads provided for analysis."
    
    airtable_tool = next((tool for tool in self.tools if isinstance(tool, AirtableTool)), None)
    if not airtable_tool:
        return "AirtableTool not available."
        
    if mode == 'evaluate-single':
        return self._evaluate_specific_offer(airtable_tool, offer_id, leads)
    else:
        return self._find_best_offer(airtable_tool, leads)

def _evaluate_specific_offer(self, airtable_tool, offer_id, leads):
    """Evaluate a specific offer for the given leads."""
    if not offer_id:
        return "No offer ID provided for evaluation."
        
    # Get the specific offer from Airtable
    offer = airtable_tool.get_offer(offer_id)
    if not offer:
        return f"Offer with ID {offer_id} not found."
    
    analysis = []
    for lead in leads:
        # Analyze fit between lead and offer
        fit_analysis = self.analyze_offer_fit(offer, lead)
        
        # Store analysis results
        analysis.append({
            'lead_name': lead.get('name'),
            'company': lead.get('company'),
            'offer_id': offer_id,
            'offer_name': offer.get('Offer Name'),
            'fit_score': fit_analysis.get('fit_score'),
            'fit_reasons': fit_analysis.get('reasons'),
            'recommendations': fit_analysis.get('recommendations')
        })
    
    return {
        'offer_details': offer,
        'lead_analyses': analysis,
        'summary': self.summarize_analyses(analysis)
    }

def _find_best_offer(self, airtable_tool, leads):
    """Find the best offer for the given leads."""
    # Get all available offers
    offers = airtable_tool.list_offers()
    if not offers:
        return "No offers available for analysis."
    
    best_matches = []
    for lead in leads:
        lead_matches = []
        for offer in offers:
            # Analyze fit between lead and offer
            fit_analysis = self.analyze_offer_fit(offer, lead)
            lead_matches.append({
                'offer_id': offer.get('Offer ID'),
                'offer_name': offer.get('Offer Name'),
                'fit_score': fit_analysis.get('fit_score'),
                'fit_reasons': fit_analysis.get('reasons'),
                'recommendations': fit_analysis.get('recommendations')
            })
        
        # Sort matches by fit score and get the best one
        lead_matches.sort(key=lambda x: x['fit_score'], reverse=True)
        best_matches.append({
            'lead_name': lead.get('name'),
            'company': lead.get('company'),
            'best_offer': lead_matches[0],
            'alternative_offers': lead_matches[1:3]  # Next 2 best matches
        })
    
    return {
        'matches': best_matches,
        'summary': self.summarize_matches(best_matches)
    }

def analyze_offer_fit(self, offer, lead):
    """Analyze the fit between an offer and a lead."""
    prompt = f"""
    Analyze the fit between the following lead and offer:
    
    Lead:
    - Name: {lead.get('name')}
    - Company: {lead.get('company')}
    - Role: {lead.get('role')}
    - Industry: {lead.get('industry')}
    - Company Size: {lead.get('company_size')}
    - Technologies: {lead.get('technologies')}
    
    Offer:
    - Name: {offer.get('Offer Name')}
    - Category: {offer.get('Category')}
    - Description: {offer.get('Description')}
    - Industry Fit: {offer.get('Industry Fit')}
    - Target Client Type: {offer.get('Target Client Type')}
    
    Provide:
    1. A fit score (0-100)
    2. Key reasons for the fit score
    3. Specific recommendations for approaching this lead with this offer
    """
    
    response = self.llm.predict(prompt)
    
    # Parse the response and structure it
    # (You might want to add more structure to the prompt and response parsing)
    return {
        'fit_score': self._extract_fit_score(response),
        'reasons': self._extract_reasons(response),
        'recommendations': self._extract_recommendations(response)
    }

def _extract_fit_score(self, response):
    """Extract numerical fit score from response."""
    try:
        # Look for patterns like "fit score: 85" or "85/100" or just "85"
        import re
        score_patterns = [
            r'fit score:?\s*(\d+)',
            r'(\d+)/100',
            r'score:?\s*(\d+)',
            r'rating:?\s*(\d+)'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, response.lower())
            if match:
                score = int(match.group(1))
                return min(100, max(0, score))  # Ensure score is between 0-100
                
        # If no pattern matched, use AI to extract the score
        score_prompt = f"""
        Extract only the numerical fit score (0-100) from this analysis. 
        Output only the number:
        
        {response}
        """
        score_str = self.llm.predict(score_prompt).strip()
        return min(100, max(0, int(score_str)))
    except:
        return 50  # Default score if extraction fails

def _extract_reasons(self, response):
    """Extract reasons from response."""
    try:
        reasons_prompt = f"""
        Extract the key reasons for the fit score from this analysis.
        Format as a list of strings, with each reason being clear and concise.
        Output as a JSON array:
        
        {response}
        """
        reasons_str = self.llm.predict(reasons_prompt)
        import json
        reasons = json.loads(reasons_str)
        return reasons if isinstance(reasons, list) else []
    except:
        return ["Unable to extract specific reasons from analysis"]

def _extract_recommendations(self, response):
    """Extract recommendations from response."""
    try:
        recommendations_prompt = f"""
        Extract specific recommendations for approaching this lead with this offer.
        Format as a list of actionable steps.
        Output as a JSON array:
        
        {response}
        """
        recommendations_str = self.llm.predict(recommendations_prompt)
        import json
        recommendations = json.loads(recommendations_str)
        return recommendations if isinstance(recommendations, list) else []
    except:
        return ["Unable to extract specific recommendations from analysis"]

def summarize_analyses(self, analyses):
    """Summarize the analyses of a single offer across multiple leads."""
    if not analyses:
        return "No analyses to summarize."
        
    # Calculate aggregate statistics
    total_leads = len(analyses)
    avg_score = sum(a['fit_score'] for a in analyses) / total_leads if total_leads > 0 else 0
    high_fit = len([a for a in analyses if a['fit_score'] >= 70])
    medium_fit = len([a for a in analyses if 40 <= a['fit_score'] < 70])
    low_fit = len([a for a in analyses if a['fit_score'] < 40])
    
    summary_prompt = f"""
    Create a concise summary of this offer's fit analysis across {total_leads} leads:
    
    Statistics:
    - Average Fit Score: {avg_score:.1f}
    - High Fit (70+): {high_fit} leads
    - Medium Fit (40-69): {medium_fit} leads
    - Low Fit (<40): {low_fit} leads
    
    Individual Analyses:
    {json.dumps(analyses, indent=2)}
    
    Provide:
    1. Overall assessment of the offer's potential
    2. Key patterns in fit/non-fit reasons
    3. General recommendations for offer positioning
    """
    
    return self.llm.predict(summary_prompt)

def summarize_matches(self, matches):
    """Summarize the best matches found for all leads."""
    if not matches:
        return "No matches to summarize."
        
    # Calculate aggregate statistics
    total_leads = len(matches)
    avg_best_score = sum(m['best_offer']['fit_score'] for m in matches) / total_leads if total_leads > 0 else 0
    
    # Get unique offers that were selected as best matches
    best_offers = {}
    for match in matches:
        offer_id = match['best_offer']['offer_id']
        if offer_id not in best_offers:
            best_offers[offer_id] = {
                'name': match['best_offer']['offer_name'],
                'count': 1,
                'total_score': match['best_offer']['fit_score']
            }
        else:
            best_offers[offer_id]['count'] += 1
            best_offers[offer_id]['total_score'] += match['best_offer']['fit_score']
    
    summary_prompt = f"""
    Create a concise summary of the best offer matches for {total_leads} leads:
    
    Statistics:
    - Average Best Match Score: {avg_best_score:.1f}
    - Number of Unique Best Offers: {len(best_offers)}
    
    Best Offer Distribution:
    {json.dumps({k: {
        'name': v['name'],
        'times_selected': v['count'],
        'average_score': v['total_score'] / v['count']
    } for k, v in best_offers.items()}, indent=2)}
    
    Individual Matches:
    {json.dumps(matches, indent=2)}
    
    Provide:
    1. Overall assessment of the matching results
    2. Key patterns in offer selection
    3. General recommendations for offer strategy
    """
    
    return self.llm.predict(summary_prompt)

def get_offer_creator_agent(config, tools, llm):
    """Create and configure the offer creator agent."""
    agent_instance = Agent(
        name="Offer Research & Creation Agent",
        goal="Analyze leads and either find the best matching offer or evaluate a specific offer's fit",
        backstory="""Expert at analyzing lead characteristics and matching them with the most suitable offers. 
        Can evaluate both individual offers and find the best matches from available options.""",
        tools=tools,
        llm=llm,
        verbose=True
    )
    
    # Attach the methods to the agent instance
    agent_instance.run = offer_creator_agent_logic.__get__(agent_instance, Agent)
    agent_instance._evaluate_specific_offer = _evaluate_specific_offer.__get__(agent_instance, Agent)
    agent_instance._find_best_offer = _find_best_offer.__get__(agent_instance, Agent)
    agent_instance.analyze_offer_fit = analyze_offer_fit.__get__(agent_instance, Agent)
    agent_instance._extract_fit_score = _extract_fit_score.__get__(agent_instance, Agent)
    agent_instance._extract_reasons = _extract_reasons.__get__(agent_instance, Agent)
    agent_instance._extract_recommendations = _extract_recommendations.__get__(agent_instance, Agent)
    agent_instance.summarize_analyses = summarize_analyses.__get__(agent_instance, Agent)
    agent_instance.summarize_matches = summarize_matches.__get__(agent_instance, Agent)
    
    return agent_instance
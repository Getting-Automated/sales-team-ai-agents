from crewai import Agent
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool
from ..utils.business_profile import read_business_profile

class EmailCampaignGenerator:
    """Email campaign generation logic using LLM for personalized content"""
    
    @staticmethod
    def _create_email_prompt(lead_data, business_profile, sequence_number, previous_emails=None):
        """Create a prompt for the LLM to generate email content"""
        # Build context from business profile
        context = {
            'company_info': business_profile['company'],
            'products': business_profile['products'],
            'pain_points': business_profile['pain_points'],
            'success_stories': business_profile['success_stories'],
            'results': business_profile['results']
        }
        
        # Build lead context
        lead_context = {
            'name': lead_data.get('name', '').split()[0],  # First name only
            'company': lead_data.get('company', ''),
            'industry': lead_data.get('industry', ''),
            'role': lead_data.get('role', ''),
            'company_size': lead_data.get('company_size', '')
        }
        
        email_types = {
            1: {
                'type': 'initial',
                'focus': 'introduction and primary value proposition',
                'max_words': 75,
                'wait_days': 0
            },
            2: {
                'type': 'value_add',
                'focus': 'share relevant content or insight',
                'max_words': 100,
                'wait_days': 3
            },
            3: {
                'type': 'pain_point',
                'focus': 'address specific pain points with case study',
                'max_words': 125,
                'wait_days': 5
            },
            4: {
                'type': 'roi',
                'focus': 'concrete business value and metrics',
                'max_words': 150,
                'wait_days': 7
            },
            5: {
                'type': 'final',
                'focus': 'urgency and strong offer',
                'max_words': 125,
                'wait_days': 10
            }
        }
        
        email_type = email_types[sequence_number]
        
        prompt = f"""Generate email #{sequence_number} in a 5-part sequence following these guidelines:
        - Focus on: {email_type['focus']}
        - Keep it under {email_type['max_words']} words
        - Include a clear call to action
        - Use simple language (max 3 industry terms)
        - Be conversational but professional
        
        Business Context:
        {context}
        
        Lead Information:
        {lead_context}
        
        Previous Emails in Sequence:
        {previous_emails if previous_emails else 'None'}
        
        Generate response as JSON with:
        - subject: Email subject line
        - body: Email body
        - personalization_notes: Key personalization points used
        - pain_points_addressed: Main pain points tackled
        - call_to_action: Primary CTA for this stage"""
            
        return prompt
    
    @staticmethod
    def create_campaign_sequence(lead_data, offer_data, llm):
        """Create a sequence of 5 personalized follow-up emails"""
        business_profile = read_business_profile()
        email_sequence = []
        
        # Generate all 5 emails
        for sequence_number in range(1, 6):
            prompt = EmailCampaignGenerator._create_email_prompt(
                lead_data,
                business_profile,
                sequence_number,
                previous_emails=email_sequence
            )
            
            response = llm.generate_content(prompt)
            
            try:
                email_content = response.json()
                
                # Add sequence-specific data
                email_content['sequence_number'] = sequence_number
                email_content['wait_days'] = [0, 3, 5, 7, 10][sequence_number-1]
                email_content['lead_id'] = lead_data.get('lead_id')
                
                email_sequence.append(email_content)
                
            except Exception as e:
                print(f"Error generating email {sequence_number}: {str(e)}")
                continue
        
        return email_sequence

def get_email_campaign_agent(config, tools, llm):
    """Create an email campaign agent that uses LLM for content generation"""
    return Agent(
        role='Email Campaign Specialist',
        goal='Create highly effective, personalized cold email campaigns that get responses',
        backstory="""Expert in creating personalized cold email campaigns that combine proven frameworks 
                  with dynamic, context-aware content. Focuses on building genuine connections while 
                  maintaining high conversion rates.""",
        tools=tools,
        llm=llm,
        verbose=True
    )

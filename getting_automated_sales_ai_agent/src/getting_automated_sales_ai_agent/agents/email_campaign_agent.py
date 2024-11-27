from crewai import Agent
from ..tools.openai_tool import OpenAITool
from ..tools.airtable_tool import AirtableTool
from ..utils.business_profile import read_business_profile

class EmailCampaignGenerator:
    """Email campaign generation logic using LLM for personalized content"""
    
    @staticmethod
    def _create_email_prompt(lead_data, business_profile, email_type="initial", previous_emails=None):
        """Create a prompt for the LLM to generate email content
        
        Args:
            lead_data: Dictionary containing lead information
            business_profile: Dictionary containing business profile information
            email_type: Type of email to generate ("initial" or "followup")
            previous_emails: List of previous emails in the sequence, each containing subject and body
        """
        
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
        
        if email_type == "initial":
            prompt = f"""Generate a cold email following these guidelines:
            - Keep it under 75 words
            - Focus on specific value and outcomes
            - Include a soft call to action
            - Use simple language (max 3 industry terms)
            - Goal is to get a response, not sell the product
            - Be conversational but professional
            - Include a clear opt-out
            
            Business Context:
            {context}
            
            Lead Information:
            {lead_context}
            
            Generate two parts:
            1. Subject line (short, personalized, intriguing)
            2. Email body
            
            Format the response as JSON with 'subject' and 'body' keys."""
            
        elif email_type == "followup":
            # Build history of previous emails
            email_history = "\n\n".join([
                f"Email {i+1}:\nSubject: {email['subject']}\nBody:\n{email['body']}"
                for i, email in enumerate(previous_emails or [])
            ])
            
            prompt = f"""Generate a follow-up email following these guidelines:
            - Even shorter than initial email (max 50 words)
            - Reference previous email subtly
            - New angle on value proposition
            - Clear, specific call to action (suggest specific times)
            - Keep it casual and light
            - Include opt-out
            - DO NOT repeat points or angles already used in previous emails
            
            Business Context:
            {context}
            
            Lead Information:
            {lead_context}
            
            Previous Emails in Sequence:
            {email_history}
            
            Generate a follow-up that:
            1. Takes a fresh approach
            2. Doesn't repeat information from previous emails
            3. Adds new value or insight
            
            Format the response as JSON with 'subject' and 'body' keys."""
            
        return prompt
    
    @staticmethod
    def generate_email_content(lead_data, offer_data, llm):
        """Generate personalized email content using LLM"""
        business_profile = read_business_profile()
        
        # Generate email content using LLM
        prompt = EmailCampaignGenerator._create_email_prompt(lead_data, business_profile)
        response = llm.generate_content(prompt)
        
        try:
            # Parse LLM response as JSON
            email_content = response.json()
            return email_content
        except Exception as e:
            # Fallback content if LLM response isn't properly formatted
            return {
                'subject': f"Quick one for {lead_data.get('company', '')}",
                'body': f"""Hey {lead_data.get('name', '').split()[0]} - I'll be quick.

Would you be open to a brief chat about automating some processes at {lead_data.get('company', '')}?

Best regards"""
            }
    
    @staticmethod
    def create_campaign_sequence(lead_data, offer_data, llm):
        """Create a sequence of dynamic, personalized follow-up emails"""
        # Generate initial email
        initial_email = EmailCampaignGenerator.generate_email_content(lead_data, offer_data, llm)
        
        # Keep track of all emails in sequence
        email_sequence = [initial_email]
        
        # Generate follow-ups with different angles
        followups = []
        for i in range(2):  # Generate 2 follow-ups
            business_profile = read_business_profile()
            prompt = EmailCampaignGenerator._create_email_prompt(
                lead_data, 
                business_profile, 
                "followup",
                previous_emails=email_sequence
            )
            response = llm.generate_content(prompt)
            
            try:
                followup_content = response.json()
                followups.append({
                    'subject': followup_content['subject'],
                    'timing': '3 days' if i == 0 else '5 days',
                    'content': followup_content['body']
                })
                # Add to email sequence for context in next follow-up
                email_sequence.append(followup_content)
            except Exception as e:
                # Fallback content if LLM response isn't properly formatted
                continue
        
        return {
            'initial_email': initial_email,
            'followups': followups,
            'campaign_settings': {
                'max_followups': len(followups),
                'reply_window_minutes': 5,  # Critical to respond within 5 minutes
                'send_timezone': lead_data.get('timezone', 'EST'),
                'optimal_send_times': ['10:00', '14:00'],
                'days_between_followups': [3, 5]
            }
        }

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

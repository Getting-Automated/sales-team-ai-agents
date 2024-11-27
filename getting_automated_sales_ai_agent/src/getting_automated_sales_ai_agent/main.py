# main.py

#!/usr/bin/env python
import sys
import warnings
import argparse
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
from getting_automated_sales_ai_agent.crew import GettingAutomatedSalesAiAgent
import csv
from getting_automated_sales_ai_agent.tools import AirtableTool

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def transform_lead_data(df):
    # Transform DataFrame to list of dictionaries with proper structure
    leads = []
    for _, row in df.iterrows():
        lead = {
            'name': f"{row['First Name']} {row['Last Name']}",
            'company': row['Company'],
            'linkedin_url': row['Person Linkedin Url'],
            'role': row['Title'],
            'industry': row['Industry'],
            'company_website': row['Website'],
            'email': row['Email'],
            'company_linkedin_url': row['Company Linkedin Url'],
            'technologies': row['Technologies'],
            'employees': row['# Employees'],
            'revenue': row['Annual Revenue'],
            'location': f"{row['City']}, {row['State']}, {row['Country']}",
            'company_location': f"{row['Company City']}, {row['Company State']}, {row['Company Country']}",
            'keywords': row['Keywords'],
            'seo_description': row['SEO Description'],
            'departments': row['Departments'],
            'seniority': row['Seniority'],
            'social_media': {
                'facebook': row['Facebook Url'],
                'twitter': row['Twitter Url']
            },
            'phone': {
                'work': row['Work Direct Phone'],
                'mobile': row['Mobile Phone'],
                'corporate': row['Corporate Phone']
            },
            'company_details': {
                'address': row['Company Address'],
                'phone': row['Company Phone'],
                'total_funding': row['Total Funding'],
                'latest_funding': row['Latest Funding'],
                'latest_funding_amount': row['Latest Funding Amount']
            }
        }
        # Clean up None or NaN values
        lead = {k: (v if pd.notna(v) else '') for k, v in lead.items()}
        lead['social_media'] = {k: (v if pd.notna(v) else '') for k, v in lead['social_media'].items()}
        lead['phone'] = {k: (v if pd.notna(v) else '') for k, v in lead['phone'].items()}
        lead['company_details'] = {k: (v if pd.notna(v) else '') for k, v in lead['company_details'].items()}
        
        leads.append(lead)
    return leads

def load_config():
    """Load environment variables and basic configuration"""
    load_dotenv()
    
    config = {
        'openai': {
            'api_key': os.getenv('OPENAI_API_KEY')
        },
        'perplexity': {
            'api_key': os.getenv('PERPLEXITY_API_KEY')
        },
        'airtable': {
            'api_key': os.getenv('AIRTABLE_API_KEY'),
            'base_id': os.getenv('AIRTABLE_BASE_ID')
        },
        'proxycurl': {
            'api_key': os.getenv('PROXYCURL_API_KEY')
        },
        'reddit': {
            'client_id': os.getenv('REDDIT_CLIENT_ID'),
            'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
            'user_agent': os.getenv('REDDIT_USER_AGENT'),
            'username': os.getenv('REDDIT_USERNAME'),
            'password': os.getenv('REDDIT_PASSWORD')
        }
    }
    
    return config

def process_leads(leads):
    """Process a single lead"""
    try:
        crew = GettingAutomatedSalesAiAgent()
        crew.inputs['leads'] = leads  # This will be a list with just one lead
        result = crew.run()
        print("\nCompleted analysis")
        return result
    except Exception as e:
        print(f"Error processing leads: {str(e)}")

def check_lead_status(email):
    """Check if a lead has already been fully evaluated in Airtable"""
    try:
        # Initialize AirtableTool
        airtable_tool = AirtableTool()
        
        # Search for the lead in Airtable using _run instead of execute
        result = airtable_tool._run(
            action="search",
            table_name="Leads",
            search_field="Email",
            search_value=email
        )
        
        print(f"Checking status for lead with email: {email}")
        print(f"Airtable search result: {result}")
        
        # If lead found, check evaluation status
        if result and isinstance(result, dict):
            if 'record' in result:
                fields = result['record'].get('fields', {})
                individual_status = fields.get('Individual Evaluation Status')
                company_status = fields.get('Company Evaluation Status')
                
                print(f"Found lead with statuses - Individual: {individual_status}, Company: {company_status}")
                
                if individual_status == "Completed" and company_status == "Completed":
                    return True, "Both evaluations already completed"
                elif individual_status or company_status:
                    status_msg = []
                    if individual_status:
                        status_msg.append(f"Individual: {individual_status}")
                    if company_status:
                        status_msg.append(f"Company: {company_status}")
                    return False, f"Partial evaluation - {', '.join(status_msg)}"
        
        return False, "Lead not found"
        
    except Exception as e:
        print(f"Error checking lead status: {str(e)}")
        return False, f"Error checking status: {str(e)}"

def process_csv_files(input_dir):
    """Process all CSV files in the input directory"""
    csv_files = list(Path(input_dir).glob('*.csv'))
    print(f"Looking for CSV files in: {input_dir}")
    
    for csv_file in csv_files:
        print(f"Processing file: {csv_file.name}")
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Transform all leads
            all_leads = transform_lead_data(df)
            
            if not all_leads:
                print("No leads found in CSV")
                continue
            
            # Filter out already processed leads
            leads_to_process = []
            for lead in all_leads:
                is_completed, reason = check_lead_status(lead.get('email'))
                if is_completed:
                    print(f"Skipping lead {lead.get('email')}: {reason}")
                else:
                    leads_to_process.append(lead)
            
            if not leads_to_process:
                print("All leads have been processed")
                continue
                
            print(f"\nProcessing {len(leads_to_process)} leads from {csv_file.name}")
            
            # Process remaining leads
            process_leads(leads_to_process)
            
        except Exception as e:
            print(f"Error processing CSV file {csv_file}: {str(e)}")

def load_leads_from_csv(file_path):
    """Load leads from a CSV file"""
    leads = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            leads.append({
                'name': row.get('Name', ''),
                'email': row.get('Email', ''),
                'company': row.get('Company', ''),
                'role': row.get('Title', ''),
                'linkedin_url': row.get('LinkedIn URL', ''),
                'company_website': row.get('Company Website', '')
            })
    return leads

def main():
    # Find CSV files in the inputs directory
    input_dir = Path(__file__).parent.parent.parent / 'inputs'
    print(f"\nLooking for CSV files in: {input_dir}")
    
    csv_files = list(input_dir.glob('*.csv'))
    if not csv_files:
        print("No CSV files found in the inputs directory")
        return
    
    # Process each CSV file
    for csv_file in csv_files:
        print(f"\nProcessing file: {csv_file.name}")
        
        # Load leads from CSV
        leads = load_leads_from_csv(csv_file)
        
        # Initialize the crew
        sales_crew = GettingAutomatedSalesAiAgent()
        
        # Process each lead
        for lead in leads:
            try:
                print(f"\nProcessing lead:")
                print(f"Name: {lead['name']}")
                print(f"Email: {lead['email']}")
                print(f"Company: {lead['company']}")
                
                # Set the lead data for processing
                sales_crew.inputs['leads'] = [lead]
                
                # Run the crew with hierarchical process
                result = sales_crew.run()
                
                # Print results and usage statistics
                print("\nProcessing Results:")
                print(result)
                
            except Exception as e:
                print(f"Error processing lead: {str(e)}")
                continue

def run():
    """Main function to run the crew"""
    parser = argparse.ArgumentParser(description='Process leads from a CSV file')
    parser.add_argument('--file', type=str, help='Path to CSV file')
    parser.add_argument('--mode', type=str, choices=['find-best', 'evaluate-single'], 
                       default='find-best', help='Operation mode: find best offer or evaluate single offer')
    parser.add_argument('--offer-id', type=str, help='Offer ID to evaluate (required for evaluate-single mode)')
    args = parser.parse_args()
    
    if args.mode == 'evaluate-single' and not args.offer_id:
        parser.error("--offer-id is required when using evaluate-single mode")
    
    if not args.file:
        input_dir = Path(__file__).parent.parent.parent / 'inputs'
        process_csv_files(input_dir)
    else:
        file_path = Path(args.file)
        process_leads([transform_lead_data(pd.read_csv(file_path))])

if __name__ == "__main__":
    run()

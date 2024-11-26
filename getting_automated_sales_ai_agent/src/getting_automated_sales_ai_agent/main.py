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

def process_csv_files(input_dir):
    """Process all CSV files in the input directory"""
    csv_files = list(Path(input_dir).glob('*.csv'))
    print(f"Looking for CSV files in: {input_dir}")
    
    for csv_file in csv_files:
        print(f"Processing file: {csv_file.name}")
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Take just the first row as a DataFrame
            first_lead_df = df.head(1)
            
            # Transform using our existing function
            leads = transform_lead_data(first_lead_df)
            
            if not leads:
                print("No leads found in CSV")
                continue
                
            lead = leads[0]  # Get the first (and only) lead
            print(f"\nProcessing lead:")
            print(f"Name: {lead.get('name')}")
            print(f"Email: {lead.get('email')}")
            print(f"Company: {lead.get('company')}")
            
            # Process just this one lead
            process_leads([lead])
            
        except Exception as e:
            print(f"Error processing CSV file {csv_file}: {str(e)}")

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

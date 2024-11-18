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
        'airtable': {
            'api_key': os.getenv('AIRTABLE_API_KEY'),
            'base_id': os.getenv('AIRTABLE_BASE_ID')
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
        print(f"Looking for CSV files in: {input_dir}")
        csv_files = list(input_dir.glob('*.csv'))
        if not csv_files:
            print("No CSV files found in inputs directory")
            return
        file_path = csv_files[0]
    else:
        file_path = Path(args.file)
    
    print(f"Processing file: {file_path.name}")
    
    try:
        df = pd.read_csv(file_path)
        leads = transform_lead_data(df)
        
        inputs = {
            'leads': leads,
            'config': load_config(),
            'mode': args.mode,
            'offer_id': args.offer_id if args.mode == 'evaluate-single' else None
        }
        
        crew = GettingAutomatedSalesAiAgent()
        crew.inputs = inputs
        result = crew.crew.kickoff()
        print(f"Processed {len(leads)} leads in {args.mode} mode")
        return result
        
    except Exception as e:
        print(f"Error processing leads: {str(e)}")
        raise

if __name__ == "__main__":
    run()

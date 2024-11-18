import os
from dotenv import load_dotenv
from pyairtable import Api
import requests
from config.airtable_config import BASE_NAME, Tables

# Load environment variables
load_dotenv()
API_KEY = os.getenv('AI_AGENT_AIRTABLE_API_KEY')

def get_field_options():
    api = Api(API_KEY)
    
    # Get base ID (using the same method from data loader)
    url = "https://api.airtable.com/v0/meta/bases"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    base_id = None
    if response.status_code == 200:
        bases = response.json().get('bases', [])
        for base in bases:
            if base.get('name') == BASE_NAME:
                base_id = base.get('id')
                break
    
    if not base_id:
        print("Base not found!")
        return
    
    # Get table schema
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        tables = response.json().get('tables', [])
        for table in tables:
            if table.get('name') == Tables.OFFERS:
                fields = table.get('fields', [])
                for field in fields:
                    if field.get('name') == 'Category':
                        options = field.get('options', {}).get('choices', [])
                        print("\nValid Category options:")
                        for option in options:
                            print(f"- {option.get('name')}")
                        return
    
    print("Could not find Category field options")

if __name__ == "__main__":
    get_field_options()
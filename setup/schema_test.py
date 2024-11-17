import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
API_KEY = os.getenv('AI_AGENT_AIRTABLE_API_KEY')
BASE_ID = 'appdbL326NiaPg7Dm'  # Replace with your actual base ID

def get_base_schema(base_id):
    """Fetches the schema of the tables in the specified base."""
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"Fetching schema from URL: {url}")  # Print the URL for debugging
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            schema_data = response.json()
            print("Base Schema:")
            print(schema_data)
        else:
            print(f"Error fetching schema: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    get_base_schema(BASE_ID)
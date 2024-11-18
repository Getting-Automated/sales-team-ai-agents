import os
import requests
from dotenv import load_dotenv
from config.airtable_config import (
    BASE_NAME, 
    WORKSPACE_ID, 
    Tables, 
    TABLE_SCHEMAS, 
    SAMPLE_DATA
)
import argparse
from pyairtable import Table, Api
import sys

# Load environment variables
load_dotenv()
API_KEY = os.getenv('AI_AGENT_AIRTABLE_API_KEY')

def delete_base(base_id):
    """Deletes an existing Airtable base"""
    print(f"Deleting base {base_id}...")
    
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code in [200, 204]:
            print(f"Base {base_id} deleted successfully")
            return True
        else:
            print(f"Failed to delete base: {response.text}")
            return False
    except Exception as e:
        print(f"Error deleting base: {str(e)}")
        return False

def list_bases(workspace_id):
    """Lists all bases in a workspace"""
    print(f"Listing bases in workspace {workspace_id}...")
    
    url = f"https://api.airtable.com/v0/meta/workspaces/{workspace_id}/bases"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            bases = response.json().get('bases', [])
            return bases
        else:
            print(f"Failed to list bases: {response.text}")
            return []
    except Exception as e:
        print(f"Error listing bases: {str(e)}")
        return []

def find_base_by_name(workspace_id, base_name):
    """Finds a base by name in the workspace"""
    bases = list_bases(workspace_id)
    for base in bases:
        if base.get('name') == base_name:
            return base.get('id')
    return None

def create_workspace(name="AI Sales Workspace"):
    """Creates a new Airtable workspace"""
    print(f"Creating new workspace '{name}'...")
    
    url = "https://api.airtable.com/v0/meta/workspaces"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {"name": name}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            workspace_data = response.json()
            print(f"Workspace created successfully with ID: {workspace_data['id']}")
            return workspace_data['id']
        else:
            raise Exception(f"Failed to create workspace: {response.text}")
    except Exception as e:
        print(f"Error creating workspace: {str(e)}")
        return None

def initialize_table(table_name, base_id):
    """Initializes a table with sample data"""
    try:
        print(f"Initializing {table_name} table...")
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        sample_record = SAMPLE_DATA[table_name]
        payload = {
            "fields": sample_record
        }
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"{table_name} table initialized with sample data.\n")
        else:
            raise Exception(f"Error initializing {table_name}: {response.text}")
    except Exception as e:
        print(f"Error initializing {table_name}: {str(e)}")
        raise

def create_base(workspace_id, base_name):
    """Creates a new Airtable base with defined schema"""
    print(f"Creating new base '{base_name}'...")
    
    url = "https://api.airtable.com/v0/meta/bases"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Define select field choices
    select_options = {
        "Lead Tier": [
            {"name": "High"},
            {"name": "Medium"},
            {"name": "Low"}
        ],
        "Campaign Tier": [
            {"name": "High"},
            {"name": "Medium"},
            {"name": "Low"}
        ],
        "Wait Time": [
            {"name": "Same Day"},
            {"name": "1 Day"},
            {"name": "2 Days"},
            {"name": "3 Days"},
            {"name": "5 Days"},
            {"name": "1 Week"},
            {"name": "2 Weeks"}
        ],
        "Status": [
            {"name": "Drafted"},
            {"name": "Ready to Send"},
            {"name": "Sent"},
            {"name": "Engaged"},
            {"name": "Completed"},
            {"name": "Stopped"}
        ],
        "Category": [
            {"name": "Time & Attendance"},
            {"name": "Payroll & Billing"},
            {"name": "Candidate Management"},
            {"name": "Client Management"},
            {"name": "Compliance"},
            {"name": "Reporting"}
        ],
        "Target Client Type": [
            {"name": "Small Staffing"},
            {"name": "Mid-size Staffing"},
            {"name": "Enterprise Staffing"},
            {"name": "Healthcare Staffing"},
            {"name": "IT Staffing"},
            {"name": "Industrial Staffing"}
        ]
    }
    
    # Simplify the table structure for initial creation
    airtable_tables = []
    for table_name, fields in TABLE_SCHEMAS.items():
        formatted_fields = []
        for field in fields:
            # Start with basic field definition
            field_def = {
                "name": field["name"],
                "type": field["type"]
            }
            
            # Add options based on field type
            if field["type"] == "number":
                field_def["options"] = {"precision": 0}
            elif field["type"] in ["singleSelect", "multipleSelects"]:
                if field["name"] in select_options:
                    field_def["options"] = {"choices": select_options[field["name"]]}
                else:
                    field_def["options"] = {"choices": []}
            elif field["type"] == "date":
                field_def["options"] = {"dateFormat": {"name": "local"}}
            # No options for text fields
                
            formatted_fields.append(field_def)
            
        table = {
            "name": table_name,
            "fields": formatted_fields
        }
        airtable_tables.append(table)
    
    payload = {
        "name": base_name,
        "workspaceId": workspace_id,
        "tables": airtable_tables
    }
    
    try:
        # Debug: Print the payload
        print("\nAPI Request Payload:")
        print(payload)
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            base_data = response.json()
            print(f"Base created successfully with ID: {base_data['id']}")
            return base_data['id']
        else:
            print(f"\nAPI Response Status: {response.status_code}")
            print(f"API Response Headers: {response.headers}")
            print(f"API Response Body: {response.text}")
            raise Exception(f"Failed to create base: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error creating base: {str(e)}")
        raise

def get_existing_base_id():
    """Get ID of existing base"""
    api = Api(API_KEY)
    bases = api.workspace(WORKSPACE_ID).list_bases()
    
    for base in bases:
        if base['name'] == BASE_NAME:
            return base['id']
    return None

def main():
    """Main initialization function with delete/recreate capability"""
    parser = argparse.ArgumentParser(description='Initialize or reinitialize Airtable base')
    parser.add_argument('--force', action='store_true', 
                      help='Force delete and recreate if base exists')
    parser.add_argument('--delete-only', action='store_true',
                      help='Only delete the existing base without recreating')
    parser.add_argument('--get-base-id', action='store_true',
                      help='Get the ID of the existing base')
    args = parser.parse_args()

    if args.get_base_id:
        base_id = get_existing_base_id()
        if base_id:
            print(base_id)
            return base_id
        else:
            sys.exit(1)
    
    print("Starting Airtable initialization...\n")
    
    if not API_KEY:
        raise ValueError("AI_AGENT_AIRTABLE_API_KEY not found in environment variables")
    
    try:
        # Check if base already exists
        existing_base_id = find_base_by_name(WORKSPACE_ID, BASE_NAME)
        
        if existing_base_id:
            print(f"Found existing base: {existing_base_id}")
            if args.force or args.delete_only:
                if delete_base(existing_base_id):
                    print("Existing base deleted successfully")
                else:
                    raise Exception("Failed to delete existing base")
                    
                if args.delete_only:
                    print("Delete-only operation completed")
                    return None
            else:
                print("Base already exists. Use --force to delete and recreate, or --delete-only to just delete")
                return existing_base_id
        
        # Create new base
        base_id = create_base(WORKSPACE_ID, BASE_NAME)
        
        # Initialize tables with sample data
        for table_name in TABLE_SCHEMAS.keys():
            initialize_table(table_name, base_id)
        
        print("\nSetup Complete!")
        print(f"Workspace ID: {WORKSPACE_ID}")
        print(f"Base ID: {base_id}")
        print("\nSave these IDs for future reference.")
        
        return base_id
        
    except Exception as e:
        print(f"\nSetup failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()

# Normal initialization (only creates if doesn't exist): python airtable_initialization.py
# Force delete and recreate: python airtable_initialization.py --force
# Delete only (if you just want to remove the base): python airtable_initialization.py --delete-only
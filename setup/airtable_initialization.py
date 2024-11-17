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

# Load environment variables
load_dotenv()

# Airtable configuration
API_KEY = os.getenv('AI_AGENT_AIRTABLE_API_KEY')

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

def main():
    """Main initialization function"""
    print("Starting Airtable initialization...\n")
    
    # Verify API key
    if not API_KEY:
        raise ValueError("AI_AGENT_AIRTABLE_API_KEY not found in environment variables")
    
    try:
        # Create base using workspace ID from config
        base_id = create_base(WORKSPACE_ID, BASE_NAME)
        
        # Initialize tables
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

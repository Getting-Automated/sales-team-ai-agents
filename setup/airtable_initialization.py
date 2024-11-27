import os
import requests
from dotenv import load_dotenv
from config.airtable_config import (
    BASE_NAME, 
    WORKSPACE_ID, 
    Tables, 
    TABLE_SCHEMAS, 
    SAMPLE_DATA,
    SELECT_OPTIONS
)
import argparse
from pyairtable import Table, Api
import sys
import json

# Load environment variables
load_dotenv()
API_KEY = os.getenv('AI_AGENT_AIRTABLE_API_KEY')

def delete_base(base_id):
    """Deletes an existing Airtable base"""
    print(f"Deleting base {base_id}...")
    
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Scope": "workspacesAndBases:manage"
    }
    
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code in [200, 204]:
            print(f"Base {base_id} deleted successfully")
            return True
        else:
            error_msg = response.json().get('error', {})
            print(f"Failed to delete base: {error_msg}")
            if error_msg.get('type') == 'INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND':
                print("\nThis error usually means one of the following:")
                print("1. Your API token doesn't have the 'workspacesAndBases:manage' scope")
                print("2. You need to be an Enterprise admin")
                print("3. You need to use an enterprise-scoped token")
            return False
    except Exception as e:
        print(f"Error deleting base: {str(e)}")
        return False

def list_bases(workspace_id):
    """Lists all bases in a workspace"""
    print(f"Listing bases in workspace {workspace_id}...")
    
    url = "https://api.airtable.com/v0/meta/bases"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            bases = response.json().get('bases', [])
            # Debug: Print all bases before filtering
            print("\nAll available bases:")
            for base in bases:
                print(f"- {base.get('name')} (ID: {base.get('id')}, Workspace: {base.get('workspaceId')})")
            
            # Include bases with None workspaceId
            if workspace_id:
                bases = [base for base in bases if base.get('workspaceId') == workspace_id or base.get('workspaceId') is None]
                print(f"\nBases in workspace {workspace_id} (including unassigned):")
                for base in bases:
                    print(f"- {base.get('name')} (ID: {base.get('id')})")
            
            return bases
        else:
            print(f"Failed to list bases: {response.text}")
            return []
    except Exception as e:
        print(f"Error listing bases: {str(e)}")
        return []

def find_base_by_name(workspace_id, base_name):
    """Finds a base by name in the workspace"""
    print(f"\nLooking for base named '{base_name}'...")
    bases = list_bases(workspace_id)
    for base in bases:
        print(f"Checking base: {base.get('name')} (ID: {base.get('id')})")
        if base.get('name') == base_name:
            print(f"Found matching base: {base.get('name')} (ID: {base.get('id')})")
            return base.get('id')
    print(f"No base found with name '{base_name}'")
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
                field_def["options"] = {"precision": 1}
            elif field["type"] in ["singleSelect", "multipleSelects"]:
                if field["name"] in SELECT_OPTIONS:
                    field_def["options"] = SELECT_OPTIONS[field["name"]]
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

def update_base_schema(base_id):
    """Updates an existing base's schema by creating new tables and renaming old ones"""
    print(f"Updating schema for base {base_id}...")
    
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get existing tables
        response = requests.get(url, headers=headers)
        existing_tables = response.json().get('tables', [])
        existing_table_names = {table['name']: table['id'] for table in existing_tables}
        
        print("\nExisting tables:", list(existing_table_names.keys()))
        
        # Update each table
        for table_name, fields in TABLE_SCHEMAS.items():
            table_name_str = table_name.value
            temp_table_name = f"{table_name_str}_new"
            formatted_fields = []
            
            print(f"\nProcessing table: {table_name_str}")
            
            # Format fields as before
            for field in fields:
                field_def = {
                    "name": field["name"],
                    "type": field["type"]
                }
                
                if field["type"] == "number":
                    field_def["options"] = {"precision": 1}
                elif field["type"] in ["singleSelect", "multipleSelects"]:
                    if field["name"] in SELECT_OPTIONS:
                        field_def["options"] = SELECT_OPTIONS[field["name"]]
                    else:
                        field_def["options"] = {"choices": []}
                elif field["type"] == "date":
                    field_def["options"] = {"dateFormat": {"name": "local"}}
                
                formatted_fields.append(field_def)
                print(f"  Added field: {field_def['name']} ({field_def['type']})")
            
            if table_name_str in existing_table_names:
                # Create new table with temporary name
                create_payload = {
                    "name": temp_table_name,
                    "fields": formatted_fields
                }
                
                print(f"\nCreating temporary table: {temp_table_name}")
                create_response = requests.post(url, headers=headers, json=create_payload)
                
                if create_response.status_code == 200:
                    print(f"✓ Created temporary table {temp_table_name}")
                    
                    # Rename old table to backup name
                    old_table_id = existing_table_names[table_name_str]
                    backup_name = f"{table_name_str}_backup"
                    rename_payload = {"name": backup_name}
                    
                    print(f"Renaming old table to {backup_name}")
                    rename_response = requests.patch(
                        f"{url}/{old_table_id}",
                        headers=headers,
                        json=rename_payload
                    )
                    
                    if rename_response.status_code == 200:
                        print(f"✓ Renamed old table to {backup_name}")
                        
                        # Rename new table to final name
                        new_table_id = create_response.json()['id']
                        final_rename_payload = {"name": table_name_str}
                        
                        final_rename_response = requests.patch(
                            f"{url}/{new_table_id}",
                            headers=headers,
                            json=final_rename_payload
                        )
                        
                        if final_rename_response.status_code == 200:
                            print(f"✓ Renamed new table to {table_name_str}")
                        else:
                            print(f"Failed to rename new table: {final_rename_response.text}")
                    else:
                        print(f"Failed to rename old table: {rename_response.text}")
                else:
                    print(f"Failed to create temporary table: {create_response.text}")
            else:
                # Create new table directly if it doesn't exist
                create_payload = {
                    "name": table_name_str,
                    "fields": formatted_fields
                }
                
                print(f"\nCreating new table: {table_name_str}")
                create_response = requests.post(url, headers=headers, json=create_payload)
                
                if create_response.status_code == 200:
                    print(f"✓ Created new table {table_name_str}")
                else:
                    print(f"Failed to create table: {create_response.text}")
        
        return True
    except Exception as e:
        print(f"Error updating base schema: {str(e)}")
        return False

def main():
    """Main initialization function"""
    parser = argparse.ArgumentParser(description='Initialize or update Airtable base')
    parser.add_argument('--force', action='store_true', 
                      help='Force delete and recreate if base exists (requires Enterprise)')
    parser.add_argument('--delete-only', action='store_true',
                      help='Only delete the existing base (requires Enterprise)')
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
                # Update existing base schema
                if update_base_schema(existing_base_id):
                    print("Base schema updated successfully")
                    return existing_base_id
                else:
                    raise Exception("Failed to update base schema")
        else:
            # Create new base only if it doesn't exist
            base_id = create_base(WORKSPACE_ID, BASE_NAME)
            print(f"New base created with ID: {base_id}")
            return base_id
        
    except Exception as e:
        print(f"\nSetup failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
# Normal initialization (only creates if doesn't exist): python airtable_initialization.py
# Force delete and recreate: python airtable_initialization.py --force
# Delete only (if you just want to remove the base): python airtable_initialization.py --delete-only

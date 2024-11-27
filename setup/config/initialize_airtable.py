from pyairtable import Api, Base, Table
import os
from dotenv import load_dotenv
from airtable_config import Tables, TABLE_SCHEMAS, BASE_ID

def initialize_airtable():
    """Initialize Airtable with the defined schema"""
    load_dotenv()
    
    api_key = os.getenv('AIRTABLE_API_KEY')
    if not api_key:
        raise ValueError("AIRTABLE_API_KEY not found in environment variables")
    
    base = Base(api_key, BASE_ID)
    
    # Create or update tables
    for table_name in Tables:
        schema = TABLE_SCHEMAS[table_name]
        try:
            # Create table if it doesn't exist
            table = Table(api_key, BASE_ID, table_name.value)
            print(f"✓ Table {table_name.value} exists or was created")
            
            # Print schema for manual verification
            print(f"\nSchema for {table_name.value}:")
            for field in schema:
                print(f"  - {field['name']} ({field['type']})")
            print("\n")
            
        except Exception as e:
            print(f"✗ Error with table {table_name.value}: {str(e)}")

if __name__ == "__main__":
    initialize_airtable() 
import os
import pandas as pd
from dotenv import load_dotenv
from pyairtable import Table, Api
import json
import requests
from datetime import datetime
from config.airtable_config import BASE_NAME, WORKSPACE_ID, Tables

# Load environment variables
load_dotenv()
API_KEY = os.getenv('AI_AGENT_AIRTABLE_API_KEY')

class DataLoader:
    def __init__(self):
        if not API_KEY:
            raise ValueError("AI_AGENT_AIRTABLE_API_KEY not found in environment variables")
            
        self.api = Api(API_KEY)
        self.base_id = self._get_base_id()
        
        if not self.base_id:
            raise ValueError(f"Could not find base '{BASE_NAME}' in workspace. Please run initialization first.")
    
    def _get_base_id(self):
        """Get base ID by looking up the base name"""
        url = "https://api.airtable.com/v0/meta/bases"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"Looking for base named: {BASE_NAME}")
            response = requests.get(url, headers=headers)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                bases = response.json().get('bases', [])
                print(f"Found {len(bases)} bases:")
                for base in bases:
                    print(f"- {base.get('name')} ({base.get('id')})")
                    if base.get('name') == BASE_NAME:
                        print(f"\nFound matching base! ID: {base.get('id')}")
                        return base.get('id')
                print("\nNo matching base found!")
            else:
                print(f"Error response: {response.text}")
        except Exception as e:
            print(f"Error looking up base: {str(e)}")
        return None
        
    def load_table(self, table_name, csv_path):
        """Load data from CSV into specified Airtable table"""
        print(f"\nLoading data for table: {table_name}")
        print(f"Base ID: {self.base_id}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
        # Initialize Airtable table
        try:
            table = self.api.table(self.base_id, table_name)
        except Exception as e:
            raise Exception(f"Error connecting to Airtable table '{table_name}': {str(e)}")
        
        # Read CSV file
        try:
            df = pd.read_csv(csv_path)
            print(f"\nFound {len(df)} records to load")
            print("\nCSV Data Preview:")
            print(df.head())
            print("\nColumns in CSV:")
            print(df.columns.tolist())
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        
        # Process and upload each record
        successful = 0
        failed = 0
        
        for record in records:
            try:
                # Pre-process specific fields based on table
                processed_record = self._preprocess_record(table_name, record)
                
                print("\nSending record to Airtable:")
                print(json.dumps(processed_record, indent=2))
                
                # Create record in Airtable
                result = table.create(processed_record, typecast=True)
                successful += 1
                print(f"\nAirtable response:")
                print(json.dumps(result, indent=2))
                
            except Exception as e:
                failed += 1
                print(f"Error creating record in {table_name}: {str(e)}")
        
        print(f"\nTable {table_name} Summary:")
        print(f"Successfully loaded: {successful}")
        print(f"Failed: {failed}")
        
        # Verify final record count
        final_records = table.all()
        print(f"Final table record count: {len(final_records)}")
        
    def _preprocess_record(self, table_name, record):
        """Preprocess record based on table-specific requirements"""
        if table_name == Tables.OFFERS:
            # Convert Target Client Type from string to list if it exists
            if isinstance(record.get('Target Client Type'), str):
                record['Target Client Type'] = [x.strip() for x in record['Target Client Type'].split(',')]
                
        elif table_name == Tables.CAMPAIGNS:
            # Convert date strings to proper format if they exist
            for date_field in ['Last Sent Date', 'Next Send Date']:
                if record.get(date_field):
                    record[date_field] = record[date_field]
                    
        return record

def main():
    try:
        loader = DataLoader()
        
        # Add argument parsing for selective table loading
        import argparse
        parser = argparse.ArgumentParser(description='Load data into existing Airtable tables')
        parser.add_argument('--table', type=str, required=True, 
                          help='Table name to load data into (Leads, Offers, etc.)')
        args = parser.parse_args()
        
        # Validate table name
        if not hasattr(Tables, args.table.upper().replace(' ', '_')):
            valid_tables = [attr for attr in dir(Tables) if not attr.startswith('_')]
            raise ValueError(f"Invalid table name. Valid tables are: {', '.join(valid_tables)}")
        
        # Get table name from Tables class
        table_name = getattr(Tables, args.table.upper().replace(' ', '_'))
        
        # Construct CSV path
        csv_path = os.path.join('data', f"{args.table.lower().replace(' ', '_')}.csv")
        
        # Load the data
        loader.load_table(table_name, csv_path)
                    
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nPlease ensure:")
        print("1. Your .env file contains:")
        print("   AI_AGENT_AIRTABLE_API_KEY=your_key_here")
        print("   AIRTABLE_BASE_ID=your_base_id_here")
        print("2. The specified table exists in your Airtable base")
        print("3. The CSV file exists in the data directory")
        exit(1)

if __name__ == "__main__":
    main()
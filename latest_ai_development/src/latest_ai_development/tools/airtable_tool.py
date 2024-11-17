# tools/airtable_tool.py

from crewai.tools import BaseTool
import os
from pyairtable import Table

class AirtableTool(BaseTool):
    name = "airtable_tool"
    description = "Interacts with Airtable for data storage and retrieval."

    def __init__(self):
        self.api_key = os.getenv('AI_AGENT_AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')

    def _run(self, action: str, table_name: str, data: dict = None, record_id: str = None) -> dict:
        """Perform CRUD operations on Airtable."""
        if not all([self.api_key, self.base_id]):
            return {"error": "Airtable API credentials not found."}
        
        try:
            table = Table(self.api_key, self.base_id, table_name)
            
            if action == "create":
                cleaned_data = self._clean_data_for_schema(data, table_name)
                return table.create(cleaned_data)
            elif action == "update":
                cleaned_data = self._clean_data_for_schema(data, table_name)
                return table.update(record_id, cleaned_data)
            elif action == "retrieve":
                return table.get(record_id)
            elif action == "list":
                return table.all()
            else:
                return {"error": "Invalid action specified."}
        except Exception as e:
            return {"error": str(e)}

    def _clean_data_for_schema(self, data: dict, table_name: str) -> dict:
        """Clean and validate data against the table schema"""
        schemas = {
            "Leads": {
                "Lead ID": "singleLineText",
                "Name": "singleLineText",
                "Email": "email",
                "Company": "singleLineText",
                "Role": "singleLineText",
                "Lead Score": "number",
                "Lead Tier": ["High", "Medium", "Low"]
            },
            "Campaign Drafts": {
                "Lead ID": "singleLineText",
                "Campaign Name": "singleLineText",
                "Campaign Tier": ["High", "Medium", "Low"],
                "Sequence Position": "number",
                "Wait Time": ["Same Day", "1 Day", "2 Days", "3 Days", "5 Days", "1 Week", "2 Weeks"],
                "Email Draft": "multilineText",
                "Status": ["Drafted", "Ready to Send", "Sent", "Engaged", "Completed", "Stopped"]
            },
            "Pain Points": {
                "Industry": "singleLineText",
                "Pain Points": "multilineText",
                "Keywords": "multilineText",
                "Highlighted Quotes": "multilineText"
            },
            "Offers": {
                "Offer ID": "singleLineText",
                "Offer Name": "singleLineText",
                "Category": ["Time & Attendance", "Payroll & Billing", "Candidate Management", 
                           "Client Management", "Compliance", "Reporting"],
                "Description": "multilineText",
                "Key Benefits": "multilineText",
                "Industry Fit": "multilineText",
                "Customization Options": "multilineText",
                "Target Client Type": ["Small Staffing", "Mid-size Staffing", "Enterprise Staffing",
                                     "Healthcare Staffing", "IT Staffing", "Industrial Staffing"]
            }
        }

        if table_name not in schemas:
            return data

        cleaned_data = {}
        schema = schemas[table_name]

        for field, value in data.items():
            if field in schema:
                field_type = schema[field]
                
                if isinstance(field_type, list) and value not in field_type:
                    continue
                
                if field_type == "number" and isinstance(value, str):
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                
                cleaned_data[field] = value

        return cleaned_data

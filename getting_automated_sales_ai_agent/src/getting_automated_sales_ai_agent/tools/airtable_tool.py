# tools/airtable_tool.py

from crewai.tools import BaseTool
from pydantic import Field, BaseModel
import os
from pyairtable import Table
from typing import Optional, Dict, Any, Type

class AirtableToolArgs(BaseModel):
    action: str = Field(description="CRUD action to perform (create, update, retrieve, list)")
    table_name: str = Field(description="Name of the Airtable table")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Data for create/update operations")
    record_id: Optional[str] = Field(default=None, description="Record ID for update/retrieve operations")

class AirtableTool(BaseTool):
    name: str = "airtable_tool"
    description: str = "Interacts with Airtable for data storage and retrieval."
    args_schema: Type[BaseModel] = AirtableToolArgs
    llm: Any = Field(..., description="LLM to use for the tool")
    api_key: Optional[str] = Field(default=None, description="Airtable API key")
    base_id: Optional[str] = Field(default=None, description="Airtable base ID")
    
    def __init__(self, llm: Any = None, **kwargs):
        super().__init__(llm=llm, **kwargs)
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        
        if not self.api_key or not self.base_id:
            print("Warning: Airtable credentials not found in environment variables")
            print(f"API Key present: {'Yes' if self.api_key else 'No'}")
            print(f"Base ID present: {'Yes' if self.base_id else 'No'}")

    def _run(self, action: str, table_name: str, data: dict = None, record_id: str = None) -> dict:
        """Perform CRUD operations on Airtable."""
        if not self.api_key or not self.base_id:
            return {
                "error": "Airtable credentials not found",
                "details": "Please ensure AIRTABLE_API_KEY and AIRTABLE_BASE_ID are set in your environment"
            }
        
        try:
            table = Table(self.api_key, self.base_id, table_name)
            
            if action == "create":
                if not data:
                    return {"error": "Data required for create operation"}
                cleaned_data = self._clean_data_for_schema(data, table_name)
                return table.create(cleaned_data)
            
            elif action == "update":
                if not data or not record_id:
                    return {"error": "Both data and record_id required for update operation"}
                cleaned_data = self._clean_data_for_schema(data, table_name)
                return table.update(record_id, cleaned_data)
            
            elif action == "retrieve":
                if not record_id:
                    return {"error": "Record ID required for retrieve operation"}
                return table.get(record_id)
            
            elif action == "list":
                return table.all()
            
            else:
                return {"error": f"Invalid action: {action}"}
                
        except Exception as e:
            return {
                "error": f"Airtable operation failed: {str(e)}",
                "details": {
                    "action": action,
                    "table": table_name,
                    "base_id": self.base_id[:5] + "..." if self.base_id else None
                }
            }

    def _clean_data_for_schema(self, data: dict, table_name: str) -> dict:
        """Clean and validate data against the table schema"""
        schemas = {
            "Leads": {
                "Lead ID": str,
                "Name": str,
                "Email": str,
                "Company": str,
                "Title": str,
                "LinkedIn URL": str,
                "Company LinkedIn": str,
                "Raw Data": str
            },
            "Lead Evaluations": {
                "Lead ID": str,
                "Individual Score": float,
                "Company Score": float,
                "Overall Score": float,
                "Decision Making Level": ["Final Decision Maker", "Key Influencer", "Budget Holder", "Individual Contributor"],
                "Department Match": list,
                "Industry Match": list,
                "Technical Analysis": str,
                "Company Analysis": str,
                "Evaluation Summary": str
            },
            "Pain Points": {
                "Lead ID": str,
                "Primary Pain Points": str,
                "Technical Challenges": str,
                "Operational Challenges": str,
                "Industry Specific Issues": str,
                "Analysis": str,
                "Priority Level": ["High", "Medium", "Low"]
            },
            "Solution Offers": {
                "Lead ID": str,
                "Solution Name": str,
                "Value Proposition": str,
                "Key Benefits": str,
                "Technical Fit": str,
                "ROI Analysis": str,
                "Customization Notes": str
            },
            "Email Campaigns": {
                "Lead ID": str,
                "Email Subject": str,
                "Email Body": str,
                "Sequence Number": int,
                "Wait Days": int,
                "Personalization Notes": str,
                "Pain Points Addressed": str,
                "Call To Action": str
            }
        }

        if table_name not in schemas:
            return data

        cleaned_data = {}
        schema = schemas[table_name]

        for field, value in data.items():
            if field in schema:
                field_type = schema[field]
                
                if isinstance(field_type, list):
                    if isinstance(value, list):
                        cleaned_data[field] = [v for v in value if v in field_type]
                    elif value in field_type:
                        cleaned_data[field] = value
                elif field_type in [int, float] and isinstance(value, str):
                    try:
                        cleaned_data[field] = field_type(value)
                    except ValueError:
                        continue
                elif isinstance(value, field_type):
                    cleaned_data[field] = value
                elif field_type == str:
                    cleaned_data[field] = str(value)

        return cleaned_data

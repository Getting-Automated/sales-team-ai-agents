# tools/airtable_tool.py

from crewai.tools import BaseTool
from pydantic import Field, BaseModel
import os
from pyairtable import Table
from typing import Optional, Dict, Any, Type

class AirtableToolArgs(BaseModel):
    action: str = Field(
        description="Action to perform: 'create', 'update', 'get', 'search'"
    )
    table_name: str = Field(
        description="Name of the Airtable table to interact with"
    )
    data: Optional[Dict] = Field(
        description="Data to create or update record with",
        default=None
    )
    record_id: Optional[str] = Field(
        description="Record ID for updates or retrievals",
        default=None
    )
    search_field: Optional[str] = Field(
        description="Field to search by (e.g., 'Email')",
        default=None
    )
    search_value: Optional[str] = Field(
        description="Value to search for",
        default=None
    )

class AirtableTool(BaseTool):
    name: str = "AirtableTool"
    description: str = """
    Tool for interacting with Airtable. Can create, update, get, and search records.
    Handles evaluation statuses and scores for leads.
    """
    args_schema: Type[BaseModel] = AirtableToolArgs
    api_key: str = Field(default_factory=lambda: os.environ.get("AI_AGENT_AIRTABLE_API_KEY"))
    base_id: str = Field(default_factory=lambda: os.environ.get("AIRTABLE_BASE_ID"))

    def __init__(self, **data):
        super().__init__(**data)
        if not self.api_key:
            raise ValueError("AI_AGENT_AIRTABLE_API_KEY environment variable is not set")
        if not self.base_id:
            raise ValueError("AIRTABLE_BASE_ID environment variable is not set")

    def _run(self, action: str, table_name: str, data: Optional[Dict] = None,
            record_id: Optional[str] = None, search_field: Optional[str] = None,
            search_value: Optional[str] = None) -> Dict:
        """Execute the Airtable operation"""
        try:
            table = Table(self.api_key, self.base_id, table_name)
            
            if action == "search":
                if not search_field or not search_value:
                    return {"error": "Search field and value are required for search operation"}
                # Search for existing record - using exact field name from schema
                formula = f"LOWER({search_field}) = LOWER('{search_value}')"
                records = table.all(formula=formula)
                if records:
                    return {"record": records[0], "record_id": records[0]["id"]}
                return {"records": []}
                
            elif action == "create":
                if not data:
                    return {"error": "Data is required for create operation"}
                # Clean and validate data before creation
                cleaned_data = self._clean_data_for_schema(data, table_name)
                created_record = table.create(cleaned_data)
                return {"record": created_record, "record_id": created_record["id"]}
                
            elif action == "update":
                if not record_id:
                    return {"error": "Record ID is required for update operation"}
                if not data:
                    return {"error": "Data is required for update operation"}
                # Clean and validate data before update
                cleaned_data = self._clean_data_for_schema(data, table_name)
                updated_record = table.update(record_id, cleaned_data)
                return {"record": updated_record, "record_id": record_id}
                
            elif action == "get":
                if not record_id:
                    return {"error": "Record ID is required for get operation"}
                record = table.get(record_id)
                return {"record": record, "record_id": record_id}
                
            else:
                return {"error": f"Unsupported action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}

    def _clean_data_for_schema(self, data: dict, table_name: str) -> dict:
        """Clean and validate data against the table schema"""
        schemas = {
            "Leads": {
                "Lead ID": str,
                "Name": str,
                "Email": str,
                "Company": str,
                "Role": str,
                "Individual Score": float,
                "Company Score": float,
                "Individual Evaluation Status": ["Completed", "In Progress", "Not Started", "Needs Review"],
                "Company Evaluation Status": ["Completed", "In Progress", "Not Started", "Needs Review"],
                "Role Match Score": float,
                "Authority Match Score": float,
                "Department Match Score": float,
                "Skills Match Score": float,
                "Industry Match Score": float,
                "Size Match Score": float,
                "Location Match Score": float,
                "Growth Match Score": float,
                "Lead Tier": ["High", "Medium", "Low"],
                "Last Evaluated": str,  # Date will be handled as string
                "Individual Analysis": str,
                "Company Analysis": str,
                "Enriched Individual Data": str,
                "Enriched Company Data": str,
                "Raw Data": str
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
        
        cleaned_data = {}
        schema = schemas.get(table_name, {})
        
        for field, value in data.items():
            if field in schema:
                field_type = schema[field]
                
                if isinstance(field_type, list):
                    if value in field_type:
                        cleaned_data[field] = value
                elif field_type in [int, float] and isinstance(value, (int, float, str)):
                    try:
                        cleaned_data[field] = field_type(value)
                    except ValueError:
                        continue
                elif isinstance(value, field_type):
                    cleaned_data[field] = value
                elif field_type == str:
                    cleaned_data[field] = str(value)

        return cleaned_data

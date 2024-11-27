# tools/airtable_tool.py

from crewai.tools import BaseTool
from pydantic import Field, BaseModel
import os
from pyairtable import Table
from typing import Optional, Dict, Any, Type
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.debug(f"AirtableTool executing action: {action}")
            logger.debug(f"Input data: {data}")
            
            table = Table(self.api_key, self.base_id, table_name)
            
            if action == "search":
                if not search_field or not search_value:
                    return {"error": "Search field and value are required for search operation"}
                # Search for existing record
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
                logger.debug(f"Cleaned data for create: {cleaned_data}")
                # Enable typecast for automatic data conversion
                created_record = table.create(cleaned_data, typecast=True)
                return {"record": created_record, "record_id": created_record["id"]}
                
            elif action == "update":
                if not record_id:
                    return {"error": "Record ID is required for update operation"}
                if not data:
                    return {"error": "Data is required for update operation"}
                # Clean and validate data before update
                cleaned_data = self._clean_data_for_schema(data, table_name)
                logger.debug(f"Cleaned data for update: {cleaned_data}")
                # Enable typecast for automatic data conversion
                updated_record = table.update(record_id, cleaned_data, typecast=True)
                return {"record": updated_record, "record_id": record_id}
                
            elif action == "get":
                if not record_id:
                    return {"error": "Record ID is required for get operation"}
                record = table.get(record_id)
                return {"record": record, "record_id": record_id}
                
            else:
                return {"error": f"Unsupported action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in AirtableTool: {str(e)}")
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
                "LinkedIn URL": str,
                "Company LinkedIn": str,
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
                "Last Evaluated": str,
                "Individual Analysis": str,
                "Company Analysis": str,
                "Enriched Individual Data": str,
                "Enriched Company Data": str,
                "Raw Data": str,
                "Proxycurl Result": str
            }
        }
        
        cleaned_data = {}
        schema = schemas.get(table_name, {})
        logger.debug(f"Cleaning data for table {table_name}")
        logger.debug(f"Input data: {data}")
        
        # Score conversion mapping
        score_mapping = {
            "High": 90,
            "Strong": 90,
            "Medium": 70,
            "Moderate": 70,
            "Low": 30,
            "Weak": 30
        }
        
        for field, value in data.items():
            if field in schema:
                field_type = schema[field]
                logger.debug(f"Processing field: {field}, value: {value}, expected type: {field_type}")
                
                # Skip empty values
                if value is None or value == "":
                    continue
                    
                # Handle Last Evaluated date field
                if field == "Last Evaluated":
                    try:
                        # If it's already a date string in ISO format, use it
                        if isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-":
                            cleaned_data[field] = value
                        else:
                            # Convert to ISO format YYYY-MM-DD
                            cleaned_data[field] = datetime.now().strftime("%Y-%m-%d")
                    except Exception as e:
                        logger.warning(f"Failed to process date for {field}: {str(e)}")
                        cleaned_data[field] = datetime.now().strftime("%Y-%m-%d")
                    continue
                    
                # Handle JSON fields
                if field in ["Raw Data", "Proxycurl Result", "Enriched Individual Data", "Enriched Company Data"]:
                    if isinstance(value, (dict, list)):
                        cleaned_data[field] = json.dumps(value)
                    elif isinstance(value, str):
                        # Verify it's valid JSON if it's a string
                        try:
                            json.loads(value)
                            cleaned_data[field] = value
                        except json.JSONDecodeError:
                            cleaned_data[field] = json.dumps({"raw": value})
                    continue
                
                # Handle enum fields
                if isinstance(field_type, list):
                    if value in field_type:
                        cleaned_data[field] = value
                    else:
                        logger.warning(f"Value {value} not in allowed values for field {field}: {field_type}")
                        # Set default value for status fields
                        if "Status" in field:
                            cleaned_data[field] = "Not Started"
                
                # Handle numeric fields
                elif field_type in [int, float]:
                    try:
                        if isinstance(value, str):
                            # Handle score format like "75/100"
                            if "/" in value:
                                numerator = float(value.split("/")[0])
                                cleaned_data[field] = numerator
                            # Handle percentage format
                            elif value.endswith("%"):
                                cleaned_data[field] = float(value.rstrip("%"))
                            # Handle text-based scores
                            elif value in score_mapping:
                                cleaned_data[field] = float(score_mapping[value])
                            else:
                                # Try direct conversion
                                cleaned_data[field] = field_type(value)
                        else:
                            # Direct numeric conversion
                            cleaned_data[field] = field_type(value)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to convert {field} value {value} to {field_type}: {str(e)}")
                        continue
                
                # Handle string fields
                elif field_type == str:
                    if isinstance(value, (dict, list)):
                        cleaned_data[field] = json.dumps(value)
                    else:
                        cleaned_data[field] = str(value)
                
                # Handle direct type matches
                elif isinstance(value, field_type):
                    cleaned_data[field] = value
                
        logger.debug(f"Cleaned data output: {cleaned_data}")
        return cleaned_data

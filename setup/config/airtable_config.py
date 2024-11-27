from enum import Enum

# Base configuration
BASE_NAME = "AI Sales Agent Prospecting"
WORKSPACE_ID = "wspvmw70ZPF8XuEtI"

# Table names
class Tables(str, Enum):
    LEADS = "Leads"
    EMAIL_CAMPAIGNS = "Email Campaigns"

# Define select field options with proper schema
SELECT_OPTIONS = {
    "Individual Evaluation Status": {
        "choices": [
            {"name": "Not Started", "color": "redBright"},
            {"name": "In Progress", "color": "yellowBright"},
            {"name": "Completed", "color": "greenBright"},
            {"name": "Needs Review", "color": "orangeBright"}
        ]
    },
    "Company Evaluation Status": {
        "choices": [
            {"name": "Not Started", "color": "redBright"},
            {"name": "In Progress", "color": "yellowBright"},
            {"name": "Completed", "color": "greenBright"},
            {"name": "Needs Review", "color": "orangeBright"}
        ]
    },
    "Lead Tier": {
        "choices": [
            {"name": "High", "color": "greenBright"},
            {"name": "Medium", "color": "yellowBright"},
            {"name": "Low", "color": "redBright"}
        ]
    }
}

# Table structure
TABLE_SCHEMAS = {
    Tables.LEADS: [
        # Basic Lead Info
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Company", "type": "singleLineText"},
        {"name": "Role", "type": "singleLineText"},
        {"name": "LinkedIn URL", "type": "url"},
        {"name": "Company LinkedIn", "type": "url"},
        
        # Status Fields with proper select options
        {"name": "Individual Evaluation Status", "type": "singleSelect", 
         "options": SELECT_OPTIONS["Individual Evaluation Status"]},
        {"name": "Company Evaluation Status", "type": "singleSelect",
         "options": SELECT_OPTIONS["Company Evaluation Status"]},
        
        # Score Fields
        {"name": "Individual Score", "type": "number", "options": {"precision": 1}},
        {"name": "Company Score", "type": "number", "options": {"precision": 1}},
        {"name": "Role Match Score", "type": "number", "options": {"precision": 1}},
        {"name": "Authority Match Score", "type": "number", "options": {"precision": 1}},
        {"name": "Department Match Score", "type": "number", "options": {"precision": 1}},
        {"name": "Skills Match Score", "type": "number", "options": {"precision": 1}},
        {"name": "Industry Match Score", "type": "number", "options": {"precision": 1}},
        {"name": "Size Match Score", "type": "number", "options": {"precision": 1}},
        {"name": "Location Match Score", "type": "number", "options": {"precision": 1}},
        {"name": "Growth Match Score", "type": "number", "options": {"precision": 1}},
        
        # Analysis Fields
        {"name": "Individual Analysis", "type": "multilineText"},
        {"name": "Company Analysis", "type": "multilineText"},
        {"name": "Enriched Individual Data", "type": "multilineText"},
        {"name": "Enriched Company Data", "type": "multilineText"},
        {"name": "Raw Data", "type": "multilineText"},
        {"name": "Proxycurl Result", "type": "multilineText"},
        
        # Tracking Fields
        {"name": "Lead Tier", "type": "singleSelect", 
         "options": SELECT_OPTIONS["Lead Tier"]},
        {"name": "Last Evaluated", "type": "date"}
    ],
    
    Tables.EMAIL_CAMPAIGNS: [
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Email Subject", "type": "singleLineText"},
        {"name": "Email Body", "type": "multilineText"},
        {"name": "Sequence Number", "type": "number"},
        {"name": "Wait Days", "type": "number"},
        {"name": "Personalization Notes", "type": "multilineText"},
        {"name": "Pain Points Addressed", "type": "multilineText"},
        {"name": "Call To Action", "type": "singleLineText"}
    ]
}

# Sample data for initialization
SAMPLE_DATA = {
    Tables.LEADS.value: {
        "Lead ID": "L001",
        "Name": "John Doe",
        "Email": "john.doe@example.com",
        "Company": "Example Corp",
        "Role": "CTO",
        "Individual Score": 85,
        "Individual Evaluation Status": "Not Started",
        "Company Score": 78,
        "Company Evaluation Status": "Not Started",
        "Lead Tier": "High"
    },
    Tables.EMAIL_CAMPAIGNS.value: {
        "Campaign ID": "C001",
        "Lead ID": "L001",
        "Email Subject": "Improving Your Staffing Operations",
        "Email Body": "Hi [Name],\n\nI noticed your company...",
        "Sequence Number": 1,
        "Wait Time": "1 Day",
        "Status": "Drafted"
    }
}

# Field types reference (for documentation)
FIELD_TYPES = {
    "singleLineText": "Single line text field",
    "email": "Email field",
    "number": "Numeric field",
    "singleSelect": "Single select field with predefined options",
    "multipleSelect": "Multiple select field with predefined options",
    "multilineText": "Multi-line text field",
    "checkbox": "Boolean checkbox field",
    "date": "Date field",
    "dateTime": "Date and time field",
    "attachment": "File attachment field",
    "multipleAttachments": "Multiple file attachments field",
    "url": "URL field",
    "phone": "Phone number field",
    "currency": "Currency field",
    "percent": "Percentage field",
    "duration": "Duration field",
    "rating": "Rating field",
    "barcode": "Barcode field",
    "formula": "Formula field",
    "rollup": "Rollup field",
    "count": "Count field",
    "multipleLookupValues": "Multiple lookup values field",
    "multipleRecordLinks": "Multiple record links field"
}
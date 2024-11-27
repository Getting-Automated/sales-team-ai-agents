from enum import Enum

# Base configuration
BASE_NAME = "AI Sales Agent Prospecting"
WORKSPACE_ID = "wspvmw70ZPF8XuEtI"

# Table names
class Tables(str, Enum):
    LEADS = "Leads"
    EMAIL_CAMPAIGNS = "Email Campaigns"

# Select field options
SELECT_OPTIONS = {
    "Individual Evaluation Status": [
        {"name": "Not Started"},
        {"name": "In Progress"},
        {"name": "Completed"},
        {"name": "Needs Review"}
    ],
    "Company Evaluation Status": [
        {"name": "Not Started"},
        {"name": "In Progress"},
        {"name": "Completed"},
        {"name": "Needs Review"}
    ],
    "Lead Tier": [
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
    ]
}

# Table structure
TABLE_SCHEMAS = {
    Tables.LEADS.value: [
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Company", "type": "singleLineText"},
        {"name": "Role", "type": "singleLineText"},
        {"name": "LinkedIn URL", "type": "url"},
        {"name": "Company LinkedIn", "type": "url"},
        {"name": "Individual Score", "type": "number"},
        {"name": "Individual Evaluation Status", "type": "singleSelect", "options": {"choices": SELECT_OPTIONS["Individual Evaluation Status"]}},
        {"name": "Role Match Score", "type": "number"},
        {"name": "Authority Match Score", "type": "number"},
        {"name": "Department Match Score", "type": "number"},
        {"name": "Skills Match Score", "type": "number"},
        {"name": "Individual Analysis", "type": "multilineText"},
        {"name": "Enriched Individual Data", "type": "multilineText"},
        {"name": "Company Score", "type": "number"},
        {"name": "Company Evaluation Status", "type": "singleSelect", "options": {"choices": SELECT_OPTIONS["Company Evaluation Status"]}},
        {"name": "Industry Match Score", "type": "number"},
        {"name": "Size Match Score", "type": "number"},
        {"name": "Location Match Score", "type": "number"},
        {"name": "Growth Match Score", "type": "number"},
        {"name": "Company Analysis", "type": "multilineText"},
        {"name": "Enriched Company Data", "type": "multilineText"},
        {"name": "Lead Tier", "type": "singleSelect", "options": {"choices": SELECT_OPTIONS["Lead Tier"]}},
        {"name": "Last Evaluated", "type": "date"}
    ],
    Tables.EMAIL_CAMPAIGNS.value: [
        {"name": "Campaign ID", "type": "singleLineText"},
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Email Subject", "type": "singleLineText"},
        {"name": "Email Body", "type": "multilineText"},
        {"name": "Sequence Number", "type": "number"},
        {"name": "Wait Time", "type": "singleSelect", "options": {"choices": SELECT_OPTIONS["Wait Time"]}},
        {"name": "Status", "type": "singleSelect", "options": {"choices": SELECT_OPTIONS["Status"]}},
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
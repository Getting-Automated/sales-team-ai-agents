# Base configuration
BASE_NAME = "AI Sales Agent Prospecting"
WORKSPACE_ID = "wspvmw70ZPF8XuEtI"

# Table names
class Tables:
    LEADS = "Leads"
    CAMPAIGNS = "Campaign Drafts"
    PAIN_POINTS = "Pain Points"
    OFFERS = "Offers"

# Table structure
TABLE_SCHEMAS = {
    Tables.LEADS: [
        {"name": "Lead ID", "type": "singleLineText", "options": {"formatting": {}}},
        {"name": "Name", "type": "singleLineText", "options": {"formatting": {}}},
        {"name": "Email", "type": "email", "options": {"formatting": {}}},
        {"name": "Company", "type": "singleLineText", "options": {"formatting": {}}},
        {"name": "Role", "type": "singleLineText", "options": {"formatting": {}}},
        {"name": "Lead Score", "type": "number", "options": {
            "precision": 1
        }},
        {"name": "Lead Tier", "type": "singleSelect", "options": {
            "choices": [
                {"name": "High"},
                {"name": "Medium"},
                {"name": "Low"}
            ]
        }},
    ],
    Tables.CAMPAIGNS: [
        {"name": "Lead ID", "type": "singleLineText", "options": {"formatting": {}}},
        {"name": "Campaign Name", "type": "singleLineText", "options": {"formatting": {}}},
        {"name": "Campaign Tier", "type": "singleSelect", "options": {
            "choices": [
                {"name": "High"},
                {"name": "Medium"},
                {"name": "Low"}
            ]
        }},
        {"name": "Sequence Position", "type": "number", "options": {
            "precision": 0,
        }},
        {"name": "Wait Time", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Same Day"},
                {"name": "1 Day"},
                {"name": "2 Days"},
                {"name": "3 Days"},
                {"name": "5 Days"},
                {"name": "1 Week"},
                {"name": "2 Weeks"}
            ]
        }},
        {"name": "Email Draft", "type": "multilineText", "options": {}},
        {"name": "Subject Line Variations", "type": "multilineText", "options": {}},
        {"name": "CTA Variations", "type": "multilineText", "options": {}},
        {"name": "Previous Response", "type": "multilineText", "options": {}},
        {"name": "Status", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Drafted"},
                {"name": "Ready to Send"},
                {"name": "Sent"},
                {"name": "Engaged"},
                {"name": "Completed"},
                {"name": "Stopped"}
            ]
        }},
        {"name": "Engagement Metrics", "type": "multilineText", "options": {}},
        {"name": "Last Sent Date", "type": "date", "options": {
            "dateFormat": {
                "format": "YYYY-MM-DD",
                "name": "iso"
            }
        }},
        {"name": "Next Send Date", "type": "date", "options": {
            "dateFormat": {
                "format": "YYYY-MM-DD",
                "name": "iso"
            }
        }}
    ],
    Tables.PAIN_POINTS: [
        {"name": "Industry", "type": "singleLineText", "options": {"formatting": {}}},
        {"name": "Pain Points", "type": "multilineText", "options": {"formatting": {}}},
        {"name": "Keywords", "type": "multilineText", "options": {"formatting": {}}},
        {"name": "Highlighted Quotes", "type": "multilineText", "options": {"formatting": {}}},
    ],
    Tables.OFFERS: [
        {"name": "Offer ID", "type": "singleLineText", "options": {}},
        {"name": "Offer Name", "type": "singleLineText", "options": {}},
        {"name": "Category", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Time & Attendance"},
                {"name": "Payroll & Billing"},
                {"name": "Candidate Management"},
                {"name": "Client Management"},
                {"name": "Compliance"},
                {"name": "Reporting"}
            ]
        }},
        {"name": "Description", "type": "multilineText", "options": {}},
        {"name": "Key Benefits", "type": "multilineText", "options": {}},
        {"name": "Industry Fit", "type": "multilineText", "options": {}},
        {"name": "Customization Options", "type": "multilineText", "options": {}},
        {"name": "Target Client Type", "type": "multipleSelects", "options": {
            "choices": [
                {"name": "Small Staffing"},
                {"name": "Mid-size Staffing"},
                {"name": "Enterprise Staffing"},
                {"name": "Healthcare Staffing"},
                {"name": "IT Staffing"},
                {"name": "Industrial Staffing"}
            ]
        }}
    ]
}

# Sample data for table initialization
SAMPLE_DATA = {
    Tables.LEADS: {
        "Lead ID": "L001",
        "Name": "John Doe",
        "Email": "john@example.com",
        "Company": "Example Corp",
        "Role": "CEO",
        "Lead Score": 85,
        "Lead Tier": "High"
    },
    Tables.CAMPAIGNS: {
        "Lead ID": "L001",
        "Campaign Name": "Enterprise Solution Introduction",
        "Campaign Tier": "High",
        "Sequence Position": 1,
        "Wait Time": "Same Day",
        "Email Draft": "Initial outreach email content...",
        "Subject Line Variations": "Streamline Your Operations\nBoost Your Efficiency",
        "CTA Variations": "Book a Demo\nSchedule a Call",
        "Previous Response": "",
        "Status": "Drafted",
        "Engagement Metrics": "Not started",
        "Last Sent Date": "2024-03-20",
        "Next Send Date": "2024-03-21"
    },
    Tables.PAIN_POINTS: {
        "Industry": "Technology",
        "Pain Points": "Integration challenges, scalability issues",
        "Keywords": "integration, scale, efficiency",
        "Highlighted Quotes": "Need better integration solutions"
    },
    Tables.OFFERS: {
        "Offer ID": "O001",
        "Offer Name": "Automated Timesheet Collection",
        "Category": "Time & Attendance",
        "Description": "Digital timesheet submission and approval system with mobile access",
        "Key Benefits": "- Eliminate manual data entry\n- Speed up approvals\n- Reduce billing errors\n- Real-time visibility",
        "Industry Fit": "Staffing & Recruiting, Professional Services",
        "Customization Options": "- Mobile app branding\n- Custom approval workflows\n- Integration options",
        "Target Client Type": ["Small Staffing", "Mid-size Staffing"]
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
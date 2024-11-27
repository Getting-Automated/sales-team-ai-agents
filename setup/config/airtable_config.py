# Base configuration
BASE_NAME = "AI Sales Agent Prospecting"
WORKSPACE_ID = "wspvmw70ZPF8XuEtI"

# Table names
class Tables:
    LEADS = "Leads"
    EVALUATIONS = "Lead Evaluations"
    PAIN_POINTS = "Pain Points"
    OFFERS = "Solution Offers"
    CAMPAIGNS = "Email Campaigns"

# Table structure
TABLE_SCHEMAS = {
    Tables.LEADS: [
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Company", "type": "singleLineText"},
        {"name": "Title", "type": "singleLineText"},
        {"name": "LinkedIn URL", "type": "url"},
        {"name": "Company LinkedIn", "type": "url"},
        {"name": "Raw Data", "type": "multilineText"}
    ],
    Tables.EVALUATIONS: [
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Individual Score", "type": "number", "options": {"precision": 1}},
        {"name": "Company Score", "type": "number", "options": {"precision": 1}},
        {"name": "Overall Score", "type": "number", "options": {"precision": 1}},
        {"name": "Decision Making Level", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Final Decision Maker"},
                {"name": "Key Influencer"},
                {"name": "Budget Holder"},
                {"name": "Individual Contributor"}
            ]
        }},
        {"name": "Department Match", "type": "multipleSelects", "options": {
            "choices": [
                {"name": "IT"},
                {"name": "Engineering"},
                {"name": "Operations"}
            ]
        }},
        {"name": "Industry Match", "type": "multipleSelects", "options": {
            "choices": [
                {"name": "Insurance"},
                {"name": "Employee Benefits"},
                {"name": "Insurance Broker"}
            ]
        }},
        {"name": "Technical Analysis", "type": "multilineText"},
        {"name": "Company Analysis", "type": "multilineText"},
        {"name": "Evaluation Summary", "type": "multilineText"}
    ],
    Tables.PAIN_POINTS: [
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Primary Pain Points", "type": "multilineText"},
        {"name": "Technical Challenges", "type": "multilineText"},
        {"name": "Operational Challenges", "type": "multilineText"},
        {"name": "Industry Specific Issues", "type": "multilineText"},
        {"name": "Analysis", "type": "multilineText"},
        {"name": "Priority Level", "type": "singleSelect", "options": {
            "choices": [
                {"name": "High"},
                {"name": "Medium"},
                {"name": "Low"}
            ]
        }}
    ],
    Tables.OFFERS: [
        {"name": "Lead ID", "type": "singleLineText"},
        {"name": "Solution Name", "type": "singleLineText"},
        {"name": "Value Proposition", "type": "multilineText"},
        {"name": "Key Benefits", "type": "multilineText"},
        {"name": "Technical Fit", "type": "multilineText"},
        {"name": "ROI Analysis", "type": "multilineText"},
        {"name": "Customization Notes", "type": "multilineText"}
    ],
    Tables.CAMPAIGNS: [
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

# Sample data for table initialization
SAMPLE_DATA = {
    Tables.LEADS: {
        "Lead ID": "L001",
        "Name": "John Doe",
        "Email": "john@example.com",
        "Company": "Example Corp",
        "Role": "CEO",
        "Lead Score": 85,
        "Lead Tier": "High",
        "Seniority": "C-Suite",
        "Departments": "Executive Leadership",
        "Location": "New York, NY, United States",
        "Company Size": 500,
        "Annual Revenue": "$50M-100M",
        "Technologies": "Salesforce, Workday, Oracle",
        "Keywords": "digital transformation, enterprise software",
        "Company Description": "Leading enterprise software company...",
        "Technical Fit Score": 8.5,
        "Technical Analysis": "Strong technical alignment with our stack...",
        "Pain Points": "Integration challenges, scalability needs",
        "Matching Criteria": "Company size, tech stack, industry",
        "Recommended Approach": "Focus on enterprise integration capabilities",
        "Next Steps": "Schedule technical demo",
        "Justification": "Perfect fit for our enterprise solution",
        "LinkedIn URL": "https://linkedin.com/in/johndoe",
        "Company LinkedIn": "https://linkedin.com/company/example-corp",
        "Company Website": "https://example.com",
        "Enriched Profile": "{\"additional_data\": \"full enriched profile json\"}"
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
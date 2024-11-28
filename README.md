# Sales Team AI Agents

An AI-powered sales automation system that leverages multiple AI agents to automate and enhance the sales process, with seamless Airtable integration for lead management.

## Overview

This project implements an advanced AI-driven sales automation system using CrewAI, a framework for orchestrating multiple AI agents. The system employs a hierarchical structure with a Sales Manager agent overseeing specialized task-specific agents, all working in coordination to automate and optimize the sales process.

> **Note**: The Pain Point Identification Agent and Email Campaign Development Agent are currently under development and will be fully implemented shortly. These additions will enhance the system's ability to identify customer pain points and create personalized email campaigns.

### Key Features

- **Multi-Agent System**: Utilizes specialized AI agents working in coordination
- **Lead Analysis**: Comprehensive evaluation of leads based on company and individual data
- **Pain Point Analysis**: Automated identification of potential customer pain points
- **Email Campaign Generation**: Customized email campaign content creation
- **Data Integration**: Seamless integration with Airtable for lead management
- **Multiple Data Sources**: Leverages various tools including ProxyCurl, Reddit, and company data APIs

## System Architecture

### CrewAI Integration

The system is built on CrewAI, which provides a robust framework for creating and managing AI agent crews. Key CrewAI components used include:

1. **Agents**: Each agent is a specialized AI entity with defined roles, goals, and backstories
2. **Tasks**: Structured units of work assigned to specific agents
3. **Process**: Sequential or parallel execution of tasks
4. **Tools**: Specialized capabilities provided to agents

### Agent Hierarchy

```mermaid
graph TD
    SM[Sales Manager Agent] --> DM[Data Manager Agent]
    SM --> DE[Data Enricher Agent]
    SM --> CE[Company Evaluator Agent]
    SM --> IE[Individual Evaluator Agent]
    SM --> PP[Pain Point Agent]
    SM --> EC[Email Campaign Agent]
    SM --> OR[Offer Researcher Creator Agent]
    
    subgraph Tools
        PT[ProxyCurl Tool]
        CDT[Company Data Tool]
        RT[Reddit Tool]
        AT[Airtable Tool]
        PLT[Perplexity Tool]
        OT[OpenAI Tool]
    end
    
    DE --> PT
    DM --> AT
    CE --> CDT
    CE --> PLT
    IE --> OT
    PP --> PLT
    PP --> OT
    EC --> OT
    OR --> PLT
    OR --> OT
```

### Agent Roles and Responsibilities

1. **Sales Manager Agent**
   - Role: Orchestrates the entire sales process
   - Responsibilities:
     - Task delegation and prioritization
     - Process monitoring and optimization
     - Resource allocation
     - Decision making based on agent outputs

2. **Data Manager Agent**
   - Role: Manages data storage and retrieval in Airtable
   - Key Tasks:
     - Lead record creation and updates
     - Data validation and integrity checks
     - Status tracking and updates
     - Relationship management between tables

3. **Data Enricher Agent**
   - Role: Enriches lead data with external information
   - Key Tasks:
     - LinkedIn profile data retrieval via ProxyCurl
     - Contact information validation
     - Company website data extraction
     - Data standardization and formatting

4. **Company Evaluator Agent**
   - Purpose: Analyzes company fit against ICP criteria
   - Key Tasks:
     - Industry match evaluation (25% weight)
     - Company size analysis (25% weight)
     - Location assessment (25% weight)
     - Growth stage evaluation (25% weight)
     - Market research via Perplexity
     - Technology stack analysis
     - Competitive landscape assessment

5. **Individual Evaluator Agent**
   - Purpose: Assesses individual leads against ICP criteria
   - Key Tasks:
     - Role match evaluation (30% weight)
     - Authority level assessment (30% weight)
     - Department alignment check (20% weight)
     - Skills and experience analysis (20% weight)
     - LinkedIn profile analysis
     - Decision-making influence evaluation

6. **Pain Point Agent** *(Coming Soon)*
   - Purpose: Identifies potential customer pain points
   - Status: Under development
   - Planned Tasks:
     - Industry pain point research
     - Company-specific challenge identification
     - Competitor pain point analysis
     - Market trend impact assessment
     - Reddit discussions analysis
     - News and social media monitoring

7. **Email Campaign Agent** *(Coming Soon)*
   - Purpose: Creates personalized email campaigns
   - Status: Under development
   - Planned Tasks:
     - Personalized content generation
     - Multi-step sequence creation
     - A/B testing variants
     - Wait time optimization
     - Pain point incorporation
     - Call-to-action optimization

8. **Offer Researcher Creator Agent**
   - Purpose: Matches and creates targeted offers
   - Key Tasks:
     - Offer-lead fit analysis
     - Fit score calculation
     - Best offer selection
     - Alternative offer identification
     - Personalization recommendations
     - Offer effectiveness analysis
     - Multi-lead offer optimization

Each agent utilizes specific tools and APIs:
- Company Evaluator: CompanyDataTool, PerplexityTool
- Individual Evaluator: OpenAITool
- Data Manager: AirtableTool
- Data Enricher: ProxycurlTool
- Offer Creator: AirtableTool, OpenAITool

### Process Types

The system supports multiple process types through CrewAI:

1. **Sequential Process**
   ```python
   crew.kickoff(
       process=Process.sequential
   )
   ```
   - Tasks are executed in a predetermined order
   - Each agent waits for previous tasks to complete
   - Ideal for dependent workflows (e.g., company analysis → pain point identification → offer creation)

2. **Hierarchical Process**
   ```python
   crew.kickoff(
       process=Process.hierarchical
   )
   ```
   - Manager agent delegates and oversees tasks
   - Parallel execution of independent tasks
   - Dynamic task prioritization

3. **Parallel Process**
   ```python
   crew.kickoff(
       process=Process.parallel
   )
   ```
   - Simultaneous execution of independent tasks
   - Faster processing for large lead volumes
   - Resource-efficient for independent analyses

### Data Flow

The system follows a sophisticated data flow process:

1. **Data Ingestion**
   ```python
   # Lead data is ingested and initially processed
   crew.inputs['leads'] = leads_data
   ```

2. **Data Enrichment**
   - Data Manager creates initial records
   - Data Enricher enhances profiles with:
     - LinkedIn data via ProxyCurl
     - Company information
     - Additional contact details

3. **Analysis Pipeline**
   - Company and Individual evaluation
   - Pain point identification
   - Offer creation
   - Email campaign generation

4. **Data Storage**
   - All processed data is stored in Airtable
   - Structured for easy retrieval and updates
   - Maintains relationships between different data points

## Setup

### Prerequisites
- Python 3.8+
- Airtable account with workspace creator permissions
- API access to various services (OpenAI, Perplexity, ProxyCurl, etc.)

### Environment Variables

The project requires several API keys to function. Create a `.env` file in the root directory with the following variables (you can copy from `.env.sample`):

```bash
# OpenAI API Key for GPT-4 and other OpenAI services
OPENAI_API_KEY=your_openai_api_key_here

# Perplexity API Key for web research
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Proxycurl API Key for LinkedIn profile data
PROXYCURL_API_KEY=your_proxycurl_api_key_here

# Airtable configuration
AI_AGENT_AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
```

> **Note**: Never commit your actual API keys to version control. The `.env` file is included in `.gitignore` to prevent accidental commits.

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd sales-team-ai-agents
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the System

1. Navigate to the project directory where the `pyproject.toml` is located:
```bash
cd sales-team-ai-agents
```

2. Run the CrewAI project:
```bash
crewai run
```

The system will automatically:
- Load environment variables
- Initialize the agent crew
- Process leads according to the configured workflow
- Store results in Airtable

### Processing Leads

The system processes leads from CSV files containing lead information. The CSV should include fields such as:
- First Name, Last Name
- Company
- LinkedIn URLs (Person and Company)
- Role/Title
- Industry
- Company Website
- Contact Information
- Company Details

## Airtable Integration

### Overview
The system uses Airtable as its primary data store, with a sophisticated schema designed for lead management and email campaign tracking. The integration is handled through automated setup scripts and a dedicated Airtable tool.

### Base Structure

The Airtable base "AI Sales Agent Prospecting" consists of two main tables:

1. **Leads Table**
   ```
   ├── Basic Lead Info
   │   ├── Lead ID (Text)
   │   ├── Name (Text)
   │   ├── Email (Email)
   │   ├── Company (Text)
   │   ├── Role (Text)
   │   ├── LinkedIn URL (URL)
   │   └── Company LinkedIn (URL)
   │
   ├── Evaluation Status
   │   ├── Individual Evaluation Status (Select)
   │   │   └── Options: Not Started, In Progress, Completed, Needs Review
   │   └── Company Evaluation Status (Select)
   │       └── Options: Not Started, In Progress, Completed, Needs Review
   │
   ├── Scoring Metrics
   │   ├── Individual Score (Number)
   │   ├── Company Score (Number)
   │   ├── Role Match Score (Number)
   │   ├── Authority Match Score (Number)
   │   ├── Department Match Score (Number)
   │   ├── Skills Match Score (Number)
   │   ├── Industry Match Score (Number)
   │   ├── Size Match Score (Number)
   │   └── Growth Match Score (Number)
   │
   └── Analysis Data
       ├── Individual Analysis (Long Text)
       ├── Company Analysis (Long Text)
       ├── Enriched Individual Data (Long Text)
       ├── Enriched Company Data (Long Text)
       ├── Raw Data (Long Text)
       └── Proxycurl Result (Long Text)
   ```

2. **Email Campaigns Table**
   ```
   ├── Campaign Info
   │   ├── Lead ID (Text)
   │   ├── Email Subject (Text)
   │   ├── Email Body (Long Text)
   │   └── Sequence Number (Number)
   │
   └── Campaign Details
       ├── Wait Days (Number)
       ├── Personalization Notes (Long Text)
       ├── Pain Points Addressed (Long Text)
       └── Call To Action (Text)
   ```

### Setup and Configuration

1. **Initial Setup**
   ```bash
   # Initialize Airtable base with schema
   python setup/airtable_initialization.py
   
   # Force recreation of base
   python setup/airtable_initialization.py --force
   ```

2. **Environment Variables**
   ```env
   AI_AGENT_AIRTABLE_API_KEY=your_api_key
   AIRTABLE_BASE_ID=your_base_id
   AIRTABLE_WORKSPACE_ID=your_workspace_id
   ```

3. **Schema Management**
   - The schema is defined in `setup/config/airtable_config.py`
   - Includes table definitions, field types, and select options
   - Automated schema updates via initialization script

### Data Flow

1. **Lead Creation**
   ```python
   # Example of lead data structure
   lead_data = {
       "Lead ID": "L001",
       "Name": "John Doe",
       "Email": "john.doe@example.com",
       "Company": "Example Corp",
       "Individual Evaluation Status": "Not Started",
       "Company Evaluation Status": "Not Started"
   }
   ```

2. **Status Tracking**
   - Individual and Company evaluation statuses
   - Color-coded status indicators:
     - Not Started: Red
     - In Progress: Yellow
     - Completed: Green
     - Needs Review: Orange

3. **Scoring System**
   - Numerical scores (0-10) for various metrics
   - Automated calculation based on agent evaluations
   - Tier classification (High/Medium/Low) based on aggregate scores

### Integration with Agents

The Data Manager Agent interacts with Airtable through the AirtableTool, which provides:
- Record creation and updates
- Data validation
- Status management
- Score calculations
- Campaign tracking

```python
# Example of agent interaction with Airtable
from getting_automated_sales_ai_agent.tools import AirtableTool

airtable_tool = AirtableTool(llm=self.llm)
result = airtable_tool.create_or_update_lead(
    lead_data,
    evaluation_status="In Progress"
)
```

## Configuration

### Using the Configuration Manager UI

The project includes a user-friendly web-based configuration manager that helps you set up and manage your sales AI agent configuration without having to edit YAML files directly. You can find it at:

```
getting_automated_sales_ai_agent/src/getting_automated_sales_ai_agent/ui/templates/config_manager.html
```

Key features of the Configuration Manager:

1. **Visual Configuration**: Intuitive interface for setting up:
   - Target company parameters (size, industry, business model)
   - Target individual parameters (roles, seniority)
   - Agent scoring weights
   - Lead scoring thresholds

2. **Interactive Scoring**: Real-time preview of how your configuration affects lead scoring

3. **Templates**: Pre-built templates for common use cases

4. **Validation**: Built-in validation to ensure your configuration is valid

5. **Export**: Automatically generates properly formatted configuration files

To use the Configuration Manager:

1. Open the `config_manager.html` file in your web browser
2. Adjust the parameters according to your needs
3. Click "Save Configuration" to generate the configuration file
4. The configuration will be saved in the proper format and location

This tool significantly simplifies the configuration process and helps prevent syntax errors that might occur when editing YAML files manually.

### YAML Configuration Files

The system uses YAML configuration files located in the config directory:
- `agents.yaml`: Defines agent roles, goals, and behaviors
- `config.yaml`: Contains ICP (Ideal Customer Profile) configuration

## Directory Structure

```
sales-team-ai-agents/
├── getting_automated_sales_ai_agent/
│   └── src/
│       └── getting_automated_sales_ai_agent/
│           ├── agents/
│           │   ├── company_evaluator.py
│           │   ├── email_campaign_agent.py
│           │   ├── individual_evaluator.py
│           │   ├── offer_researcher_creator_agent.py
│           │   └── pain_point_agent.py
│           ├── tools/
│           ├── config/
│           ├── main.py
│           └── crew.py
└── setup/
    └── config/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Specify your license here]

## Support

For support, please [specify contact method or raise an issue in the repository].
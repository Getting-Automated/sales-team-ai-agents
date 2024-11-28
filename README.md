# Sales Team AI Agents

An AI-powered sales automation system that leverages multiple AI agents to automate and enhance the sales process, with seamless Airtable integration for lead management.

## Overview

This project implements an advanced AI-driven sales automation system using CrewAI, a framework for orchestrating multiple AI agents. The system employs a hierarchical structure with a Sales Manager agent overseeing specialized task-specific agents, all working in coordination to automate and optimize the sales process.

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
   - Role: Manages data storage and retrieval
   - Key Tasks:
     - Lead data storage in Airtable
     - Data validation and cleaning
     - Record updates and maintenance
     - Data synchronization across tools

3. **Data Enricher Agent**
   - Role: Enriches lead data with additional information
   - Key Tasks:
     - LinkedIn profile data retrieval
     - Company information enrichment
     - Contact information validation
     - Data standardization

4. **Company Evaluator Agent**
   - Purpose: Analyzes company profiles for market fit
   - Key Tasks:
     - Company data enrichment
     - Industry analysis
     - Market fit scoring
     - Technology stack evaluation

5. **Individual Evaluator Agent**
   - Purpose: Assesses individual lead characteristics
   - Key Tasks:
     - Professional background analysis
     - Role relevance evaluation
     - Decision-making authority assessment
     - Communication preference analysis

6. **Pain Point Agent**
   - Purpose: Identifies potential customer pain points
   - Key Tasks:
     - Industry research
     - Competitor analysis
     - Market trend analysis
     - Pain point prioritization

7. **Email Campaign Agent**
   - Purpose: Creates personalized email campaigns
   - Key Tasks:
     - Content generation
     - Personalization
     - A/B testing suggestions
     - Campaign sequencing

8. **Offer Researcher Creator Agent**
   - Purpose: Develops targeted solutions and offers
   - Key Tasks:
     - Solution research
     - Pricing analysis
     - Proposal generation
     - Value proposition creation

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
Create a `.env` file in the root directory with the following:

```env
AIRTABLE_API_KEY=your_personal_access_token
AIRTABLE_BASE_ID=your_base_id
OPENAI_API_KEY=your_openai_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
PROXYCURL_API_KEY=your_proxycurl_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

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

### Processing Leads

The system can process leads from CSV files containing lead information. The CSV should include fields such as:
- First Name, Last Name
- Company
- LinkedIn URLs (Person and Company)
- Role/Title
- Industry
- Company Website
- Contact Information
- Company Details

### Running the System

```python
from getting_automated_sales_ai_agent.crew import GettingAutomatedSalesAiAgent

# Initialize the crew
crew = GettingAutomatedSalesAiAgent()

# Process leads
crew.inputs['leads'] = your_leads_data
result = crew.run()
```

## Configuration

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
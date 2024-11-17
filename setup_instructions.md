### **Overview**

We'll cover:

1. **Setting Up and Configuring Each Tool**
   - Proxycurl API
   - Company Data API (e.g., Clearbit API)
   - OpenAI API
   - Google News API
   - Reddit API
   - Airtable

2. **Implementing Each Agent's Logic**
   - CustomerICPAgent
   - PainPointIdentificationAgent
   - SolutionTemplatesAgent
   - OfferResearcherCreatorAgent

3. **Securing API Keys and Sensitive Information**

4. **Structuring Your Project Repository**

5. **Installing Necessary Dependencies**

6. **Testing and Debugging**

---

### **1. Setting Up and Configuring Each Tool**

#### **a. Proxycurl API**

- **Purpose**: Retrieves LinkedIn profile data of individuals.
- **Setup Steps**:
  1. **Sign Up**: Create an account at [Proxycurl](https://nubela.co/proxycurl).
  2. **Get API Key**: Obtain your API key from your account dashboard.
  3. **Read Documentation**: Familiarize yourself with the [Proxycurl API documentation](https://nubela.co/proxycurl/docs).
- **Python Usage**:
  - Use the `requests` library to interact with the API.

#### **b. Company Data API (e.g., Clearbit API)**

- **Purpose**: Retrieves company data such as industry, size, and revenue.
- **Setup Steps**:
  1. **Choose an API Provider**: Options include [Clearbit](https://clearbit.com/), [ZoomInfo](https://www.zoominfo.com/), or [Crunchbase](https://about.crunchbase.com/).
  2. **Sign Up**: Create an account with the chosen provider.
  3. **Get API Key**: Obtain your API key.
  4. **Read Documentation**: Understand how to use their API.
- **Python Usage**:
  - Use the `requests` library or any provided SDK.

#### **c. OpenAI API**

- **Purpose**: Performs NLP tasks and content generation.
- **Setup Steps**:
  1. **Sign Up**: Create an account at [OpenAI](https://platform.openai.com/).
  2. **Get API Key**: Generate an API key from your account settings.
  3. **Install SDK**: Install the OpenAI Python library.

     ```bash
     pip install openai
     ```

  4. **Read Documentation**: Familiarize yourself with the [OpenAI API docs](https://platform.openai.com/docs/).
- **Python Usage**:
  - Use the `openai` library to interact with the API.

#### **d. Google News API**

- **Purpose**: Retrieves recent industry news articles.
- **Setup Steps**:
  1. **Choose an API Provider**: Since Google doesn't offer a public News API, you can use [NewsAPI.org](https://newsapi.org/).
  2. **Sign Up**: Create an account at NewsAPI.org.
  3. **Get API Key**: Obtain your API key.
  4. **Read Documentation**: Understand how to use their API.
- **Python Usage**:
  - Use the `requests` library to make API calls.

#### **e. Reddit API**

- **Purpose**: Captures relevant discussions from Reddit.
- **Setup Steps**:
  1. **Create Reddit Account**: If you don't have one already.
  2. **Create an App**: Go to [Reddit Apps](https://www.reddit.com/prefs/apps) and create a new app to get `client_id` and `client_secret`.
  3. **Install PRAW**: Install the Python Reddit API Wrapper.

     ```bash
     pip install praw
     ```

  4. **Read Documentation**: Familiarize yourself with [PRAW documentation](https://praw.readthedocs.io/en/latest/).
- **Python Usage**:
  - Use the `praw` library to interact with Reddit.

#### **f. Airtable**

- **Purpose**: Centralized data storage and management.
- **Setup Steps**:
  1. **Sign Up**: Create an account at [Airtable](https://airtable.com/).
  2. **Create Base and Tables**: Set up your base with the required tables and fields as per your configuration.
  3. **Get API Key**: Obtain your API key from your account settings.
  4. **Install PyAirtable**: Install the Airtable Python client.

     ```bash
     pip install pyairtable
     ```

  5. **Read Documentation**: Familiarize yourself with the [PyAirtable documentation](https://pyairtable.readthedocs.io/en/latest/).

---

### **2. Implementing Each Agent's Logic**

#### **a. CustomerICPAgent**

- **Files**: `agents/customer_icp_agent.py`
- **Responsibilities**:
  - Retrieve individual LinkedIn profile data using Proxycurl API.
  - Retrieve company data using the Company Data API.
  - Analyze profiles using OpenAI API.
  - Score leads and store data in Airtable.

**Sample Code**:

```python
# agents/customer_icp_agent.py

import os
import json
import requests
import openai
from pyairtable import Table

# Load API keys from environment variables
PROXYCURL_API_KEY = os.getenv('PROXYCURL_API_KEY')
COMPANY_DATA_API_KEY = os.getenv('COMPANY_DATA_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

def get_linkedin_profile(linkedin_url):
    headers = {'Authorization': f'Bearer {PROXYCURL_API_KEY}'}
    params = {'url': linkedin_url}
    response = requests.get('https://api.proxycurl.com/v2/linkedin', headers=headers, params=params)
    return response.json()

def get_company_data(domain):
    headers = {'Authorization': f'Bearer {COMPANY_DATA_API_KEY}'}
    response = requests.get(f'https://company.clearbit.com/v2/companies/find?domain={domain}', headers=headers)
    return response.json()

def analyze_profiles(individual_profile, company_profile):
    prompt = f"""
    Evaluate the following individual and company for fit with our Ideal Customer Profile.

    Individual Profile:
    {json.dumps(individual_profile, indent=2)}

    Company Profile:
    {json.dumps(company_profile, indent=2)}

    Provide a lead score between 0 and 100 and assign a tier (High, Medium, Low).
    Respond in JSON format: {{"lead_score": ..., "lead_tier": "..."}}
    """
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=150,
        temperature=0.5,
    )
    result_text = response.choices[0].text.strip()
    return json.loads(result_text)

def store_lead_data(lead_data):
    leads_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'LeadsTable')
    leads_table.create(lead_data)

def main(linkedin_url):
    # Get individual profile
    individual_profile = get_linkedin_profile(linkedin_url)
    # Extract company domain
    company_domain = individual_profile.get('company', {}).get('website')
    if not company_domain:
        print("Company domain not found.")
        return
    # Get company data
    company_profile = get_company_data(company_domain)
    # Analyze profiles
    analysis = analyze_profiles(individual_profile, company_profile)
    # Prepare data for Airtable
    lead_data = {
        'Name': individual_profile.get('full_name'),
        'Email': individual_profile.get('email'),
        'Company': individual_profile.get('company', {}).get('name'),
        'Role': individual_profile.get('occupation'),
        'LeadScore': analysis.get('lead_score'),
        'LeadTier': analysis.get('lead_tier'),
        'EnrichedIndividualProfile': json.dumps(individual_profile),
        'EnrichedCompanyProfile': json.dumps(company_profile),
    }
    # Store data in Airtable
    store_lead_data(lead_data)
    print("Lead data stored successfully.")

if __name__ == '__main__':
    linkedin_url = 'https://www.linkedin.com/in/example-profile/'
    main(linkedin_url)
```

**Notes**:

- Replace `'https://www.linkedin.com/in/example-profile/'` with the actual LinkedIn URL.
- Handle exceptions and errors appropriately.

#### **b. PainPointIdentificationAgent**

- **Files**: `agents/pain_point_identification_agent.py`
- **Responsibilities**:
  - Retrieve industry news articles via Google News API.
  - Retrieve Reddit discussions using Reddit API.
  - Use OpenAI API for NLP tasks.
  - Store pain points in Airtable.

**Sample Code**:

```python
# agents/pain_point_identification_agent.py

import os
import json
import requests
import openai
from pyairtable import Table
import praw

# Load API keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

# Initialize Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def get_news_articles(industry_keywords):
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': industry_keywords,
        'apiKey': NEWS_API_KEY,
        'language': 'en',
        'sortBy': 'relevancy',
        'pageSize': 20
    }
    response = requests.get(url, params=params)
    articles = response.json().get('articles', [])
    return articles

def get_reddit_posts(subreddit_list, industry_keywords):
    posts = []
    for subreddit in subreddit_list:
        subreddit_obj = reddit.subreddit(subreddit)
        for submission in subreddit_obj.search(industry_keywords, limit=10):
            posts.append({
                'title': submission.title,
                'selftext': submission.selftext,
                'url': submission.url
            })
    return posts

def extract_pain_points(texts):
    combined_text = '\n\n'.join(texts)
    prompt = f"""
    Analyze the following text and extract the main pain points, keywords, and any significant quotes.

    Text:
    {combined_text}

    Respond in JSON format: {{"summary": "...", "keywords": [...], "quotes": [...]}}
    """
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=500,
        temperature=0.5,
    )
    result_text = response.choices[0].text.strip()
    return json.loads(result_text)

def store_pain_points(pain_points_data, industry):
    pain_points_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'PainPointsTable')
    record = {
        'Industry': industry,
        'PainPoints': pain_points_data.get('summary'),
        'Keywords': ', '.join(pain_points_data.get('keywords', [])),
        'HighlightedQuotes': '\n'.join(pain_points_data.get('quotes', [])),
    }
    pain_points_table.create(record)

def main(industry_keywords):
    # Get news articles
    articles = get_news_articles(industry_keywords)
    article_texts = [article.get('content') or article.get('description', '') for article in articles]
    # Get Reddit posts
    subreddit_list = ['industry_subreddit1', 'industry_subreddit2']  # Replace with actual subreddit names
    reddit_posts = get_reddit_posts(subreddit_list, industry_keywords)
    reddit_texts = [post['title'] + '\n' + post['selftext'] for post in reddit_posts]
    # Combine texts
    all_texts = article_texts + reddit_texts
    # Extract pain points
    pain_points_data = extract_pain_points(all_texts)
    # Store in Airtable
    store_pain_points(pain_points_data, industry_keywords)
    print("Pain points stored successfully.")

if __name__ == '__main__':
    industry_keywords = 'your industry keywords'  # Replace with actual keywords
    main(industry_keywords)
```

**Notes**:

- Replace `'your industry keywords'` with the actual industry keywords.
- Replace `['industry_subreddit1', 'industry_subreddit2']` with relevant subreddit names.
- Handle exceptions and errors appropriately.

#### **c. SolutionTemplatesAgent**

- **Files**: `agents/solution_templates_agent.py`
- **Responsibilities**:
  - Access solution templates from Airtable.
  - Adapt templates using identified pain points and keywords.
  - Store customized templates in Airtable.

**Sample Code**:

```python
# agents/solution_templates_agent.py

import os
import openai
from pyairtable import Table

# Load API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

def get_templates():
    templates_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'SolutionTemplatesTable')
    return templates_table.all()

def get_pain_points():
    pain_points_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'PainPointsTable')
    return pain_points_table.all()

def customize_template(template, pain_points, keywords):
    prompt = f"""
    Customize the following solution template to address the pain points and include the keywords.

    Template:
    {template}

    Pain Points:
    {pain_points}

    Keywords:
    {', '.join(keywords)}

    Provide the customized solution.
    """
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=500,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

def store_customized_template(template_id, customized_template):
    templates_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'SolutionTemplatesTable')
    templates_table.update(template_id, {'CustomizedTemplate': customized_template})

def main():
    templates = get_templates()
    pain_points_records = get_pain_points()
    if not pain_points_records:
        print("No pain points available.")
        return
    # Assuming we take the latest pain points record
    latest_pain_points = pain_points_records[-1]['fields']
    pain_points = latest_pain_points.get('PainPoints', '')
    keywords = latest_pain_points.get('Keywords', '').split(', ')

    for record in templates:
        template_id = record['id']
        template_content = record['fields'].get('Description', '')
        customized_template = customize_template(template_content, pain_points, keywords)
        store_customized_template(template_id, customized_template)
    print("Templates customized successfully.")

if __name__ == '__main__':
    main()
```

**Notes**:

- Ensure that the `SolutionTemplatesTable` in Airtable has a field named `CustomizedTemplate`.
- Handle exceptions and errors appropriately.

#### **d. OfferResearcherCreatorAgent**

- **Files**: `agents/offer_researcher_creator_agent.py`
- **Responsibilities**:
  - Combine pain points, solution templates, and enriched profiles.
  - Generate personalized offers and email drafts using OpenAI API.
  - Store results in Airtable.

**Sample Code**:

```python
# agents/offer_researcher_creator_agent.py

import os
import json
import openai
from pyairtable import Table

# Load API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

def get_leads():
    leads_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'LeadsTable')
    return leads_table.all()

def get_customized_templates():
    templates_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'SolutionTemplatesTable')
    return templates_table.all()

def create_offer(lead_profile, company_profile, customized_template):
    prompt = f"""
    Using the following lead and company profiles, along with the customized solution template, create a personalized offer document and email draft.

    Lead Profile:
    {json.dumps(lead_profile, indent=2)}

    Company Profile:
    {json.dumps(company_profile, indent=2)}

    Customized Solution Template:
    {customized_template}

    Respond in JSON format: {{"offer_document": "...", "email_draft": "...", "offer_highlights": "..."}}
    """
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=1000,
        temperature=0.5,
    )
    result_text = response.choices[0].text.strip()
    return json.loads(result_text)

def store_offer(lead_id, offer_data):
    offers_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, 'OffersTable')
    record = {
        'LeadID': lead_id,
        'OfferDocument': offer_data.get('offer_document'),
        'EmailDrafts': offer_data.get('email_draft'),
        'OfferHighlights': offer_data.get('offer_highlights'),
        'Status': 'Drafted'
    }
    offers_table.create(record)

def main():
    leads = get_leads()
    templates = get_customized_templates()
    if not templates:
        print("No customized templates available.")
        return
    customized_template = templates[0]['fields'].get('CustomizedTemplate', '')

    for lead in leads:
        lead_id = lead['id']
        lead_fields = lead['fields']
        enriched_individual_profile = json.loads(lead_fields.get('EnrichedIndividualProfile', '{}'))
        enriched_company_profile = json.loads(lead_fields.get('EnrichedCompanyProfile', '{}'))

        offer_data = create_offer(enriched_individual_profile, enriched_company_profile, customized_template)
        store_offer(lead_id, offer_data)
    print("Offers created and stored successfully.")

if __name__ == '__main__':
    main()
```

**Notes**:

- Ensure that the `OffersTable` in Airtable has fields matching those used in the `record` dictionary.
- Handle exceptions and errors appropriately.

---

### **3. Securing API Keys and Sensitive Information**

- **Use Environment Variables**: Store API keys in environment variables.
  - On Unix/Linux/MacOS:

    ```bash
    export PROXYCURL_API_KEY='your_proxycurl_api_key'
    export COMPANY_DATA_API_KEY='your_company_data_api_key'
    # ... and so on for all API keys
    ```

- **Use a `.env` File**: Create a `.env` file to store API keys (don't commit this file to version control).

  ```ini
  # .env
  PROXYCURL_API_KEY=your_proxycurl_api_key
  COMPANY_DATA_API_KEY=your_company_data_api_key
  OPENAI_API_KEY=your_openai_api_key
  AIRTABLE_API_KEY=your_airtable_api_key
  AIRTABLE_BASE_ID=your_airtable_base_id
  NEWS_API_KEY=your_news_api_key
  REDDIT_CLIENT_ID=your_reddit_client_id
  REDDIT_CLIENT_SECRET=your_reddit_client_secret
  REDDIT_USER_AGENT=your_app_name
  ```

- **Load Environment Variables in Python**:

  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```

- **Add `.env` to `.gitignore`**:

  ```ini
  # .gitignore
  .env
  ```

---

### **4. Structuring Your Project Repository**

Your project directory should look like this:

```
your-project/
├── crew.yaml
├── agents/
│   ├── customer_icp_agent.py
│   ├── pain_point_identification_agent.py
│   ├── solution_templates_agent.py
│   └── offer_researcher_creator_agent.py
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

- **`crew.yaml`**: Your main configuration file.
- **`agents/`**: Contains Python scripts for each agent.
- **`.env`**: Contains your environment variables (API keys).
- **`.gitignore`**: Lists files and directories to be ignored by Git.
- **`requirements.txt`**: Lists Python dependencies.

---

### **5. Installing Necessary Dependencies**

Create a `requirements.txt` file:

```
openai
pyairtable
requests
praw
python-dotenv
```

Install dependencies using:

```bash
pip install -r requirements.txt
```

---

### **6. Testing and Debugging**

- **Test Each Agent Individually**: Run each script separately to ensure they work as expected.
- **Handle Exceptions**: Use try-except blocks to catch and handle exceptions.
- **Logging**: Implement logging to track the flow and catch issues.
- **API Rate Limits**: Be mindful of rate limits and implement retries if necessary.
- **Data Validation**: Ensure the data you retrieve and store is valid and properly formatted.

---

### **Additional Considerations**

- **Data Privacy and Compliance**:
  - Ensure compliance with data protection regulations (e.g., GDPR).
  - Be cautious when handling personal data.

- **OpenAI Usage Policies**:
  - Review and comply with [OpenAI's policies](https://platform.openai.com/docs/usage-policies).
  - Avoid disallowed content and ensure ethical use.

- **Scalability**:
  - Design your code to handle scaling (e.g., batching API calls).
  - Monitor performance and optimize where necessary.

---

### **Conclusion**

By setting up each tool and implementing the agent logic as outlined, you'll have a fully functional system that:

- Analyzes leads and companies.
- Identifies industry pain points.
- Generates customized solution templates.
- Creates personalized offers and email drafts.
- Stores all data centrally in Airtable for easy access and management.

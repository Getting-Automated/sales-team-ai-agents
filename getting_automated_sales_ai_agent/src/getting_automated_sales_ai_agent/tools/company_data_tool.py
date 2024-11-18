# tools/company_data_tool.py

from crewai.tools import BaseTool
from pydantic import Field, BaseModel
from typing import Any, Type
import requests
from bs4 import BeautifulSoup
import tldextract
import time
from urllib.parse import urljoin, urlparse
import json
from urllib.robotparser import RobotFileParser

class CompanyDataToolArgs(BaseModel):
    domain: str = Field(description="The domain to crawl")

class CompanyDataTool(BaseTool):
    name: str = "company_data_tool"
    description: str = "Crawls the company's website to extract relevant information."
    llm: Any = Field(description="LLM instance to use for text analysis")
    args_schema: Type[BaseModel] = CompanyDataToolArgs

    visited_urls: set = Field(default_factory=set)
    max_depth: int = 2
    max_pages: int = 20
    headers: dict = Field(default_factory=lambda: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 '
                      'Safari/604.1'
    })

    class Config:
        arbitrary_types_allowed = True

    def _run(self, domain: str) -> dict:
        """Fetch and analyze company data from the company's website."""
        # Validate domain
        if not domain:
            return {"error": "No domain provided."}

        # Prepare base URL
        domain_info = tldextract.extract(domain)
        if not domain_info.domain:
            return {"error": "Invalid domain provided."}

        base_url = f"https://{domain_info.domain}.{domain_info.suffix}"

        # Check robots.txt
        if not self.is_allowed_by_robots(base_url):
            return {"error": f"Crawling is disallowed by robots.txt for {base_url}"}

        # Start crawling from the base URL
        self.visited_urls = set()
        extracted_texts = []
        self.crawl_site(base_url, base_url, 0, extracted_texts)

        if not extracted_texts:
            return {"error": "No content extracted from the website."}

        # Combine all extracted texts
        combined_text = ' '.join(extracted_texts)

        # Use the LLM to extract structured company data
        company_data = self.extract_company_data_with_llm(combined_text)

        return company_data

    def is_allowed_by_robots(self, base_url):
        """Check if crawling is allowed by robots.txt."""
        robots_url = urljoin(base_url, '/robots.txt')
        try:
            response = requests.get(robots_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                robots_txt = response.text
                rp = RobotFileParser()
                rp.parse(robots_txt.splitlines())
                # Check if the user agent is allowed
                return rp.can_fetch(self.headers['User-Agent'], base_url)
            # If robots.txt is not found, assume allowed
            return True
        except requests.exceptions.RequestException:
            # Assume allowed if robots.txt is not accessible
            return True

    def crawl_site(self, base_url, current_url, depth, extracted_texts):
        """Recursively crawl the site to a certain depth."""
        if depth > self.max_depth or len(self.visited_urls) >= self.max_pages:
            return

        try:
            response = requests.get(current_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return

            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            extracted_texts.append(text)

            self.visited_urls.add(current_url)

            # Find all internal links
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                full_url = urljoin(base_url, href)
                parsed_url = urlparse(full_url)

                # Check if the link is within the same domain
                if parsed_url.netloc != urlparse(base_url).netloc:
                    continue

                # Avoid re-visiting URLs
                if full_url in self.visited_urls:
                    continue

                # Only crawl HTTP and HTTPS URLs
                if parsed_url.scheme not in ['http', 'https']:
                    continue

                # Politeness delay
                time.sleep(1)

                # Recursively crawl the next page
                self.crawl_site(base_url, full_url, depth + 1, extracted_texts)

                if len(self.visited_urls) >= self.max_pages:
                    break

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to fetch {current_url}: {e}")
            return

    def extract_company_data_with_llm(self, text_content):
        """Use the LLM to extract structured company data from text content."""
        # Prepare the prompt
        prompt = f"""
As an AI language model, you are tasked with extracting key company information from the following text:

{text_content}

Extract the following information if available:
- Company Name
- Industry
- Description
- Products and Services
- Technologies Used
- Company Size (number of employees)
- Headquarters Location
- Mission and Vision
- Key Clients or Partners

Provide the extracted information in JSON format, including only the fields you can find:

{{
    "company_name": "...",
    "industry": "...",
    "description": "...",
    "products_and_services": ["..."],
    "technologies_used": ["..."],
    "company_size": "...",
    "headquarters_location": "...",
    "mission": "...",
    "vision": "...",
    "key_clients_or_partners": ["..."]
}}
"""
        # Use the LLM to process the prompt
        try:
            llm_response = self.llm.complete(prompt)
            # Parse the JSON output
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            company_data_json = llm_response[json_start:json_end]
            company_data = json.loads(company_data_json)
            return company_data
        except Exception as e:
            self.logger.error(f"LLM processing error: {e}")
            return {"error": f"LLM processing error: {e}"}

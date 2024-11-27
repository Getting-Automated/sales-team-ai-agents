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
from openai import OpenAI

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
    client: OpenAI = Field(default_factory=lambda: OpenAI())

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self, domain: str) -> dict:
        """Fetch and analyze company data from the company's website."""
        print(f"Starting analysis of domain: {domain}")
        
        try:
            # Clean up domain if it's a full URL
            if domain.startswith(('http://', 'https://')):
                parsed = urlparse(domain)
                domain = parsed.netloc or parsed.path
            
            # Validate domain
            if not domain:
                print("Error: No domain provided")
                return {"error": "No domain provided."}

            # Prepare base URL
            domain_info = tldextract.extract(domain)
            if not domain_info.domain:
                print("Error: Invalid domain provided")
                return {"error": "Invalid domain provided."}

            base_url = f"https://{domain_info.domain}.{domain_info.suffix}"
            print(f"Base URL: {base_url}")

            # Check robots.txt
            if not self.is_allowed_by_robots(base_url):
                print(f"Warning: Crawling is disallowed by robots.txt for {base_url}")
                return {"error": f"Crawling is disallowed by robots.txt for {base_url}"}

            # Reset visited URLs for this domain
            self.visited_urls = set()
            extracted_texts = []
            
            # Start with the homepage
            response = requests.get(base_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return {"error": f"Failed to access homepage: {response.status_code}"}

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get homepage content
            extracted_texts = [soup.get_text(separator=' ', strip=True)]
            print("Extracted homepage content")

            # Get important links to crawl
            important_urls = self.get_important_links(soup, base_url)
            print(f"Selected {len(important_urls)} important pages to analyze")

            # Crawl selected pages
            for url in important_urls:
                try:
                    print(f"Analyzing important page: {url}")
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        extracted_texts.append(text)
                        print(f"Successfully extracted content from {url}")
                    time.sleep(1)  # Politeness delay
                except Exception as e:
                    print(f"Error fetching {url}: {str(e)}")
                    continue

            if not extracted_texts:
                return {"error": "No content extracted from the website"}

            # Combine all extracted texts
            combined_text = ' '.join(extracted_texts)
            print(f"Extracted content from {len(extracted_texts)} pages")

            # Use the LLM to extract structured company data
            company_data = self.extract_company_data_with_llm(combined_text)
            print("Completed company data extraction")

            return company_data
            
        except Exception as e:
            print(f"Error analyzing domain {domain}: {str(e)}")
            return {"error": f"Analysis error: {str(e)}"}

    def is_allowed_by_robots(self, base_url):
        """Check if crawling is allowed by robots.txt."""
        robots_url = urljoin(base_url, '/robots.txt')
        try:
            response = requests.get(robots_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                robots_txt = response.text
                rp = RobotFileParser()
                rp.parse(robots_txt.splitlines())
                return rp.can_fetch(self.headers['User-Agent'], base_url)
            return True
        except requests.exceptions.RequestException:
            print(f"Warning: Could not access robots.txt for {base_url}")
            return True

    def extract_company_data_with_llm(self, text_content):
        """Use OpenAI directly to extract structured company data."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # or your preferred model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction specialist. Extract company information in JSON format."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Extract key company information from this text in JSON format:

                        {text_content}

                        Return ONLY a valid JSON object with these fields (if found):
                        - company_name
                        - industry
                        - description
                        - products_and_services (as array)
                        - technologies_used (as array)
                        - company_size
                        - headquarters_location
                        - mission
                        - vision
                        - key_clients_or_partners (as array)
                        """
                    }
                ],
                response_format={ "type": "json_object" }  # Ensure JSON response
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error processing with OpenAI: {str(e)}")
            return {"error": f"OpenAI processing error: {str(e)}"}

    def get_important_links(self, soup, base_url):
        """Use OpenAI directly to identify important links."""
        try:
            # Get all links and their surrounding text
            link_data = []
            all_links = soup.find_all('a', href=True)
            print(f"\nFound {len(all_links)} total links on the page")
            
            for link in all_links:
                href = link.get('href', '')
                full_url = urljoin(base_url, href)
                
                # Skip external links and non-http(s) links
                parsed_url = urlparse(full_url)
                if (parsed_url.netloc != urlparse(base_url).netloc or
                    parsed_url.scheme not in ['http', 'https']):
                    continue
                
                # Get context around the link
                context = link.get_text(strip=True)
                parent_text = link.parent.get_text(strip=True)[:200]
                
                if context:  # Only add links with visible text
                    link_data.append({
                        "url": full_url,
                        "text": context,
                        "context": parent_text
                    })
                    print(f"Found link: {context} -> {full_url}")

            print(f"\nFiltered to {len(link_data)} internal links with text")

            if not link_data:
                print("No valid links found for analysis")
                return []

            print("\nSending links to OpenAI for analysis...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at identifying valuable company information pages.
                        Select the most important links that are likely to contain key company information.
                        Focus on pages like: About Us, Products/Services, Company Info, Leadership, Contact."""
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Analyze these links from {base_url} and return a JSON object with an array of the most important URLs
                        that would contain valuable company information. Consider the link text and surrounding context.
                        
                        Link data:
                        {json.dumps(link_data, indent=2)}
                        
                        Return format:
                        {{
                            "urls": ["url1", "url2", "url3", "url4", "url5"]
                        }}
                        
                        Include any URLs that might contain company
                        """
                    }
                ],
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("urls", [])  # Expect a JSON object with "urls" array

        except Exception as e:
            print(f"Error selecting important links: {str(e)}")
            return []

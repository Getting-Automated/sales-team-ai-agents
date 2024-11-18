# tools/proxycurl_tool.py

from crewai.tools import BaseTool
import os
import requests
from typing import Dict, Any, Optional
from pydantic import Field, BaseModel

class ProxycurlParams(BaseModel):
    linkedin_profile_url: Optional[str] = None
    twitter_profile_url: Optional[str] = None
    facebook_profile_url: Optional[str] = None
    extra: str = "include"
    github_profile_id: str = "exclude"
    facebook_profile_id: str = "exclude"
    twitter_profile_id: str = "exclude"
    personal_contact_number: str = "exclude"
    personal_email: str = "exclude"
    inferred_salary: str = "exclude"
    skills: str = "include"
    use_cache: str = "if-present"
    fallback_to_cache: str = "on-error"

    class Config:
        extra = "allow"

class ProxycurlTool(BaseTool):
    """Tool for retrieving LinkedIn profile data using Proxycurl API."""
    
    name: str = "proxycurl_tool"
    description: str = """
    Retrieves profile data using Proxycurl API. Can fetch data from LinkedIn, Twitter, or Facebook profiles.
    Includes enriched data like personal contact info, skills, and inferred salary when available.
    """
    llm: Any = Field(..., description="LLM to use for the tool")
    api_key: Optional[str] = Field(default=None, description="Proxycurl API key")
    base_url: str = "https://nubela.co/proxycurl/api/v2/linkedin"

    def __init__(self, llm: Any = None, **kwargs):
        super().__init__(llm=llm, **kwargs)
        self.api_key = os.getenv('PROXYCURL_API_KEY')
        if not self.api_key:
            print("WARNING: PROXYCURL_API_KEY not found in environment variables")
            raise ValueError("PROXYCURL_API_KEY is required but not found in environment variables")

    def _run(self, profile_url: str, platform: str = "linkedin", **kwargs) -> Dict:
        """
        Fetch profile data for the given URL.
        
        Args:
            profile_url (str): URL of the profile to fetch
            platform (str): Platform to fetch from ('linkedin', 'twitter', or 'facebook')
            **kwargs: Additional parameters to pass to the API
        """
        if not self.api_key:
            error_msg = "Proxycurl API key not found. Please set PROXYCURL_API_KEY environment variable."
            print(f"ERROR: {error_msg}")
            return {"error": error_msg}
        
        # Set up the parameters
        params = ProxycurlParams(
            **{f"{platform}_profile_url": profile_url},
            **kwargs
        ).dict(exclude_none=True)
        
        # Validate that only one profile URL is provided
        url_params = [
            params.get("linkedin_profile_url"),
            params.get("twitter_profile_url"),
            params.get("facebook_profile_url")
        ]
        if len([url for url in url_params if url]) != 1:
            return {"error": "Exactly one profile URL must be provided"}
            
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            # Log the number of credits used (if available in headers)
            credits_used = response.headers.get('x-credits-used', 'Unknown')
            credits_remaining = response.headers.get('x-credits-remaining', 'Unknown')
            print(f"Credits used: {credits_used}, Credits remaining: {credits_remaining}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Proxycurl API error: {str(e)}",
                "details": {
                    "url": profile_url,
                    "platform": platform,
                    "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                }
            }

    def get_linkedin_profile(self, linkedin_url: str, **kwargs) -> Dict:
        """Convenience method for fetching LinkedIn profiles."""
        return self._run(linkedin_url, platform="linkedin", **kwargs)

    def get_twitter_profile(self, twitter_url: str, **kwargs) -> Dict:
        """Convenience method for fetching Twitter profiles."""
        return self._run(twitter_url, platform="twitter", **kwargs)

    def get_facebook_profile(self, facebook_url: str, **kwargs) -> Dict:
        """Convenience method for fetching Facebook profiles."""
        return self._run(facebook_url, platform="facebook", **kwargs)

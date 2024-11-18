# tools/proxycurl_tool.py

from crewai.tools import BaseTool
import os
import requests
from typing import Dict, Any, Optional
from pydantic import Field

class ProxycurlTool(BaseTool):
    """Tool for retrieving LinkedIn profile data using Proxycurl API."""
    
    name: str = "proxycurl_tool"
    description: str = "Retrieves LinkedIn profile data using Proxycurl API."
    llm: Any = Field(..., description="LLM to use for the tool")
    api_key: Optional[str] = Field(default=None, description="Proxycurl API key")

    def __init__(self, llm: Any = None, **kwargs):
        super().__init__(llm=llm, **kwargs)
        self.api_key = os.getenv('PROXYCURL_API_KEY')

    def _run(self, linkedin_url: str) -> Dict:
        """Fetch LinkedIn profile data for the given URL."""
        if not self.api_key:
            return {"error": "Proxycurl API key not found."}
            
        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {'url': linkedin_url}
        
        try:
            response = requests.get(
                'https://api.proxycurl.com/v2/linkedin', 
                headers=headers, 
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Proxycurl API error: {str(e)}"}

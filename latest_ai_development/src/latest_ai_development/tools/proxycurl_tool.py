# tools/proxycurl_tool.py

from crewai.tools import BaseTool
import os
import requests

class ProxycurlTool(BaseTool):
    name = "proxycurl_tool"
    description = "Retrieves LinkedIn profile data using Proxycurl API."

    def _run(self, linkedin_url: str) -> dict:
        """Fetch LinkedIn profile data for the given URL."""
        api_key = os.getenv('PROXYCURL_API_KEY')
        if not api_key:
            return {"error": "Proxycurl API key not found."}
        headers = {'Authorization': f'Bearer {api_key}'}
        params = {'url': linkedin_url}
        response = requests.get('https://api.proxycurl.com/v2/linkedin', headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Proxycurl API error: {response.text}"}

from crewai.tools import BaseTool
import os
from typing import ClassVar, Optional, Any
from pydantic import Field, ConfigDict
from dotenv import load_dotenv
from openai import OpenAI

class PerplexityTool(BaseTool):
    name: ClassVar[str] = "perplexity_tool"
    tool_description: ClassVar[str] = "Performs web research using Perplexity API"
    api_key: Optional[str] = Field(default=None, exclude=True)
    client: Any = Field(default=None, exclude=True)
    
    # Allow arbitrary types in the model
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, llm=None):
        super().__init__(llm=llm)
        load_dotenv()
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.perplexity.ai"
        )

    @property
    def description(self) -> str:
        return self.tool_description

    def _run(self, query: str, focus: str = 'business') -> str:
        """
        Perform research using Perplexity API
        
        Args:
            query (str): Research query
            focus (str): Research focus area (business, tech, general)
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are a business research assistant focused on {focus}. "
                        "Provide detailed, factual information with citations where possible. "
                        "Focus on recent and relevant information."
                    )
                },
                {
                    "role": "user",
                    "content": self._format_research_prompt(query, focus)
                }
            ]
            
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=messages,
            )
            
            result = response.choices[0].message.content
            
            if not self._validate_response(result):
                raise ValueError("Invalid or empty response from Perplexity API")
            
            print(f"Perplexity Research Query: {query}")
            print(f"Response length: {len(result)} characters")
            
            return result
            
        except Exception as e:
            error_msg = f"Perplexity API error: {str(e)}"
            print(error_msg)
            return f"Error during research: {error_msg}"

    def _validate_response(self, response: str) -> bool:
        """Validate the response from Perplexity API"""
        if not response:
            return False
        if response.startswith('Error'):
            return False
        if len(response.strip()) < 10:  # Arbitrary minimum length
            return False
        return True

    def _format_research_prompt(self, query: str, focus: str) -> str:
        """Helper method to format research prompts"""
        focus_prompts = {
            'business': (
                "Focus on business-specific information, market trends, "
                "company details, and industry analysis."
            ),
            'tech': (
                "Focus on technical details, technology stack information, "
                "integration capabilities, and technical challenges."
            ),
            'general': (
                "Provide comprehensive information from various reliable sources."
            )
        }
        
        return f"{query}\n\nContext: {focus_prompts.get(focus, focus_prompts['general'])}"
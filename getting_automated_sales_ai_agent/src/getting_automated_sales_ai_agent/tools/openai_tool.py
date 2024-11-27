# tools/openai_tool.py

from crewai.tools import BaseTool
import os
from typing import ClassVar, Optional, Any
from pydantic import Field, ConfigDict
from openai import OpenAI
from dotenv import load_dotenv

class OpenAITool(BaseTool):
    name: ClassVar[str] = "openai_tool"
    tool_description: ClassVar[str] = "Performs NLP tasks using OpenAI's GPT-4 model."
    api_key: Optional[str] = Field(default=None, exclude=True)
    client: Any = Field(default=None, exclude=True)
    
    # Allow arbitrary types in the model
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, llm=None):
        super().__init__(llm=llm)
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)

    @property
    def description(self) -> str:
        return self.tool_description

    def _run(self, prompt: str | dict, max_tokens: int = 1500, temperature: float = 0.5) -> str:
        """Generate a completion for the given prompt.
        
        Args:
            prompt: Either a string prompt or a dictionary containing prompt info
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for response generation
        """
        try:
            # Handle dictionary input
            if isinstance(prompt, dict):
                prompt = prompt.get('prompt', '') if isinstance(prompt.get('prompt'), str) else str(prompt)
            
            # Ensure prompt is a string
            prompt = str(prompt)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            print(error_msg)
            return f"Error during completion: {error_msg}"

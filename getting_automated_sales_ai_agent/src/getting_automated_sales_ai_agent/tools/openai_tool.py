# tools/openai_tool.py

from crewai.tools import BaseTool
import os
import openai
from typing import ClassVar

class OpenAITool(BaseTool):
    name: ClassVar[str] = "openai_tool"
    description: ClassVar[str] = "Performs NLP tasks using OpenAI's GPT-4 model."

    def _run(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.5) -> str:
        """Generate a completion for the given prompt."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return "OpenAI API key not found."
        openai.api_key = api_key
        response = openai.Completion.create(
            engine='gpt-4',  # Or use 'text-davinci-003' for GPT-3
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].text.strip()

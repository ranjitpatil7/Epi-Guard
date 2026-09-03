from abc import ABC, abstractmethod
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, system_prompt: str, messages: list, tools: list = None, response_schema: type[BaseModel] = None) -> tuple[str, list]:
        """
        Generates a response from the LLM.
        Returns a tuple: (content_string, tool_calls_list)
        """
        pass

from app.core.config import settings

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set. Copilot cannot operate.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = os.environ.get("LLM_MODEL", "gemini-2.5-flash")

    async def generate_response(self, system_prompt: str, messages: list, tools: list = None, response_schema: type[BaseModel] = None) -> tuple[str, list]:
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
            
        config_kwargs = {
            "system_instruction": system_prompt,
            "temperature": 0.2,
        }
        
        # Tools in Google GenAI are usually function declarations
        if tools:
            # For simplicity in this demo we rely on standard prompting or structured schema.
            # Real tool integration with google-genai would pass 'tools' here.
            # Due to the complexity of dynamic schema binding, we'll let the agent just return structured JSON directly.
            pass
            
        if response_schema:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema
            
        config = types.GenerateContentConfig(**config_kwargs)

        try:
            # We use synchronous generate_content because google-genai async support might require specific async client setup,
            # but we'll wrap it or just use the standard client for now.
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            return response.text, []
        except Exception as e:
            raise RuntimeError(f"LLM Provider Error: {str(e)}")

def get_llm_provider() -> BaseLLMProvider:
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return GeminiProvider()
    else:
        raise NotImplementedError(f"LLM Provider {provider} is not implemented.")

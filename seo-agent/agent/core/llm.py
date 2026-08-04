import json
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from core.config import GEMINI_API_KEY

T = TypeVar("T", bound=BaseModel)

# Global client, initialized lazily
_client: Optional[genai.Client] = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured. Please set it in your .env file.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = "gemini-2.5-flash"
) -> str:
    """Generate plain text from Gemini."""
    client = get_client()
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
        
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        return response.text
    except APIError as e:
        print(f"Gemini API Error: {e}")
        raise e

def generate_json(
    prompt: str,
    response_schema: Type[T],
    system_instruction: Optional[str] = None,
    model: str = "gemini-2.5-flash"
) -> T:
    """Generate structured JSON parsed into a Pydantic model."""
    client = get_client()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema
    )
    if system_instruction:
        config.system_instruction = system_instruction
        
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        # Parse text into Pydantic model
        data = json.loads(response.text)
        return response_schema.model_validate(data)
    except APIError as e:
        print(f"Gemini API Error (JSON): {e}")
        raise e
    except Exception as e:
        print(f"Failed to parse JSON response: {e}")
        # Log response text for debugging
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Raw Response: {response.text}")
        raise e

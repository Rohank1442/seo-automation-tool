import json
import time
from typing import Type, TypeVar, Optional, List
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from core.config import GEMINI_API_KEY, GEMINI_MODEL

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
    model: Optional[str] = None
) -> str:
    """Generate plain text from Gemini with automatic retry and model fallback."""
    client = get_client()
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
        
    target_model = model or GEMINI_MODEL
    models_to_try = [target_model]
    for fallback in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)
            
    last_error = None
    for m in models_to_try:
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=config
                )
                return response.text
            except APIError as e:
                last_error = e
                is_transient = (e.code in [429, 503]) or ("demand" in str(e).lower()) or ("unavailable" in str(e).lower())
                if is_transient:
                    if attempt < max_retries - 1:
                        print(f"Gemini API returned {e.code} for model '{m}'. Retrying in {delay} seconds (attempt {attempt+1}/{max_retries})...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        print(f"Model '{m}' exhausted retries. Trying next model...")
                        break
                else:
                    print(f"Gemini API Non-transient Error: {e}")
                    raise e
                    
    raise RuntimeError(f"All model attempts failed. Last error: {last_error}")

def generate_json(
    prompt: str,
    response_schema: Type[T],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None
) -> T:
    """Generate structured JSON parsed into a Pydantic model with retry and fallback."""
    client = get_client()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema
    )
    if system_instruction:
        config.system_instruction = system_instruction
        
    target_model = model or GEMINI_MODEL
    models_to_try = [target_model]
    for fallback in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)
            
    last_error = None
    for m in models_to_try:
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=config
                )
                data = json.loads(response.text)
                return response_schema.model_validate(data)
            except APIError as e:
                last_error = e
                is_transient = (e.code in [429, 503]) or ("demand" in str(e).lower()) or ("unavailable" in str(e).lower())
                if is_transient:
                    if attempt < max_retries - 1:
                        print(f"Gemini API returned {e.code} (JSON) for model '{m}'. Retrying in {delay} seconds (attempt {attempt+1}/{max_retries})...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        print(f"Model '{m}' (JSON) exhausted retries. Trying next model...")
                        break
                else:
                    print(f"Gemini API Non-transient Error (JSON): {e}")
                    raise e
            except Exception as e:
                print(f"Failed parsing response from model '{m}': {e}")
                if 'response' in locals() and hasattr(response, 'text'):
                    print(f"Raw response was: {response.text}")
                # This is likely a format issue rather than a transient API issue, so we try next model
                break
                
    raise RuntimeError(f"All JSON model attempts failed. Last error: {last_error}")

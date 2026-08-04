import os
import sys
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# Required Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SERVICE_ROLE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Optional Config
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

def validate_config():
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
        
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Please copy .env.example to .env and fill in the values.")
        print("Required values are: SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY")
        sys.exit(1)

# Run validation when imported, unless running tests or running in a context where we want to handle it manually.
# Let's let the main runner validate it.

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
# Product APIs stay closed unless the trusted local environment opts out.
EARLY_ACCESS_MODE = os.getenv("EARLY_ACCESS_MODE", "true").strip().lower() not in {
    "0", "false", "no", "off"
}

# Custom Auth & JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "seo-automation-custom-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")) # 7 days
AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "seo_access_token")
PIPELINE_ARTIFACTS_BUCKET = os.getenv("PIPELINE_ARTIFACTS_BUCKET", "pipeline-artifacts")

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

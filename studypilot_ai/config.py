"""Central settings for StudyPilot AI, read from studypilot_ai/.env."""
import os
import warnings
from pathlib import Path
from dotenv import load_dotenv
from google.genai import types
# Load studypilot_ai/.env (the same folder as this file).
load_dotenv(Path(__file__).resolve().parent / ".env")
# The Gemini model every agent uses. Change it in .env, not in code.
MODEL_NAME = os.getenv("STUDYPILOT_MODEL", "gemini-3.5-flash")
# Missing API key: warn clearly instead of failing later with a confusing error.
_api_key = os.getenv("GOOGLE_API_KEY", "")
if not _api_key or _api_key == "REPLACE_WITH_YOUR_KEY":
   warnings.warn("GOOGLE_API_KEY is not set in studypilot_ai/.env, so Gemini calls will fail.")
# If Gemini is busy (503) or a rate limit is hit (429), wait and try again.
# Waits grow each time (about 2 s, 4 s, 8 s, 16 s) for up to 5 attempts in total.
RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=2, attempts=5)

def generation_config(temperature):
   """Gemini settings shared by all agents: a temperature plus automatic retries."""
   return types.GenerateContentConfig(
       temperature=temperature,
       http_options=types.HttpOptions(retry_options=RETRY_OPTIONS),
   )
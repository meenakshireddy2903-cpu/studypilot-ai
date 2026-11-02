"""Quick check: is the Gemini API key loaded, valid, and able to reach Gemini?"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import errors
# Where our .env file lives: <project root>/studypilot_ai/.env
ENV_FILE = Path(__file__).resolve().parent.parent / "studypilot_ai" / ".env"
# Model to test. You can pass a different one: python scripts\check_api_key.py <model-name>
MODEL_TO_TEST = sys.argv[1] if len(sys.argv) > 1 else "gemini-3.5-flash"

def main() -> None:
   # 1. Load settings from studypilot_ai/.env into environment variables
   load_dotenv(ENV_FILE)
   api_key = os.getenv("GOOGLE_API_KEY", "")
   if not api_key or api_key == "REPLACE_WITH_YOUR_KEY":
       print(f"No real GOOGLE_API_KEY found in {ENV_FILE}")
       return
   print(f"OK: key loaded from .env (length {len(api_key)}, value not shown)")
   # 2. Create a Gemini client that uses our key
   client = genai.Client(api_key=api_key)
   try:
       # 3. List the Gemini models this key can use for text generation
       print("\nGemini models available to your key:")
       available = []
       for model in client.models.list():
           actions = getattr(model, "supported_actions", None) or []
           if "generateContent" in actions and "gemini" in model.name:
               short_name = model.name.removeprefix("models/")
               available.append(short_name)
               print("  -", short_name)
       if available and MODEL_TO_TEST not in available:
           print(f"\nWARNING: '{MODEL_TO_TEST}' is not in the list above.")
           print("Pick one from the list and run:")
           print("  python scripts\\check_api_key.py <model-name>")
           return
       # 4. Send one tiny test message
       print(f"\nSending a test message to {MODEL_TO_TEST} ...")
       response = client.models.generate_content(
           model=MODEL_TO_TEST,
           contents="Reply with exactly: StudyPilot key works",
       )
       print("Gemini replied:", response.text)
       print("\nSUCCESS: your key, network and model all work.")
   except errors.APIError as e:
       print(f"\nGemini API error {e.code}: {e.message}")
   except Exception as e:
       print(f"\nCould not reach Gemini ({type(e).__name__}): {e}")

if __name__ == "__main__":
   main()
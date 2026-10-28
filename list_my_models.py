import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("[+] Fetching available models for your API key...")
try:
    for model in client.models.list():
        # Only show models that support generateContent
        if "generateContent" in (model.supported_actions or []):
            print(f" -> {model.name}")
except Exception as e:
    print(f"[!] Error listing models: {e}")
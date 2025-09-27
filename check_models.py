import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("❌ GOOGLE_API_KEY not found in .env or environment")

genai.configure(api_key=api_key)

print("✅ Connected. Listing available models...\n")

for m in genai.list_models():
    print(m.name, "→", m.supported_generation_methods)

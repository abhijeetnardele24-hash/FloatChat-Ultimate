"""
Simple test script to verify Gemini API connection.
"""

import os

from dotenv import load_dotenv
import google.generativeai as genai


# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {api_key[:20]}..." if api_key else "API Key NOT found!")

# Configure Gemini
genai.configure(api_key=api_key)

# Prefer configured model, but fallback if unavailable or quota-limited.
primary_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
if primary_model.startswith("models/"):
    primary_model = primary_model.replace("models/", "", 1)

model_candidates = [primary_model, "gemini-2.5-flash", "gemini-flash-latest"]
seen = set()
model_candidates = [m for m in model_candidates if not (m in seen or seen.add(m))]

print("\nTesting Gemini API...")
last_error = None

for model_name in model_candidates:
    try:
        print(f"Trying model: {model_name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("What is ocean salinity?")
        print(f"\nResponse: {response.text}")
        print(f"\nGemini API is working with model: {model_name}")
        break
    except Exception as e:
        last_error = e
        print(f"Model failed: {model_name} -> {e}")
else:
    raise RuntimeError(f"All model attempts failed: {last_error}")

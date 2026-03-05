"""
List available Gemini models
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

# List available models
print("\nAvailable Gemini models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")

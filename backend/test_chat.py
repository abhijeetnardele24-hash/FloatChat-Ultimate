"""
Quick chat test through the API (OpenAI path).
Falls back to other providers when OpenAI is unavailable.
"""

import requests
import json

# Test general ocean question with OpenAI
print("Testing OpenAI chat integration...")
print("=" * 60)

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "What causes ocean currents?",
        "provider": "openai"
    }
)

result = response.json()

print(f"\nSuccess: {result.get('success')}")
print(f"Source: {result.get('source')}")
print(f"Query Type: {result.get('query_type')}")
print(f"\nResponse:\n{result.get('response')}")

if result.get('error'):
    print(f"\nError: {result.get('error')}")

print("\n" + "=" * 60)

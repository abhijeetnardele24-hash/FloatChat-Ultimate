#!/usr/bin/env python3
"""
Test script to verify Groq API integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_groq_integration():
    """Test Groq API integration"""
    try:
        from llm.groq_engine import GroqQueryEngine
        
        print("🚀 Testing Groq Integration...")
        print(f"API Key: {os.getenv('GROQ_API_KEY', 'Not found')[:20]}...")
        print(f"Model: {os.getenv('GROQ_MODEL', 'Not configured')}")
        
        # Initialize Groq engine
        engine = GroqQueryEngine()
        print("✅ Groq engine initialized successfully!")
        
        # Test health check
        health = engine.health_check()
        print(f"✅ Health check: {health}")
        
        # Test a simple query
        test_query = "What are ARGO floats in oceanography?"
        print(f"🧪 Testing query: {test_query}")
        
        result = engine.query(test_query)
        print(f"✅ Query result: {result}")
        
        if result.get('success'):
            print("🎉 Groq integration is working perfectly!")
            print(f"📝 Response: {result.get('response', 'No response')[:200]}...")
            return True
        else:
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Groq integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_groq_integration()
    sys.exit(0 if success else 1)

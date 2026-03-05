#!/usr/bin/env python3
"""
Simple test to demonstrate Groq API working without database dependencies
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Groq Test API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    message: str

# Initialize Groq
try:
    from llm.groq_engine import GroqQueryEngine
    groq_engine = GroqQueryEngine()
    print("✅ Groq engine initialized successfully!")
except Exception as e:
    print(f"❌ Groq engine failed: {e}")
    groq_engine = None

@app.get("/")
async def root():
    return {"message": "Groq Test API is running!", "groq_available": groq_engine is not None}

@app.get("/health")
async def health():
    if groq_engine:
        return {"status": "healthy", "groq": groq_engine.health_check()}
    return {"status": "limited", "groq": None}

@app.post("/chat")
async def chat(request: ChatRequest):
    if not groq_engine:
        return {"success": False, "response": "Groq engine not available"}
    
    try:
        result = groq_engine.query(request.message)
        return result
    except Exception as e:
        return {"success": False, "response": f"Error: {e}"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Groq Test API on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)

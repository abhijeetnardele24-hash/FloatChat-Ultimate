"""
Test script to identify where the PostgreSQL dialect error is coming from
"""

print("Step 1: Testing basic imports...")
try:
    from fastapi import FastAPI
    print("✅ FastAPI imported")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")

print("\nStep 2: Testing SQLAlchemy...")
try:
    from sqlalchemy import create_engine
    print("✅ SQLAlchemy imported")
except Exception as e:
    print(f"❌ SQLAlchemy import failed: {e}")

print("\nStep 3: Testing database connection...")
try:
    from sqlalchemy import create_engine
    engine = create_engine("postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat")
    print("✅ Database engine created")
except Exception as e:
    print(f"❌ Database engine creation failed: {e}")

print("\nStep 4: Testing dotenv...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Dotenv loaded")
except Exception as e:
    print(f"❌ Dotenv failed: {e}")

print("\nStep 5: Testing main.py imports...")
try:
    import sys
    sys.path.insert(0, '.')
    # Don't import main, just test if we can import the modules it uses
    print("✅ Path setup complete")
except Exception as e:
    print(f"❌ Import test failed: {e}")

print("\nStep 6: Testing router imports...")
try:
    from routers import argo_filter
    print("✅ ARGO filter router imported")
except Exception as e:
    print(f"❌ Router import failed: {e}")

print("\nStep 7: Testing LLM imports...")
try:
    from llm import chat_service
    print("✅ Chat service imported")
except Exception as e:
    print(f"❌ Chat service import failed: {e}")
    import traceback
    traceback.print_exc()

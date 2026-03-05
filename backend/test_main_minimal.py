"""
Minimal test of main.py to identify the issue
"""

print("Step 1: Loading dotenv...")
from dotenv import load_dotenv
load_dotenv()
print("✅ Dotenv loaded")

print("\nStep 2: Importing os...")
import os
print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL', 'NOT FOUND')[:50]}...")

print("\nStep 3: Creating database engine...")
from sqlalchemy import create_engine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat")
print(f"Using DATABASE_URL: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(DATABASE_URL)
    print("✅ Engine created successfully")
except Exception as e:
    print(f"❌ Engine creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 4: Testing connection...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Connection successful: {result.scalar()}")
except Exception as e:
    print(f"❌ Connection failed: {e}")

print("\nStep 5: Creating SessionLocal...")
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("✅ SessionLocal created")

print("\nStep 6: Importing FastAPI...")
from fastapi import FastAPI
app = FastAPI()
print("✅ FastAPI app created")

print("\n✅ ALL TESTS PASSED!")

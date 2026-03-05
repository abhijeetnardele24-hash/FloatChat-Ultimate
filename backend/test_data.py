#!/usr/bin/env python3
"""Test database connection and data"""

import psycopg2

def test_data():
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="floatchat",
        user="floatchat_user",
        password="1234"
    )
    cursor = conn.cursor()
    
    try:
        # Test counts
        cursor.execute("SELECT COUNT(*) FROM argo_floats")
        floats = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_profiles")
        profiles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_measurements")
        measurements = cursor.fetchone()[0]
        
        # Test sample data
        cursor.execute("SELECT wmo_number, ocean_basin FROM argo_floats LIMIT 5")
        sample_floats = cursor.fetchall()
        
        print(f"✅ Database connected!")
        print(f"   Floats: {floats}")
        print(f"   Profiles: {profiles}")
        print(f"   Measurements: {measurements}")
        print(f"   Sample floats: {sample_floats}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_data()

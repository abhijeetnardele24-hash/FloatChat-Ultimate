#!/usr/bin/env python3
"""
Direct SQL insert of sample ARGO data
Bypasses SQLAlchemy connection issues
"""

import psycopg2
import random
from datetime import datetime, timedelta

def insert_sample_data():
    """Insert sample data directly via psycopg2"""
    
    # Database connection
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="floatchat",
        user="floatchat_user",
        password="1234"
    )
    cursor = conn.cursor()
    
    try:
        # Sample float data
        sample_floats = [
            ("1901234", "APEX", datetime(2021, 1, 15), 12.5, 75.2, "ACTIVE", "Indian Ocean"),
            ("1901235", "APEX", datetime(2021, 2, 20), 35.7, -75.3, "ACTIVE", "Pacific Ocean"),
            ("1901236", "ARVOR", datetime(2021, 3, 10), 40.2, -30.1, "ACTIVE", "Atlantic Ocean"),
            ("1901237", "APEX", datetime(2021, 4, 5), -55.8, 45.2, "ACTIVE", "Southern Ocean"),
            ("1901238", "SOLO", datetime(2021, 5, 12), 78.5, 15.3, "ACTIVE", "Arctic Ocean"),
            ("1901239", "APEX", datetime(2021, 6, 8), 35.0, 25.0, "ACTIVE", "Mediterranean Sea"),
            ("1901240", "APEX", datetime(2021, 7, 15), 10.2, 80.1, "ACTIVE", "Indian Ocean"),
            ("1901241", "ARVOR", datetime(2021, 8, 22), -20.5, 120.3, "ACTIVE", "Pacific Ocean"),
            ("1901242", "APEX", datetime(2021, 9, 10), 45.8, -60.2, "ACTIVE", "Atlantic Ocean"),
            ("1901243", "SOLO", datetime(2021, 10, 5), -65.1, 0.0, "ACTIVE", "Southern Ocean"),
        ]
        
        # Insert floats
        for wmo, platform, date, lat, lon, status, ocean in sample_floats:
            cursor.execute("""
                INSERT INTO argo_floats (wmo_number, platform_type, deployment_date, last_latitude, last_longitude, status, ocean_basin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (wmo_number) DO NOTHING
            """, (wmo, platform, date, lat, lon, status, ocean))
        
        # Get float IDs and WMO numbers
        cursor.execute("SELECT id, wmo_number FROM argo_floats ORDER BY wmo_number")
        float_data = cursor.fetchall()
        
        # Insert profiles and measurements
        for float_id, wmo_number in float_data:
            for cycle in range(1, 6):  # 5 profiles per float
                profile_date = datetime(2021, 1, 1) + timedelta(days=cycle * 10)
                lat = random.uniform(-60, 60)
                lon = random.uniform(-180, 180)
                
                # Insert profile
                cursor.execute("""
                    INSERT INTO argo_profiles (float_id, wmo_number, cycle_number, profile_date, latitude, longitude)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (float_id, wmo_number, cycle, profile_date, lat, lon))
                profile_id = cursor.fetchone()[0]
                
                # Insert measurements (depth levels)
                depths = [5, 10, 20, 50, 100, 200, 500, 1000, 1500, 2000]
                
                for depth in depths:
                    # Realistic temperature and salinity based on depth
                    if depth < 100:
                        temp = random.uniform(15, 30)
                        sal = random.uniform(34, 36)
                    elif depth < 500:
                        temp = random.uniform(8, 20)
                        sal = random.uniform(34.5, 35.5)
                    elif depth < 1000:
                        temp = random.uniform(4, 12)
                        sal = random.uniform(34.6, 34.9)
                    else:
                        temp = random.uniform(2, 6)
                        sal = random.uniform(34.7, 34.8)
                    
                    cursor.execute("""
                        INSERT INTO argo_measurements (profile_id, pressure, depth, temperature, salinity, temperature_qc, salinity_qc)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (profile_id, depth, depth, temp, sal, 1, 1))
        
        conn.commit()
        
        # Check results
        cursor.execute("SELECT COUNT(*) FROM argo_floats")
        float_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_profiles")
        profile_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_measurements")
        measurement_count = cursor.fetchone()[0]
        
        print(f"✅ Sample data inserted successfully!")
        print(f"   Floats: {float_count}")
        print(f"   Profiles: {profile_count}")
        print(f"   Measurements: {measurement_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    insert_sample_data()

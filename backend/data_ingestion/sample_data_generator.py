#!/usr/bin/env python3
"""
Generate Sample ARGO Data for Testing
Creates realistic oceanographic data to test the system while real data ingestion is being fixed.
"""

import os
import sys
import random
from datetime import datetime, timedelta
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, ".env"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.db import get_database_url

class SampleDataGenerator:
    def __init__(self):
        self.engine = create_engine(get_database_url())
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Ocean basin regions
        self.ocean_regions = {
            "Indian Ocean": {"lat_range": (-40, 30), "lon_range": (30, 120)},
            "Pacific Ocean": {"lat_range": (-60, 65), "lon_range": (120, 290)},
            "Atlantic Ocean": {"lat_range": (-65, 70), "lon_range": (290, 360)},
            "Southern Ocean": {"lat_range": (-90, -35), "lon_range": (-180, 180)},
            "Arctic Ocean": {"lat_range": (65, 90), "lon_range": (-180, 180)},
            "Mediterranean Sea": {"lat_range": (30, 46), "lon_range": (0, 42)}
        }
    
    def generate_realistic_profile(self, lat: float, lon: float, ocean_basin: str) -> dict:
        """Generate realistic T/S/P profile based on ocean basin"""
        
        # Depth levels (pressure in dbar, approximately equal to meters)
        depths = np.array([5, 10, 20, 50, 100, 200, 500, 1000, 1500, 2000])
        
        # Temperature profile based on depth and location
        if ocean_basin == "Indian Ocean":
            # Warm surface, strong thermocline
            surface_temp = 28 + random.uniform(-2, 2)
            deep_temp = 2 + random.uniform(-1, 1)
        elif ocean_basin == "Pacific Ocean":
            # Variable by latitude
            surface_temp = 25 + abs(lat) * 0.1 + random.uniform(-3, 3)
            deep_temp = 1.5 + random.uniform(-1, 1)
        elif ocean_basin == "Atlantic Ocean":
            surface_temp = 22 + abs(lat) * 0.15 + random.uniform(-3, 3)
            deep_temp = 2 + random.uniform(-1, 1)
        elif ocean_basin == "Southern Ocean":
            surface_temp = 2 + random.uniform(-2, 2)
            deep_temp = -1 + random.uniform(-0.5, 0.5)
        elif ocean_basin == "Arctic Ocean":
            surface_temp = -1 + random.uniform(-2, 2)
            deep_temp = -1 + random.uniform(-0.5, 0.5)
        else:  # Mediterranean
            surface_temp = 24 + random.uniform(-2, 2)
            deep_temp = 13 + random.uniform(-1, 1)
        
        # Generate temperature profile with exponential decay
        temps = surface_temp * np.exp(-depths / 200) + deep_temp
        temps = temps + np.random.normal(0, 0.1, len(depths))  # Add noise
        
        # Generate salinity profile
        if ocean_basin == "Mediterranean Sea":
            surface_sal = 38.5 + random.uniform(-0.5, 0.5)
            deep_sal = 38.8 + random.uniform(-0.3, 0.3)
        elif ocean_basin == "Atlantic Ocean":
            surface_sal = 35.5 + random.uniform(-1, 1)
            deep_sal = 34.9 + random.uniform(-0.2, 0.2)
        elif ocean_basin == "Pacific Ocean":
            surface_sal = 34.5 + random.uniform(-1, 1)
            deep_sal = 34.6 + random.uniform(-0.2, 0.2)
        elif ocean_basin == "Indian Ocean":
            surface_sal = 35.0 + random.uniform(-1, 1)
            deep_sal = 34.7 + random.uniform(-0.2, 0.2)
        else:  # Polar regions
            surface_sal = 34.0 + random.uniform(-0.5, 0.5)
            deep_sal = 34.6 + random.uniform(-0.2, 0.2)
        
        # Salinity profile with some variation
        sals = surface_sal + (deep_sal - surface_sal) * (depths / 2000)
        sals = sals + np.random.normal(0, 0.02, len(depths))  # Add noise
        
        return {
            'depths': depths.tolist(),
            'temperatures': temps.tolist(),
            'salinities': sals.tolist()
        }
    
    def generate_float_data(self, num_floats: int = 100):
        """Generate sample float data"""
        with self.SessionLocal() as session:
            try:
                for i in range(num_floats):
                    # Random ocean basin
                    ocean_basin = random.choice(list(self.ocean_regions.keys()))
                    region = self.ocean_regions[ocean_basin]
                    
                    # Random location within ocean basin
                    lat = random.uniform(*region["lat_range"])
                    lon = random.uniform(*region["lon_range"])
                    
                    # WMO number (6-7 digits)
                    wmo_number = f"{random.randint(1000000, 9999999)}"
                    
                    # Insert float
                    insert_sql = text("""
                        INSERT INTO argo_floats (wmo_number, platform_type, deployment_date, last_latitude, last_longitude, status, ocean_basin)
                        VALUES (:wmo, 'APEX', :date, :lat, :lon, 'ACTIVE', :basin)
                        ON CONFLICT (wmo_number) DO NOTHING
                    """)
                    
                    session.execute(insert_sql, {
                        "wmo": wmo_number,
                        "date": datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1800)),
                        "lat": lat,
                        "lon": lon,
                        "basin": ocean_basin
                    })
                
                session.commit()
                print(f"Generated {num_floats} sample floats")
                
            except Exception as e:
                print(f"Error: {e}")
                session.rollback()
    
    def generate_profile_data(self, profiles_per_float: int = 10):
        """Generate sample profile data"""
        with self.SessionLocal() as session:
            try:
                # Get existing floats
                result = session.execute(text("SELECT id, wmo_number, last_latitude, last_longitude, ocean_basin FROM argo_floats"))
                floats = result.fetchall()
                
                if not floats:
                    print("No floats found. Run generate_float_data first.")
                    return
                
                profile_count = 0
                
                for float_id, wmo_number, lat, lon, ocean_basin in floats:
                    for cycle in range(1, profiles_per_float + 1):
                        # Profile date (every 10 days)
                        profile_date = datetime(2021, 1, 1) + timedelta(days=cycle * 10)
                        
                        # Slightly vary position for each profile
                        profile_lat = lat + random.uniform(-0.5, 0.5)
                        profile_lon = lon + random.uniform(-0.5, 0.5)
                        
                        # Insert profile
                        profile_sql = text("""
                            INSERT INTO argo_profiles (float_id, cycle_number, profile_date, latitude, longitude)
                            VALUES (:float_id, :cycle, :date, :lat, :lon)
                            RETURNING id
                        """)
                        
                        result = session.execute(profile_sql, {
                            "float_id": float_id,
                            "cycle": cycle,
                            "date": profile_date,
                            "lat": profile_lat,
                            "lon": profile_lon
                        })
                        profile_id = result.fetchone()[0]
                        
                        # Generate measurements
                        profile_data = self.generate_realistic_profile(profile_lat, profile_lon, ocean_basin)
                        
                        measurement_sql = text("""
                            INSERT INTO argo_measurements (profile_id, pressure, depth, temperature, salinity, temperature_qc, salinity_qc)
                            VALUES (:profile_id, :pressure, :depth, :temp, :sal, 1, 1)
                        """)
                        
                        for i in range(len(profile_data['depths'])):
                            session.execute(measurement_sql, {
                                "profile_id": profile_id,
                                "pressure": profile_data['depths'][i],
                                "depth": profile_data['depths'][i],
                                "temp": profile_data['temperatures'][i],
                                "sal": profile_data['salinities'][i]
                            })
                        
                        profile_count += 1
                
                session.commit()
                print(f"Generated {profile_count} sample profiles with measurements")
                
            except Exception as e:
                print(f"Error: {e}")
                session.rollback()
    
    def generate_all_data(self, num_floats: int = 100, profiles_per_float: int = 10):
        """Generate complete sample dataset"""
        print("Generating sample ARGO data...")
        self.generate_float_data(num_floats)
        self.generate_profile_data(profiles_per_float)
        print("Sample data generation complete!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample ARGO data for testing")
    parser.add_argument("--floats", type=int, default=100, help="Number of floats to generate")
    parser.add_argument("--profiles", type=int, default=10, help="Profiles per float")
    
    args = parser.parse_args()
    
    generator = SampleDataGenerator()
    generator.generate_all_data(args.floats, args.profiles)

if __name__ == "__main__":
    main()

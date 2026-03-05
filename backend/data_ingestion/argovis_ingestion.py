#!/usr/bin/env python3
"""
Argovis API Ingestion Script
Alternative to IFREMER GDAC when network timeouts occur.

Usage:
    python argovis_ingestion.py --start-date 2021-01-01 --end-date 2026-02-27 --max-profiles 5000
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.db import get_database_url
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ocean code mapping (same as main ingestion)
OCEAN_CODE_MAP = {
    "I": "Indian Ocean",
    "P": "Pacific Ocean", 
    "A": "Atlantic Ocean",
    "S": "Southern Ocean",
    "M": "Mediterranean Sea",
    "N": "Arctic Ocean",
    "T": "N Atlantic Subpolar",
}

class ArgoVisIngestion:
    def __init__(self):
        self.engine = create_engine(get_database_url())
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.base_url = "https://argovis-api.colorado.edu"
        
    def determine_ocean_basin(self, lat: float, lon: float) -> str:
        """Determine ocean basin from coordinates"""
        if lat > 65:
            return "Arctic Ocean"
        elif lat < -35:
            return "Southern Ocean"
        elif 30 <= lat <= 46 and 0 <= lon <= 42:
            return "Mediterranean Sea"
        elif -20 <= lat <= 30 and 30 <= lon <= 120:
            return "Indian Ocean"
        elif -60 <= lat <= 65 and 120 <= lon <= 290:
            return "Pacific Ocean"
        elif -65 <= lat <= 70 and (290 <= lon <= 360 or 0 <= lon <= 30):
            return "Atlantic Ocean"
        else:
            return "Unknown Ocean"
    
    async def fetch_profiles_batch(self, start_date: str, end_date: str, limit: int = 100) -> List[Dict]:
        """Fetch profiles from Argovis API"""
        import httpx
        
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "data": "pressure,temperature,salinity",
            "compression": "minimal",
            "source": "argo_core"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(f"{self.base_url}/argo", params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch from Argovis: {e}")
            return []
    
    def insert_float(self, wmo_number: str, lat: float, lon: float, ocean_basin: str) -> Optional[int]:
        """Insert or get float ID"""
        with self.SessionLocal() as session:
            try:
                # Check if float exists
                result = session.execute(text("SELECT id FROM argo_floats WHERE wmo_number = :wmo"), {"wmo": wmo_number})
                existing = result.fetchone()
                
                if existing:
                    return existing[0]
                
                # Insert new float
                insert_sql = text("""
                    INSERT INTO argo_floats (wmo_number, platform_type, deployment_date, last_latitude, last_longitude, status, ocean_basin)
                    VALUES (:wmo, 'APEX', CURRENT_DATE, :lat, :lon, 'ACTIVE', :basin)
                    RETURNING id
                """)
                
                result = session.execute(insert_sql, {
                    "wmo": wmo_number,
                    "lat": lat,
                    "lon": lon, 
                    "basin": ocean_basin
                })
                session.commit()
                return result.fetchone()[0]
                
            except Exception as e:
                logger.error(f"Error inserting float {wmo_number}: {e}")
                session.rollback()
                return None
    
    def insert_profile(self, profile_data: Dict) -> Optional[int]:
        """Insert profile and measurements"""
        with self.SessionLocal() as session:
            try:
                # Insert float first
                ocean_basin = self.determine_ocean_basin(profile_data['lat'], profile_data['lon'])
                float_id = self.insert_float(profile_data['platform_number'], profile_data['lat'], profile_data['lon'], ocean_basin)
                
                if not float_id:
                    return None
                
                # Insert profile
                profile_sql = text("""
                    INSERT INTO argo_profiles (float_id, cycle_number, profile_date, latitude, longitude)
                    VALUES (:float_id, :cycle, :date, :lat, :lon)
                    RETURNING id
                """)
                
                result = session.execute(profile_sql, {
                    "float_id": float_id,
                    "cycle": profile_data['cycle_number'],
                    "date": profile_data['date'],
                    "lat": profile_data['lat'],
                    "lon": profile_data['lon']
                })
                profile_id = result.fetchone()[0]
                
                # Insert measurements
                measurements = profile_data.get('data', [])
                if measurements:
                    # Parse data structure from Argovis
                    data_keys = profile_data.get('data_keys', [])
                    pres_idx = data_keys.index('pres') if 'pres' in data_keys else 0
                    temp_idx = data_keys.index('temp') if 'temp' in data_keys else 1
                    psal_idx = data_keys.index('psal') if 'psal' in data_keys else 2
                    
                    measurement_sql = text("""
                        INSERT INTO argo_measurements (profile_id, pressure, depth, temperature, salinity, temperature_qc, salinity_qc)
                        VALUES (:profile_id, :pressure, :depth, :temp, :sal, 1, 1)
                    """)
                    
                    for measurement in measurements:
                        if len(measurement) > max(pres_idx, temp_idx, psal_idx):
                            pressure = measurement[pres_idx] if pres_idx < len(measurement) else None
                            temp = measurement[temp_idx] if temp_idx < len(measurement) else None
                            sal = measurement[psal_idx] if psal_idx < len(measurement) else None
                            
                            if pressure is not None and temp is not None:
                                depth = pressure  # Approximate: 1 dbar ≈ 1 meter
                                
                                session.execute(measurement_sql, {
                                    "profile_id": profile_id,
                                    "pressure": pressure,
                                    "depth": depth,
                                    "temp": temp,
                                    "sal": sal
                                })
                
                session.commit()
                logger.info(f"Inserted profile {profile_id} with {len(measurements)} measurements")
                return profile_id
                
            except Exception as e:
                logger.error(f"Error inserting profile: {e}")
                session.rollback()
                return None
    
    async def run_ingestion(self, start_date: str, end_date: str, max_profiles: int = 1000):
        """Main ingestion loop"""
        logger.info(f"Starting Argovis ingestion from {start_date} to {end_date}")
        
        total_inserted = 0
        batch_size = 100
        batches_processed = 0
        
        while total_inserted < max_profiles:
            remaining = max_profiles - total_inserted
            current_batch_size = min(batch_size, remaining)
            
            logger.info(f"Fetching batch {batches_processed + 1}: {current_batch_size} profiles")
            
            # Calculate date range for this batch
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            total_days = (end_dt - start_dt).days
            batches_needed = max(1, (max_profiles // batch_size) + 1)
            days_per_batch = max(1, total_days // batches_needed) if batches_needed > 0 else 1
            
            batch_start = start_dt + timedelta(days=batches_processed * days_per_batch)
            batch_end = min(batch_start + timedelta(days=days_per_batch), end_dt)
            
            profiles = await self.fetch_profiles_batch(
                batch_start.strftime("%Y-%m-%dT00:00:00Z"),
                batch_end.strftime("%Y-%m-%dT23:59:59Z"),
                current_batch_size
            )
            
            if not profiles:
                logger.info("No more profiles available")
                break
            
            # Insert profiles
            for profile in profiles:
                if total_inserted >= max_profiles:
                    break
                
                profile_id = self.insert_profile(profile)
                if profile_id:
                    total_inserted += 1
            
            batches_processed += 1
            logger.info(f"Progress: {total_inserted}/{max_profiles} profiles inserted")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        logger.info(f"Ingestion complete! Total profiles inserted: {total_inserted}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest ARGO data from Argovis API")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--max-profiles", type=int, default=1000, help="Maximum profiles to ingest")
    
    args = parser.parse_args()
    
    ingestion = ArgoVisIngestion()
    asyncio.run(ingestion.run_ingestion(args.start_date, args.end_date, args.max_profiles))

if __name__ == "__main__":
    main()

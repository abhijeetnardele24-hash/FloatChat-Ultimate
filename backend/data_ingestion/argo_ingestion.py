"""
ARGO Data Ingestion Pipeline
Fetches ARGO float data from IFREMER and loads into PostgreSQL.

Examples:
    python argo_ingestion.py --region indian --max-profiles 500
    python argo_ingestion.py --region global --start-date 2024-01-01 --end-date 2024-12-31 --index-limit 20000
    python argo_ingestion.py --region custom --bbox 30 -40 120 30 --max-profiles 200
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import netCDF4 as nc
import numpy as np
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

ARGO_GDAC_URL = os.getenv("ARGO_GDAC_URL", "https://data-argo.ifremer.fr")
DEFAULT_CACHE_DIR = os.getenv("ARGO_CACHE_DIR", "./data/argo")

INDIAN_OCEAN_BOUNDS = {
    "min_lon": 30.0,
    "min_lat": -40.0,
    "max_lon": 120.0,
    "max_lat": 30.0,
}


@dataclass
class IngestionConfig:
    region: str = "indian"  # indian | global | custom
    bbox: Optional[Tuple[float, float, float, float]] = None  # min_lon, min_lat, max_lon, max_lat
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    index_limit: Optional[int] = 5000
    max_profiles: Optional[int] = 500
    cache_dir: str = DEFAULT_CACHE_DIR
    request_timeout: int = 60
    sleep_seconds: float = 0.1
    force_redownload: bool = False


class ArgoDataIngestion:
    """ARGO float data ingestion pipeline."""

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.session = SessionLocal()
        self.config = config or IngestionConfig()
        os.makedirs(self.config.cache_dir, exist_ok=True)

    def __del__(self):
        if hasattr(self, "session"):
            self.session.close()

    @staticmethod
    def _decode_char_array(value) -> str:
        """Decode ARGO char arrays robustly."""
        try:
            if hasattr(value, "tobytes"):
                return value.tobytes().decode("utf-8", errors="ignore").strip()
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="ignore").strip()
            return str(value).strip()
        except Exception:
            return ""

    @staticmethod
    def _parse_index_datetime(raw_value: str) -> Optional[datetime]:
        """Parse date values from ARGO index (YYYYMMDD... forms)."""
        if not raw_value:
            return None
        cleaned = "".join(ch for ch in raw_value if ch.isdigit())
        if len(cleaned) < 8:
            return None
        try:
            return datetime.strptime(cleaned[:8], "%Y%m%d")
        except Exception:
            return None

    def _active_bbox(self) -> Optional[Tuple[float, float, float, float]]:
        if self.config.region == "global":
            return None
        if self.config.region == "custom":
            return self.config.bbox
        return (
            INDIAN_OCEAN_BOUNDS["min_lon"],
            INDIAN_OCEAN_BOUNDS["min_lat"],
            INDIAN_OCEAN_BOUNDS["max_lon"],
            INDIAN_OCEAN_BOUNDS["max_lat"],
        )

    def _lon_to_0_360(self, lon: float) -> float:
        return lon + 360.0 if lon < 0 else lon

    def _is_in_bbox(self, lat: float, lon: float) -> bool:
        bbox = self._active_bbox()
        if bbox is None:
            return True
        min_lon, min_lat, max_lon, max_lat = bbox
        normalized_lon = self._lon_to_0_360(lon)
        return min_lat <= lat <= max_lat and min_lon <= normalized_lon <= max_lon

    def _date_in_range(self, dt: Optional[datetime]) -> bool:
        if dt is None:
            return True
        if self.config.start_date and dt < self.config.start_date:
            return False
        if self.config.end_date and dt > self.config.end_date:
            return False
        return True

    def fetch_float_index(self) -> List[Dict]:
        """Fetch and filter ARGO global profile index."""
        logger.info("Fetching ARGO global profile index...")
        logger.info(
            "Filters -> region=%s, bbox=%s, start_date=%s, end_date=%s, index_limit=%s",
            self.config.region,
            self._active_bbox(),
            self.config.start_date.isoformat() if self.config.start_date else None,
            self.config.end_date.isoformat() if self.config.end_date else None,
            self.config.index_limit,
        )

        index_url = f"{ARGO_GDAC_URL}/ar_index_global_prof.txt"
        response = requests.get(index_url, timeout=self.config.request_timeout)
        response.raise_for_status()

        floats: List[Dict] = []
        parsed_lines = 0

        for raw_line in response.text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            values = [v.strip() for v in line.split(",")]
            if len(values) < 4:
                continue

            parsed_lines += 1
            if self.config.index_limit and parsed_lines > self.config.index_limit:
                break

            try:
                lat = float(values[2])
                lon = float(values[3])
            except Exception:
                continue

            if not self._is_in_bbox(lat, lon):
                continue

            idx_date = self._parse_index_datetime(values[1])
            if not self._date_in_range(idx_date):
                continue

            floats.append(
                {
                    "file": values[0],
                    "date": values[1],
                    "latitude": lat,
                    "longitude": lon,
                    "ocean": values[4] if len(values) > 4 else None,
                    "profiler_type": values[5] if len(values) > 5 else None,
                    "institution": values[6] if len(values) > 6 else None,
                    "date_update": values[7] if len(values) > 7 else None,
                    "parsed_date": idx_date,
                }
            )

        logger.info("Index fetch complete. Candidate files after filter: %s", len(floats))
        return floats

    def download_netcdf_file(self, file_path: str) -> Optional[str]:
        """Download or reuse cached NetCDF file."""
        safe_name = file_path.replace("/", "_")
        local_path = os.path.join(self.config.cache_dir, safe_name)

        if os.path.exists(local_path) and not self.config.force_redownload:
            return local_path

        url = f"{ARGO_GDAC_URL}/{file_path}"
        try:
            response = requests.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(response.content)
            return local_path
        except Exception as e:
            logger.warning("Failed to download %s: %s", file_path, e)
            return None

    def parse_netcdf_profile(self, file_path: str) -> Optional[Dict]:
        """Parse ARGO profile NetCDF into a normalized structure."""
        dataset = None
        try:
            dataset = nc.Dataset(file_path, "r")

            platform_number = self._decode_char_array(dataset.variables["PLATFORM_NUMBER"][:])
            cycle_number = int(np.ma.filled(dataset.variables["CYCLE_NUMBER"][0], 0))

            latitude = float(np.ma.filled(dataset.variables["LATITUDE"][0], np.nan))
            longitude = float(np.ma.filled(dataset.variables["LONGITUDE"][0], np.nan))
            juld = float(np.ma.filled(dataset.variables["JULD"][0], np.nan))
            profile_date = datetime(1950, 1, 1) + timedelta(days=juld)

            pressure_raw = dataset.variables["PRES"][:]
            temperature_raw = dataset.variables["TEMP"][:]
            salinity_raw = dataset.variables["PSAL"][:]

            pressure = np.array(pressure_raw[0] if pressure_raw.ndim > 1 else pressure_raw, dtype=float)
            temperature = np.array(temperature_raw[0] if temperature_raw.ndim > 1 else temperature_raw, dtype=float)
            salinity = np.array(salinity_raw[0] if salinity_raw.ndim > 1 else salinity_raw, dtype=float)

            temp_qc = None
            sal_qc = None
            if "TEMP_QC" in dataset.variables:
                raw_temp_qc = dataset.variables["TEMP_QC"][:]
                temp_qc = raw_temp_qc[0] if raw_temp_qc.ndim > 1 else raw_temp_qc
            if "PSAL_QC" in dataset.variables:
                raw_sal_qc = dataset.variables["PSAL_QC"][:]
                sal_qc = raw_sal_qc[0] if raw_sal_qc.ndim > 1 else raw_sal_qc

            valid = np.isfinite(pressure) & (np.isfinite(temperature) | np.isfinite(salinity))

            measurements = []
            for idx in np.where(valid)[0]:
                t_val = float(temperature[idx]) if np.isfinite(temperature[idx]) else None
                s_val = float(salinity[idx]) if np.isfinite(salinity[idx]) else None
                p_val = float(pressure[idx])

                tqc_val = None
                sqc_val = None
                if temp_qc is not None:
                    raw = self._decode_char_array(temp_qc[idx])
                    tqc_val = int(raw) if raw.isdigit() else None
                if sal_qc is not None:
                    raw = self._decode_char_array(sal_qc[idx])
                    sqc_val = int(raw) if raw.isdigit() else None

                measurements.append(
                    {
                        "pressure": p_val,
                        "depth": p_val,  # Approximation for ARGO profile quick loading.
                        "temperature": t_val,
                        "salinity": s_val,
                        "temp_qc": tqc_val,
                        "psal_qc": sqc_val,
                    }
                )

            if not measurements:
                return None

            return {
                "wmo_number": platform_number,
                "cycle_number": cycle_number,
                "latitude": latitude,
                "longitude": longitude,
                "profile_date": profile_date,
                "position_qc": None,
                "data_mode": None,
                "measurements": measurements,
            }
        except Exception as e:
            logger.warning("Failed parsing NetCDF %s: %s", file_path, e)
            return None
        finally:
            if dataset is not None:
                dataset.close()

    def insert_float(self, wmo_number: str, platform_type: str = "APEX") -> Optional[int]:
        """Insert or fetch float id."""
        try:
            result = self.session.execute(
                text("SELECT id FROM argo_floats WHERE wmo_number = :wmo"),
                {"wmo": wmo_number},
            ).first()
            if result:
                return int(result[0])

            result = self.session.execute(
                text(
                    """
                    INSERT INTO argo_floats (wmo_number, platform_type, status, ocean_basin)
                    VALUES (:wmo, :platform_type, 'ACTIVE', :ocean_basin)
                    RETURNING id
                    """
                ),
                {
                    "wmo": wmo_number,
                    "platform_type": platform_type,
                    "ocean_basin": "Indian Ocean" if self.config.region == "indian" else "Unknown",
                },
            )
            self.session.commit()
            return int(result.first()[0])
        except Exception as e:
            self.session.rollback()
            logger.error("Failed inserting float %s: %s", wmo_number, e)
            return None

    def insert_profile(self, profile_data: Dict) -> Optional[int]:
        """Insert profile + measurements."""
        try:
            float_id = self.insert_float(profile_data["wmo_number"])
            if not float_id:
                return None

            existing = self.session.execute(
                text(
                    """
                    SELECT id FROM argo_profiles
                    WHERE wmo_number = :wmo AND cycle_number = :cycle
                    """
                ),
                {"wmo": profile_data["wmo_number"], "cycle": profile_data["cycle_number"]},
            ).first()
            if existing:
                return int(existing[0])

            inserted = self.session.execute(
                text(
                    """
                    INSERT INTO argo_profiles
                    (float_id, wmo_number, cycle_number, profile_date, latitude, longitude, position_qc, data_mode)
                    VALUES (:float_id, :wmo, :cycle, :profile_date, :latitude, :longitude, :position_qc, :data_mode)
                    RETURNING id
                    """
                ),
                {
                    "float_id": float_id,
                    "wmo": profile_data["wmo_number"],
                    "cycle": profile_data["cycle_number"],
                    "profile_date": profile_data["profile_date"],
                    "latitude": profile_data["latitude"],
                    "longitude": profile_data["longitude"],
                    "position_qc": profile_data.get("position_qc"),
                    "data_mode": profile_data.get("data_mode"),
                },
            )
            profile_id = int(inserted.first()[0])

            for measurement in profile_data["measurements"]:
                self.session.execute(
                    text(
                        """
                        INSERT INTO argo_measurements
                        (profile_id, pressure, depth, temperature, temperature_qc, salinity, salinity_qc)
                        VALUES (:profile_id, :pressure, :depth, :temperature, :temperature_qc, :salinity, :salinity_qc)
                        """
                    ),
                    {
                        "profile_id": profile_id,
                        "pressure": measurement["pressure"],
                        "depth": measurement.get("depth"),
                        "temperature": measurement.get("temperature"),
                        "temperature_qc": measurement.get("temp_qc"),
                        "salinity": measurement.get("salinity"),
                        "salinity_qc": measurement.get("psal_qc"),
                    },
                )

            self.session.commit()
            return profile_id
        except Exception as e:
            self.session.rollback()
            logger.warning(
                "Failed inserting profile %s/%s: %s",
                profile_data.get("wmo_number"),
                profile_data.get("cycle_number"),
                e,
            )
            return None

    def run_ingestion(self) -> Dict[str, int]:
        """Run full ingestion flow and return ingestion summary metrics."""
        logger.info("Starting ARGO ingestion...")
        start_time = time.perf_counter()
        candidates = self.fetch_float_index()
        if not candidates:
            logger.warning("No candidates after filtering.")
            return {
                "candidate_count": 0,
                "scanned": 0,
                "processed": 0,
                "inserted": 0,
                "failed": 0,
                "duration_seconds": 0,
            }

        max_profiles = self.config.max_profiles or len(candidates)
        processed = 0
        inserted = 0
        failed = 0
        scanned = 0

        for idx, item in enumerate(candidates, start=1):
            scanned += 1
            if processed >= max_profiles:
                break

            local_file = self.download_netcdf_file(item["file"])
            if not local_file:
                failed += 1
                continue

            profile_data = self.parse_netcdf_profile(local_file)
            if not profile_data:
                failed += 1
                continue

            inserted_id = self.insert_profile(profile_data)
            processed += 1
            if inserted_id:
                inserted += 1
            else:
                failed += 1

            if idx % 25 == 0:
                logger.info("Progress: scanned=%s processed=%s inserted=%s", idx, processed, inserted)

            if self.config.sleep_seconds > 0:
                time.sleep(self.config.sleep_seconds)

        logger.info(
            "Ingestion complete. scanned=%s processed=%s inserted=%s",
            min(len(candidates), max_profiles),
            processed,
            inserted,
        )
        duration_seconds = round(time.perf_counter() - start_time, 2)
        return {
            "candidate_count": len(candidates),
            "scanned": min(scanned, len(candidates)),
            "processed": processed,
            "inserted": inserted,
            "failed": failed,
            "duration_seconds": duration_seconds,
        }


def _parse_date_arg(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ARGO ingestion pipeline")
    parser.add_argument("--region", choices=["indian", "global", "custom"], default="indian")
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Bounding box for custom region (lon/lat)",
    )
    parser.add_argument("--start-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--index-limit", type=int, default=5000, help="Max index lines to scan")
    parser.add_argument("--max-profiles", type=int, default=500, help="Max profiles to process")
    parser.add_argument("--cache-dir", type=str, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    parser.add_argument("--force-redownload", action="store_true")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> IngestionConfig:
    bbox = tuple(args.bbox) if args.bbox else None
    if args.region == "custom" and not bbox:
        raise ValueError("--region custom requires --bbox MIN_LON MIN_LAT MAX_LON MAX_LAT")

    return IngestionConfig(
        region=args.region,
        bbox=bbox,
        start_date=_parse_date_arg(args.start_date),
        end_date=_parse_date_arg(args.end_date),
        index_limit=args.index_limit if args.index_limit and args.index_limit > 0 else None,
        max_profiles=args.max_profiles if args.max_profiles and args.max_profiles > 0 else None,
        cache_dir=args.cache_dir,
        request_timeout=args.request_timeout,
        sleep_seconds=max(0.0, args.sleep_seconds),
        force_redownload=args.force_redownload,
    )


if __name__ == "__main__":
    cli_args = parse_args()
    cfg = build_config(cli_args)
    ingestion = ArgoDataIngestion(cfg)
    ingestion.run_ingestion()

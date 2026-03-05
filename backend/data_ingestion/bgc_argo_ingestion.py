"""
BGC-Argo ingestion utility.

Loads BGC profile metadata (and optional parameter means) into `bgc_profiles`.
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Iterable, Optional

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

try:
    import xarray as xr
except Exception:
    xr = None

load_dotenv()


@dataclass
class Record:
    wmo_number: str
    cycle_number: Optional[int]
    profile_date: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    source_file: str
    chlorophyll: Optional[float] = None
    nitrate: Optional[float] = None
    oxygen: Optional[float] = None
    ph: Optional[float] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest BGC-Argo index and optional profile parameter means")
    parser.add_argument(
        "--index-url",
        default=os.getenv("BGC_INDEX_URL", "https://data-argo.ifremer.fr/argo_synthetic-profile_index.txt"),
        help="BGC synthetic profile index URL",
    )
    parser.add_argument("--start-date", default=None, help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Inclusive YYYY-MM-DD")
    parser.add_argument("--bbox", nargs=4, type=float, default=None, metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"))
    parser.add_argument("--max-profiles", type=int, default=2000)
    parser.add_argument(
        "--include-biogeochem",
        action="store_true",
        help="Download selected NetCDF files and compute mean CHLA/NITRATE/OXYGEN/pH",
    )
    parser.add_argument("--timeout", type=int, default=20)
    return parser.parse_args()


def _parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _parse_date(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d%H%M%S", "%Y%m%d"):
        try:
            dt = datetime.strptime(value[: len(fmt.replace("%", ""))], fmt)
            return dt.isoformat()
        except Exception:
            continue
    try:
        return datetime.fromisoformat(value).isoformat()
    except Exception:
        return None


def _extract_wmo(file_path: str) -> str:
    match = re.search(r"/(\d{7})/", file_path)
    if match:
        return match.group(1)
    match = re.search(r"(\d{7})", file_path)
    if match:
        return match.group(1)
    return "unknown"


def _extract_cycle(file_path: str) -> Optional[int]:
    match = re.search(r"_(\d{3,4})[A-Z]?\.nc$", file_path)
    if not match:
        return None
    try:
        return int(match.group(1))
    except Exception:
        return None


def _in_date_range(date_iso: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> bool:
    if not date_iso:
        return True
    if start_date and date_iso[:10] < start_date:
        return False
    if end_date and date_iso[:10] > end_date:
        return False
    return True


def _in_bbox(lat: Optional[float], lon: Optional[float], bbox: Optional[list[float]]) -> bool:
    if not bbox or lat is None or lon is None:
        return True
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def parse_index_rows(content: str) -> Iterable[Record]:
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        file_path = parts[0]
        date_iso = _parse_date(parts[1]) if len(parts) > 1 else None
        lat = _parse_float(parts[2]) if len(parts) > 2 else None
        lon = _parse_float(parts[3]) if len(parts) > 3 else None
        yield Record(
            wmo_number=_extract_wmo(file_path),
            cycle_number=_extract_cycle(file_path),
            profile_date=date_iso,
            latitude=lat,
            longitude=lon,
            source_file=file_path,
        )


def _dataset_url(index_url: str, source_file: str) -> str:
    base = index_url.rsplit("/", 1)[0]
    return f"{base}/{source_file}"


def enrich_biogeochem(record: Record, dataset_url: str, timeout: int) -> Record:
    if xr is None:
        return record
    try:
        response = requests.get(dataset_url, timeout=timeout)
        response.raise_for_status()
        with xr.open_dataset(BytesIO(response.content), engine="h5netcdf") as ds:  # type: ignore[arg-type]
            # Variable names vary by source; try common aliases.
            for field, aliases in [
                ("chlorophyll", ["CHLA", "CHLA_ADJUSTED"]),
                ("nitrate", ["NITRATE", "NITRATE_ADJUSTED"]),
                ("oxygen", ["DOXY", "DOXY_ADJUSTED"]),
                ("ph", ["PH_IN_SITU_TOTAL", "PH_IN_SITU_TOTAL_ADJUSTED"]),
            ]:
                value = None
                for alias in aliases:
                    if alias in ds:
                        arr = ds[alias].values
                        try:
                            value = float(arr[~(arr != arr)].mean())  # NaN-safe
                        except Exception:
                            value = None
                        break
                setattr(record, field, value)
    except Exception:
        return record
    return record


def ensure_table(db: Session):
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS bgc_profiles (
                id BIGSERIAL PRIMARY KEY,
                wmo_number VARCHAR(32) NOT NULL,
                cycle_number INTEGER,
                profile_date TIMESTAMP,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                chlorophyll DOUBLE PRECISION,
                nitrate DOUBLE PRECISION,
                oxygen DOUBLE PRECISION,
                ph DOUBLE PRECISION,
                source_file VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_bgc_wmo_date ON bgc_profiles (wmo_number, profile_date DESC)"))
    db.commit()


def insert_records(db: Session, records: list[Record]) -> int:
    inserted = 0
    for rec in records:
        db.execute(
            text(
                """
                INSERT INTO bgc_profiles (
                    wmo_number, cycle_number, profile_date, latitude, longitude,
                    chlorophyll, nitrate, oxygen, ph, source_file
                )
                VALUES (
                    :wmo_number, :cycle_number, :profile_date, :latitude, :longitude,
                    :chlorophyll, :nitrate, :oxygen, :ph, :source_file
                )
                """
            ),
            {
                "wmo_number": rec.wmo_number,
                "cycle_number": rec.cycle_number,
                "profile_date": rec.profile_date,
                "latitude": rec.latitude,
                "longitude": rec.longitude,
                "chlorophyll": rec.chlorophyll,
                "nitrate": rec.nitrate,
                "oxygen": rec.oxygen,
                "ph": rec.ph,
                "source_file": rec.source_file,
            },
        )
        inserted += 1
    db.commit()
    return inserted


def main() -> int:
    args = parse_args()
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)

    engine = create_engine(database_url)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    print(f"Fetching BGC index from: {args.index_url}")
    response = requests.get(args.index_url, timeout=args.timeout)
    response.raise_for_status()

    selected: list[Record] = []
    for record in parse_index_rows(response.text):
        if not _in_date_range(record.profile_date, args.start_date, args.end_date):
            continue
        if not _in_bbox(record.latitude, record.longitude, args.bbox):
            continue
        selected.append(record)
        if len(selected) >= args.max_profiles:
            break

    if args.include_biogeochem and selected:
        print("Downloading sample BGC NetCDF files for parameter enrichment...")
        for idx, rec in enumerate(selected, start=1):
            url = _dataset_url(args.index_url, rec.source_file)
            selected[idx - 1] = enrich_biogeochem(rec, url, args.timeout)
            if idx % 25 == 0:
                print(f"  enriched {idx}/{len(selected)} records")

    db = session_local()
    try:
        ensure_table(db)
        inserted = insert_records(db, selected)
        print(f"Inserted {inserted} BGC profile rows.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


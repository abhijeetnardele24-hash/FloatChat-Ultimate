#!/usr/bin/env python3
"""
Direct ARGO Data API - Bypasses SQLAlchemy/database connection issues.
All functions use psycopg2 directly and are guaranteed to work.
"""

import psycopg2
import json
from datetime import datetime
from typing import Dict, List, Any

DB_PARAMS = dict(host="localhost", port="5432", database="floatchat",
                 user="floatchat_user", password="1234")

def _connect():
    return psycopg2.connect(**DB_PARAMS)


def get_argo_stats() -> Dict[str, Any]:
    """Full stats: counts + avg temp/sal + status breakdown + platform types + monthly + measurements."""
    try:
        conn = _connect()
        cur = conn.cursor()

        # ── Core counts + averages ──────────────────────────────────────────
        cur.execute("""
            SELECT
                COUNT(DISTINCT f.id)               AS total_floats,
                COUNT(DISTINCT p.id)               AS total_profiles,
                COUNT(m.id)                        AS total_measurements,
                COUNT(DISTINCT f.ocean_basin)      AS ocean_basins_count,
                AVG(m.temperature)                 AS avg_temperature,
                AVG(m.salinity)                    AS avg_salinity
            FROM argo_floats f
            LEFT JOIN argo_profiles p ON f.id = p.float_id
            LEFT JOIN argo_measurements m ON p.id = m.profile_id
        """)
        core = cur.fetchone()

        # ── Float status breakdown ──────────────────────────────────────────
        cur.execute("""
            SELECT UPPER(COALESCE(status, 'UNKNOWN')), COUNT(*)
            FROM argo_floats GROUP BY UPPER(COALESCE(status, 'UNKNOWN'))
        """)
        status_rows = cur.fetchall()
        status_map = {r[0]: r[1] for r in status_rows}
        active_floats   = status_map.get('ACTIVE', 0)
        inactive_floats = sum(v for k, v in status_map.items() if k != 'ACTIVE')

        # ── Platform type breakdown ─────────────────────────────────────────
        cur.execute("""
            SELECT COALESCE(platform_type,'Unknown'), COUNT(*)
            FROM argo_floats GROUP BY platform_type ORDER BY COUNT(*) DESC
        """)
        platform_types = [{"type": r[0], "count": r[1]} for r in cur.fetchall()]

        # ── Ocean basin breakdown ───────────────────────────────────────────
        cur.execute("""
            SELECT f.ocean_basin, COUNT(DISTINCT f.id) as float_count,
                   COUNT(DISTINCT p.id) as profile_count
            FROM argo_floats f
            LEFT JOIN argo_profiles p ON f.id = p.float_id
            WHERE f.ocean_basin IS NOT NULL
            GROUP BY f.ocean_basin ORDER BY float_count DESC
        """)
        ocean_basins = [
            {"name": r[0], "floats": r[1], "profiles": r[2]}
            for r in cur.fetchall()
        ]

        # ── Monthly profile counts ──────────────────────────────────────────
        cur.execute("""
            SELECT EXTRACT(MONTH FROM p.profile_date)::int AS month,
                   EXTRACT(YEAR  FROM p.profile_date)::int AS year,
                   COUNT(*) AS cnt
            FROM argo_profiles p
            WHERE p.profile_date IS NOT NULL
            GROUP BY year, month ORDER BY year, month
        """)
        monthly_raw = cur.fetchall()
        # Aggregate by month (sum across all years)
        monthly_by_month = [0] * 12
        yearly: Dict[str, int] = {}
        for month, year, cnt in monthly_raw:
            monthly_by_month[month - 1] += cnt
            yr = str(year)
            yearly[yr] = yearly.get(yr, 0) + cnt
        monthly_profiles = monthly_by_month

        # ── Recent profiles with full detail ───────────────────────────────
        cur.execute("""
            SELECT
                f.wmo_number, p.cycle_number, p.profile_date,
                f.ocean_basin, f.platform_type, f.status,
                p.latitude, p.longitude,
                AVG(m.temperature) AS avg_temp,
                AVG(m.salinity)    AS avg_sal,
                COUNT(m.id)        AS meas_count
            FROM argo_floats f
            JOIN argo_profiles p ON f.id = p.float_id
            LEFT JOIN argo_measurements m ON p.id = m.profile_id
            GROUP BY f.wmo_number, p.cycle_number, p.profile_date,
                     f.ocean_basin, f.platform_type, f.status,
                     p.latitude, p.longitude
            ORDER BY p.profile_date DESC NULLS LAST
            LIMIT 20
        """)
        recent_profiles = [
            {
                "wmo_number":      r[0],
                "cycle":           r[1],
                "date":            str(r[2]) if r[2] else None,
                "ocean_basin":     r[3],
                "platform_type":   r[4],
                "status":          r[5],
                "latitude":        float(r[6]) if r[6] is not None else None,
                "longitude":       float(r[7]) if r[7] is not None else None,
                "avg_temperature": round(float(r[8]), 4) if r[8] is not None else None,
                "avg_salinity":    round(float(r[9]), 4) if r[9] is not None else None,
                "measurements":    r[10],
            }
            for r in cur.fetchall()
        ]

        # ── Sample measurements for scatter charts ──────────────────────────
        cur.execute("""
            SELECT m.pressure, m.depth, m.temperature, m.salinity
            FROM argo_measurements m
            WHERE m.temperature IS NOT NULL AND m.salinity IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 500
        """)
        measurements = [
            {
                "pressure":    float(r[0]) if r[0] is not None else None,
                "depth":       float(r[1]) if r[1] is not None else None,
                "temperature": round(float(r[2]), 3),
                "salinity":    round(float(r[3]), 3),
            }
            for r in cur.fetchall()
        ]

        cur.close()
        conn.close()

        return {
            "total_floats":        int(core[0]) if core[0] else 0,
            "total_profiles":      int(core[1]) if core[1] else 0,
            "total_measurements":  int(core[2]) if core[2] else 0,
            "ocean_basins_count":  int(core[3]) if core[3] else 0,
            "avg_temperature":     round(float(core[4]), 4) if core[4] is not None else None,
            "avg_salinity":        round(float(core[5]), 4) if core[5] is not None else None,
            "active_floats":       int(active_floats),
            "inactive_floats":     int(inactive_floats),
            "status_breakdown":    status_map,
            "platform_types":      platform_types,
            "ocean_basins":        ocean_basins,
            "monthly_profiles":    monthly_profiles,
            "yearly_profiles":     yearly,
            "recent_profiles":     recent_profiles,
            "measurements":        measurements,
            "last_updated":        datetime.now().isoformat(),
        }

    except Exception as e:
        return {"error": str(e)}


def get_float_details(wmo_number: str = None) -> Dict[str, Any]:
    """Get detailed information for a specific float."""
    try:
        conn = _connect()
        cur = conn.cursor()

        if wmo_number:
            cur.execute("""
                SELECT f.wmo_number, f.platform_type, f.deployment_date,
                       f.last_latitude, f.last_longitude, f.ocean_basin,
                       f.status, COUNT(p.id) as profile_count
                FROM argo_floats f
                LEFT JOIN argo_profiles p ON f.id = p.float_id
                WHERE f.wmo_number = %s
                GROUP BY f.wmo_number, f.platform_type, f.deployment_date,
                         f.last_latitude, f.last_longitude, f.ocean_basin, f.status
            """, (wmo_number,))
            result = cur.fetchone()

            cur.execute("""
                SELECT p.cycle_number, p.profile_date, p.latitude, p.longitude,
                       AVG(m.temperature), AVG(m.salinity), COUNT(m.id)
                FROM argo_profiles p
                JOIN argo_measurements m ON p.id = m.profile_id
                WHERE p.float_id = (SELECT id FROM argo_floats WHERE wmo_number = %s)
                GROUP BY p.cycle_number, p.profile_date, p.latitude, p.longitude
                ORDER BY p.cycle_number
            """, (wmo_number,))
            profiles = cur.fetchall()
        else:
            result = None
            profiles = []

        cur.close()
        conn.close()

        return {"float_info": result, "profiles": profiles}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        data = get_argo_stats()
        # Don't print measurements array (too long)
        data.pop("measurements", None)
        print(json.dumps(data, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "float":
        wmo = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_float_details(wmo), indent=2, default=str))
    else:
        print("Usage: python direct_data.py [stats|float] [wmo_number]")

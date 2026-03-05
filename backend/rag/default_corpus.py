"""Default ocean-study corpus used when vector services are unavailable."""

from __future__ import annotations

from typing import Dict, List


def get_default_corpus() -> List[Dict[str, str]]:
    return [
        {
            "title": "ARGO Program Overview",
            "source": "https://argo.ucsd.edu/",
            "content": (
                "Argo is a global array of autonomous profiling floats that measure "
                "temperature and salinity from about 2000 m depth to the ocean surface. "
                "Floats typically cycle every 10 days and transmit profiles through satellite links."
            ),
        },
        {
            "title": "ARGO Quality Control",
            "source": "https://argo.ucsd.edu/data/how-to-use-argo-files/",
            "content": (
                "ARGO profile variables include quality-control flags. Low QC flag values "
                "generally indicate better data quality. Researchers often apply conservative "
                "filters such as QC less than or equal to 2 for analysis."
            ),
        },
        {
            "title": "Temperature-Salinity and Density",
            "source": "https://en.wikipedia.org/wiki/Seawater_density",
            "content": (
                "Seawater density is controlled mainly by temperature, salinity, and pressure. "
                "Higher salinity and lower temperature increase density, which influences "
                "stratification and large-scale circulation."
            ),
        },
        {
            "title": "Mixed Layer and Stratification",
            "source": "https://en.wikipedia.org/wiki/Mixed_layer",
            "content": (
                "The mixed layer is the near-surface layer where turbulence homogenizes "
                "temperature and salinity. Strong stratification inhibits vertical mixing "
                "and changes heat and freshwater exchange with deeper waters."
            ),
        },
        {
            "title": "Thermohaline Circulation Basics",
            "source": "https://en.wikipedia.org/wiki/Thermohaline_circulation",
            "content": (
                "Thermohaline circulation refers to large-scale ocean circulation driven "
                "by density differences caused by temperature and salinity variations. "
                "It redistributes heat, freshwater, and dissolved properties globally."
            ),
        },
        {
            "title": "ARGO Data Modes",
            "source": "https://argo.ucsd.edu/data/argo-data-products/",
            "content": (
                "ARGO profile data modes include real-time and delayed-mode processing. "
                "Delayed-mode products usually provide improved quality after expert review "
                "and are preferred for climate-quality studies."
            ),
        },
        {
            "title": "Pressure and Depth Relationship",
            "source": "https://www.teos-10.org/",
            "content": (
                "Oceanographic profiles often use pressure as the vertical coordinate. "
                "Pressure can be converted to approximate depth using TEOS-10 equations, "
                "with latitude effects included for higher accuracy."
            ),
        },
        {
            "title": "ARGO Coverage and Applications",
            "source": "https://argo.ucsd.edu/about/status/",
            "content": (
                "The global Argo network supports climate monitoring, ocean state estimation, "
                "and operational oceanography. Regional subsets can be analyzed by basin, date range, "
                "depth range, and measurement quality criteria."
            ),
        },
    ]


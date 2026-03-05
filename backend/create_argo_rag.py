#!/usr/bin/env python3
"""
Create ARGO RAG Knowledge Base
Generates oceanographic knowledge documents from ARGO data for RAG system
"""

import psycopg2
import json
from datetime import datetime
from pathlib import Path

def create_argo_rag_corpus():
    """Create RAG corpus from ARGO database"""
    
    # Connect to database
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="floatchat",
        user="floatchat_user",
        password="1234"
    )
    cursor = conn.cursor()
    
    try:
        # Get ocean basin statistics
        cursor.execute("""
            SELECT 
                af.ocean_basin,
                COUNT(DISTINCT af.id) as float_count,
                COUNT(ap.id) as profile_count,
                COUNT(am.id) as measurement_count,
                AVG(am.temperature) as avg_temp,
                AVG(am.salinity) as avg_sal,
                MIN(am.temperature) as min_temp,
                MAX(am.temperature) as max_temp,
                MIN(am.salinity) as min_sal,
                MAX(am.salinity) as max_sal,
                MIN(ap.profile_date) as earliest_date,
                MAX(ap.profile_date) as latest_date
            FROM argo_floats af
            JOIN argo_profiles ap ON af.id = ap.float_id
            JOIN argo_measurements am ON ap.id = am.profile_id
            WHERE am.temperature IS NOT NULL AND am.salinity IS NOT NULL
            GROUP BY af.ocean_basin
            ORDER BY float_count DESC
        """)
        
        results = cursor.fetchall()
        
        # Generate RAG documents
        rag_documents = []
        
        for row in results:
            ocean_basin = row[0]
            stats = {
                'float_count': row[1],
                'profile_count': row[2],
                'measurement_count': row[3],
                'avg_temp': round(row[4], 2) if row[4] else 0,
                'avg_sal': round(row[5], 2) if row[5] else 0,
                'min_temp': round(row[6], 2) if row[6] else 0,
                'max_temp': round(row[7], 2) if row[7] else 0,
                'min_sal': round(row[8], 2) if row[8] else 0,
                'max_sal': round(row[9], 2) if row[9] else 0,
                'earliest_date': str(row[10]) if row[10] else "Unknown",
                'latest_date': str(row[11]) if row[11] else "Unknown"
            }
            
            # Create knowledge documents for each ocean basin
            documents = create_ocean_basin_documents(ocean_basin, stats)
            rag_documents.extend(documents)
        
        # Add general ARGO knowledge
        rag_documents.extend(create_general_argo_knowledge())
        
        # Save to file
        output_dir = Path("rag/corpus")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "argo_enhanced_corpus.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rag_documents, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created {len(rag_documents)} RAG documents for {len(results)} ocean basins")
        print(f"📁 Saved to: {output_file}")
        
        # Show sample documents
        print("\n📄 Sample RAG Documents:")
        for i, doc in enumerate(rag_documents[:3]):
            print(f"\n{i+1}. {doc['title']}")
            print(f"   Keywords: {doc['keywords']}")
            print(f"   Content: {doc['content'][:150]}...")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_ocean_basin_documents(ocean_basin, stats):
    """Create RAG documents for a specific ocean basin"""
    documents = []
    
    # Temperature analysis document
    temp_doc = {
        "title": f"Temperature Analysis - {ocean_basin}",
        "source": f"ARGO Database Analysis - {datetime.now().strftime('%Y-%m-%d')}",
        "content": f"""
Temperature analysis for {ocean_basin} based on ARGO float observations:
- Average temperature: {stats['avg_temp']}°C
- Temperature range: {stats['min_temp']}°C to {stats['max_temp']}°C
- Data coverage: {stats['profile_count']} profiles with {stats['measurement_count']} measurements
- Observation period: {stats['earliest_date']} to {stats['latest_date']}
- Scientific significance: This temperature distribution indicates thermal structure and ocean dynamics in {ocean_basin}.
        """.strip(),
        "keywords": ["temperature", "ocean", "thermal structure", "ARGO", ocean_basin.lower()],
        "score": 1.0
    }
    documents.append(temp_doc)
    
    # Salinity analysis document
    sal_doc = {
        "title": f"Salinity Analysis - {ocean_basin}",
        "source": f"ARGO Database Analysis - {datetime.now().strftime('%Y-%m-%d')}",
        "content": f"""
Salinity analysis for {ocean_basin} based on ARGO float observations:
- Average salinity: {stats['avg_sal']} PSU
- Salinity range: {stats['min_sal']} PSU to {stats['max_sal']} PSU
- Data coverage: {stats['profile_count']} profiles with {stats['measurement_count']} measurements
- Observation period: {stats['earliest_date']} to {stats['latest_date']}
- Scientific significance: Salinity patterns reveal water mass characteristics, freshwater influence, and ocean circulation in {ocean_basin}.
        """.strip(),
        "keywords": ["salinity", "ocean", "water mass", "ARGO", ocean_basin.lower()],
        "score": 1.0
    }
    documents.append(sal_doc)
    
    # Regional oceanography document
    ocean_doc = {
        "title": f"Regional Oceanography - {ocean_basin}",
        "source": f"ARGO Database Analysis - {datetime.now().strftime('%Y-%m-%d')}",
        "content": f"""
Regional oceanographic summary for {ocean_basin} from ARGO observations:
- Monitoring assets: {stats['float_count']} active floats
- Profile density: {stats['profile_count']} vertical profiles
- Temperature-salinity characteristics: T range {stats['min_temp']}-{stats['max_temp']}°C, S range {stats['min_sal']}-{stats['max_sal']} PSU
- Temporal coverage: {stats['earliest_date']} to {stats['latest_date']}
- Research applications: Climate monitoring, ocean circulation studies, marine ecosystem assessment, and climate change impact analysis in {ocean_basin}.
        """.strip(),
        "keywords": ["oceanography", "regional", "climate", "circulation", ocean_basin.lower()],
        "score": 1.0
    }
    documents.append(ocean_doc)
    
    return documents

def create_general_argo_knowledge():
    """Create general ARGO program knowledge documents"""
    documents = []
    
    # ARGO program overview
    argo_overview = {
        "title": "ARGO Program Overview and Scientific Impact",
        "source": "ARGO Program Documentation",
        "content": """
The ARGO (Array for Real-time Geostrophic Oceanography) program is a global array of over 3,900 free-drifting profiling floats that measure temperature and salinity of the upper ocean. Key aspects:

- Coverage: Global ocean with approximately one float every 3° latitude/longitude
- Depth range: Surface to 2000 meters
- Measurement frequency: Every 10 days per float
- Data types: Temperature, salinity, pressure, and optional bio-geochemical parameters
- Scientific impact: Enables real-time ocean monitoring, climate change detection, weather forecasting, and ocean circulation studies
- Applications: Climate research, ocean modeling, marine ecosystem management, and operational oceanography
        """.strip(),
        "keywords": ["ARGO", "ocean monitoring", "climate", "temperature", "salinity", "global"],
        "score": 1.0
    }
    documents.append(argo_overview)
    
    # Data interpretation guide
    interpretation_guide = {
        "title": "ARGO Data Interpretation and Analysis Methods",
        "source": "Oceanographic Data Analysis Guide",
        "content": """
Interpreting ARGO float data requires understanding oceanographic principles:

Temperature Profiles:
- Surface layer: Mixed layer with uniform temperature
- Thermocline: Rapid temperature change with depth (typically 100-1000m)
- Deep layer: Stable cold temperatures below thermocline
- Seasonal variation: Surface temperatures change seasonally, deep waters remain stable

Salinity Profiles:
- Surface salinity: Affected by evaporation, precipitation, river runoff
- Halocline: Salinity gradient layer, often coincides with thermocline
- Deep salinity: Relatively stable around 34.6-34.9 PSU globally
- Regional variations: High salinity in subtropical gyres, low near coasts and poles

T-S Diagrams:
- Water mass identification: Different water masses have characteristic T-S signatures
- Mixing patterns: Curved lines indicate water mass mixing
- Ocean currents: T-S properties trace water mass origins and pathways
        """.strip(),
        "keywords": ["data interpretation", "temperature profiles", "salinity profiles", "TS diagrams", "oceanography"],
        "score": 1.0
    }
    documents.append(interpretation_guide)
    
    # Climate change relevance
    climate_relevance = {
        "title": "ARGO Data in Climate Change Research",
        "source": "Climate Research Applications",
        "content": """
ARGO float data is critical for climate change monitoring and research:

Ocean Heat Content:
- ARGO measures temperature changes throughout the water column
- Ocean absorbs over 90% of excess heat from global warming
- Heat content trends provide definitive evidence of climate change
- Regional variations show different warming rates across ocean basins

Sea Level Rise:
- Temperature measurements track thermal expansion of seawater
- Combined with satellite altimetry for comprehensive sea level assessment
- Regional sea level variations identified through ARGO density measurements

Carbon Cycle:
- Salinity and temperature data inform ocean carbon uptake calculations
- Ocean acidification monitoring through complementary measurements
- Biological pump efficiency assessment through temperature-salinity relationships

Weather Prediction:
- Real-time ARGO data improves weather forecast models
- Ocean temperature influences atmospheric circulation patterns
- Seasonal forecasting benefits from accurate ocean state initialization
        """.strip(),
        "keywords": ["climate change", "ocean heat content", "sea level", "carbon cycle", "weather prediction"],
        "score": 1.0
    }
    documents.append(climate_relevance)
    
    return documents

if __name__ == "__main__":
    create_argo_rag_corpus()

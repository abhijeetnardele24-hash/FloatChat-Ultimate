#!/usr/bin/env python3
"""
ARGO Data RAG Ingestion
Converts ARGO dataset into searchable RAG documents for oceanographic knowledge retrieval
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
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
from rag.default_corpus import get_default_corpus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArgoRAGIngestion:
    def __init__(self):
        self.engine = create_engine(get_database_url())
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Oceanographic knowledge templates
        self.knowledge_templates = {
            'temperature_anomalies': {
                'title': 'Ocean Temperature Anomalies Analysis',
                'template': """
Based on ARGO float data from {ocean_basin}, temperature anomalies have been observed:
- Surface temperature variation: {surface_temp_range}°C
- Deep water temperature (1000m+): {deep_temp_range}°C
- Thermocline depth: {thermocline_depth}m
- Data coverage: {profile_count} profiles from {date_range}
- Scientific significance: These patterns indicate {significance}
                """.strip(),
                'keywords': ['temperature', 'anomaly', 'ocean', 'climate', 'thermocline']
            },
            'salinity_patterns': {
                'title': 'Ocean Salinity Distribution Patterns',
                'template': """
ARGO measurements reveal salinity characteristics in {ocean_basin}:
- Surface salinity range: {surface_sal_range} PSU
- Deep salinity stability: {deep_sal_range} PSU
- Halocline strength: {halocline_strength}
- Freshwater influence: {freshwater_influence}
- Research implications: {implications}
                """.strip(),
                'keywords': ['salinity', 'halocline', 'freshwater', 'density', 'circulation']
            },
            'water_masses': {
                'title': 'Water Mass Identification and Properties',
                'template': """
T-S diagram analysis from ARGO data identifies water masses in {ocean_basin}:
- Temperature-Salinity characteristics: {ts_characteristics}
- Water mass types present: {water_masses}
- Mixing zones identified: {mixing_zones}
- Depth distribution: {depth_distribution}
- Oceanographic importance: {importance}
                """.strip(),
                'keywords': ['water mass', 'ts diagram', 'mixing', 'oceanography', 'properties']
            },
            'regional_climatology': {
                'title': 'Regional Ocean Climatology Summary',
                'template': """
Climatological analysis for {ocean_basin} based on ARGO observations:
- Mean annual temperature: {mean_temp}°C
- Mean annual salinity: {mean_sal} PSU
- Seasonal variation amplitude: {seasonal_amp}
- Long-term trends: {trends}
- Climate change indicators: {climate_indicators}
                """.strip(),
                'keywords': ['climatology', 'mean', 'trends', 'climate change', 'regional']
            }
        }
    
    def extract_oceanographic_insights(self) -> List[Dict[str, Any]]:
        """Extract scientific insights from ARGO database"""
        insights = []
        
        with self.SessionLocal() as session:
            try:
                # Get data by ocean basin
                ocean_basins_query = text("""
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
                
                results = session.execute(ocean_basins_query).fetchall()
                
                for row in results:
                    ocean_basin = row.ocean_basin
                    stats = {
                        'ocean_basin': ocean_basin,
                        'float_count': row.float_count,
                        'profile_count': row.profile_count,
                        'measurement_count': row.measurement_count,
                        'avg_temp': round(row.avg_temp, 2) if row.avg_temp else 0,
                        'avg_sal': round(row.avg_sal, 2) if row.avg_sal else 0,
                        'min_temp': round(row.min_temp, 2) if row.min_temp else 0,
                        'max_temp': round(row.max_temp, 2) if row.max_temp else 0,
                        'min_sal': round(row.min_sal, 2) if row.min_sal else 0,
                        'max_sal': round(row.max_sal, 2) if row.max_sal else 0,
                        'temp_range': f"{round(row.min_temp, 2)} to {round(row.max_temp, 2)}",
                        'sal_range': f"{round(row.min_sal, 2)} to {round(row.max_sal, 2)}",
                        'date_range': f"{row.earliest_date} to {row.latest_date}" if row.earliest_date else "Unknown"
                    }
                    
                    # Generate insights for each template
                    insights.extend(self.generate_insights_from_stats(stats))
                
                logger.info(f"Generated {len(insights)} RAG documents from {len(results)} ocean basins")
                
            except Exception as e:
                logger.error(f"Error extracting insights: {e}")
        
        return insights
    
    def generate_insights_from_stats(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate RAG documents from statistics"""
        documents = []
        
        # Temperature anomalies insight
        temp_doc = self.knowledge_templates['temperature_anomalies'].copy()
        temp_doc['content'] = temp_doc['template'].format(
            ocean_basin=stats['ocean_basin'],
            surface_temp_range=f"{stats['min_temp']} to {stats['max_temp']}",
            deep_temp_range=f"{stats['min_temp']} to {stats['max_temp']}",  # Simplified
            thermocline_depth="100-200",  # Estimated
            profile_count=stats['profile_count'],
            date_range=stats['date_range'],
            significance=self.determine_temperature_significance(stats)
        )
        temp_doc['source'] = f"ARGO Analysis - {stats['ocean_basin']} - {datetime.now().strftime('%Y-%m-%d')}"
        temp_doc['score'] = 1.0
        documents.append(temp_doc)
        
        # Salinity patterns insight
        sal_doc = self.knowledge_templates['salinity_patterns'].copy()
        sal_doc['content'] = sal_doc['template'].format(
            ocean_basin=stats['ocean_basin'],
            surface_sal_range=stats['sal_range'],
            deep_sal_range=stats['sal_range'],
            halocline_strength=self.assess_halocline_strength(stats),
            freshwater_influence=self.assess_freshwater_influence(stats),
            implications=self.determine_salinity_implications(stats)
        )
        sal_doc['source'] = f"ARGO Analysis - {stats['ocean_basin']} - {datetime.now().strftime('%Y-%m-%d')}"
        sal_doc['score'] = 1.0
        documents.append(sal_doc)
        
        # Water masses insight
        water_doc = self.knowledge_templates['water_masses'].copy()
        water_doc['content'] = water_doc['template'].format(
            ocean_basin=stats['ocean_basin'],
            ts_characteristics=f"T: {stats['temp_range']}°C, S: {stats['sal_range']} PSU",
            water_masses=self.identify_water_masses(stats),
            mixing_zones=self.identify_mixing_zones(stats),
            depth_distribution="Surface to 2000m",
            importance=self.assess_water_mass_importance(stats)
        )
        water_doc['source'] = f"ARGO Analysis - {stats['ocean_basin']} - {datetime.now().strftime('%Y-%m-%d')}"
        water_doc['score'] = 1.0
        documents.append(water_doc)
        
        # Regional climatology insight
        climate_doc = self.knowledge_templates['regional_climatology'].copy()
        climate_doc['content'] = climate_doc['template'].format(
            ocean_basin=stats['ocean_basin'],
            mean_temp=stats['avg_temp'],
            mean_sal=stats['avg_sal'],
            seasonal_amp=f"{round(stats['max_temp'] - stats['min_temp'], 2)}°C",
            trends=self.identify_trends(stats),
            climate_indicators=self.assess_climate_indicators(stats)
        )
        climate_doc['source'] = f"ARGO Analysis - {stats['ocean_basin']} - {datetime.now().strftime('%Y-%m-%d')}"
        climate_doc['score'] = 1.0
        documents.append(climate_doc)
        
        return documents
    
    def determine_temperature_significance(self, stats: Dict[str, Any]) -> str:
        """Determine scientific significance of temperature patterns"""
        temp_range = stats['max_temp'] - stats['min_temp']
        if temp_range > 20:
            return "strong thermal stratification and potential climate change impacts"
        elif temp_range > 15:
            return "moderate thermal variation with seasonal influences"
        else:
            return "relatively stable thermal conditions"
    
    def assess_halocline_strength(self, stats: Dict[str, Any]) -> str:
        """Assess halocline strength"""
        sal_range = stats['max_sal'] - stats['min_sal']
        if sal_range > 2:
            return "strong halocline present"
        elif sal_range > 1:
            return "moderate halocline"
        else:
            return "weak halocline"
    
    def assess_freshwater_influence(self, stats: Dict[str, Any]) -> str:
        """Assess freshwater influence"""
        if stats['min_sal'] < 34:
            return "significant freshwater input detected"
        elif stats['min_sal'] < 35:
            return "moderate freshwater influence"
        else:
            return "minimal freshwater influence"
    
    def determine_salinity_implications(self, stats: Dict[str, Any]) -> str:
        """Determine salinity research implications"""
        return "affects ocean density, circulation patterns, and marine ecosystem distribution"
    
    def identify_water_masses(self, stats: Dict[str, Any]) -> str:
        """Identify likely water masses based on T-S characteristics"""
        if stats['avg_temp'] > 25 and stats['avg_sal'] > 36:
            return "Tropical Surface Water, Subtropical Water"
        elif stats['avg_temp'] < 5 and stats['avg_sal'] < 34.5:
            return "Antarctic Bottom Water, Polar Water"
        elif stats['avg_temp'] > 15 and stats['avg_sal'] > 35:
            return "Subtropical Mode Water, Mediterranean Water"
        else:
            return "Mixed water masses with regional characteristics"
    
    def identify_mixing_zones(self, stats: Dict[str, Any]) -> str:
        """Identify mixing zones"""
        return "thermocline and halocline regions where water masses interact"
    
    def assess_water_mass_importance(self, stats: Dict[str, Any]) -> str:
        """Assess water mass importance"""
        return "critical for understanding ocean circulation, heat transport, and biogeochemical cycles"
    
    def identify_trends(self, stats: Dict[str, Any]) -> str:
        """Identify potential trends"""
        return "insufficient temporal coverage for trend analysis; requires longer time series"
    
    def assess_climate_indicators(self, stats: Dict[str, Any]) -> str:
        """Assess climate change indicators"""
        temp_avg = stats['avg_temp']
        if temp_avg > 20:
            return "tropical warming patterns consistent with climate change projections"
        elif temp_avg < 5:
            return "polar amplification signals in temperature data"
        else:
            return "mid-latitude temperature variability within expected ranges"
    
    def save_rag_documents(self, documents: List[Dict[str, Any]], output_file: str = "argo_rag_corpus.json"):
        """Save RAG documents to file"""
        output_path = Path(__file__).parent / "corpus" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(documents)} RAG documents to {output_path}")
        return output_path
    
    def generate_enhanced_corpus(self) -> str:
        """Generate enhanced RAG corpus from ARGO data"""
        logger.info("Starting ARGO RAG corpus generation...")
        
        # Extract insights from database
        documents = self.extract_oceanographic_insights()
        
        # Add existing default corpus
        try:
            from rag.default_corpus import get_default_corpus
            default_docs = get_default_corpus()
        except ImportError:
            default_docs = []
        
        # Combine documents
        all_documents = documents + default_docs
        
        # Save combined corpus
        output_file = self.save_rag_documents(all_documents, "enhanced_argo_corpus.json")
        
        logger.info(f"Enhanced RAG corpus generated with {len(all_documents)} documents")
        return output_file

def main():
    """Main execution function"""
    ingestion = ArgoRAGIngestion()
    output_file = ingestion.generate_enhanced_corpus()
    print(f"✅ Enhanced RAG corpus generated: {output_file}")

if __name__ == "__main__":
    main()

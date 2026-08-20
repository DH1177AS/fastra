# historical.py - ACES-300 Layer 6: Historical Layer
# Template untuk data proyek historis

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class HistoricalProject:
    """Data proyek yang telah selesai untuk analisis tren."""
    project_name: str = ""
    location: str = ""
    building_type: str = "HOUSE"
    total_area: float = 0.0
    contract_value: float = 0.0
    actual_cost: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_planned_days: int = 0
    duration_actual_days: int = 0
    cost_overrun_percentage: float = 0.0
    material_cost_actual: Dict = field(default_factory=dict)
    labor_cost_actual: Dict = field(default_factory=dict)
    productivity_actual: Dict = field(default_factory=dict)

@dataclass
class HistoricalPriceTrend:
    """Data tren harga material per kuartal."""
    material_name: str = ""
    unit: str = ""
    q1_2024: float = 0.0
    q2_2024: float = 0.0
    q3_2024: float = 0.0
    q4_2024: float = 0.0
    q1_2025: float = 0.0
    q2_2025: float = 0.0

# Sample data tren harga sesuai ACES-300 Section 11.3
SAMPLE_PRICE_TRENDS = [
    HistoricalPriceTrend("Semen (sak)", "sak", 58000, 58500, 60000, 62000, 63000, 63500),
    HistoricalPriceTrend("Baja Ringan (batang)", "batang", 75000, 76000, 78000, 80000, 82000, 81000),
    HistoricalPriceTrend("Besi D10 (batang)", "batang", 110000, 112000, 115000, 118000, 120000, 119000),
    HistoricalPriceTrend("Genteng Beton (buah)", "buah", 6000, 6000, 6200, 6500, 6500, 6800),
]

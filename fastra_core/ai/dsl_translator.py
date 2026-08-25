"""
ACES-700 DSL Translation Protocol
Mengubah deskripsi natural language sederhana menjadi Construction DSL.
Tidak menghasilkan BOQ/RAB langsung.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastra_core.ai.safety import SafetyFilter


@dataclass
class DSLTranslationResult:
    source_text: str
    dsl_text: str
    entities: List[Dict[str, Any]]
    needs_review: bool = True
    warnings: List[str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


class DSLTranslator:
    """Penerjemah natural language (sederhana) ke Construction DSL."""

    def __init__(self) -> None:
        self.safety = SafetyFilter()

    def translate(self, text: str) -> DSLTranslationResult:
        """Menerjemahkan teks bahasa alami menjadi DSL. Selalu butuh review."""
        safe, reason = self.safety.check(text)
        if not safe:
            raise ValueError(f"Teks tidak aman: {reason}")

        dsl_lines = []
        entities: List[Dict[str, Any]] = []
        warnings = []

        lowered = text.lower()

        # Deteksi tipe bangunan
        building_type = None
        if "rumah" in lowered:
            building_type = "HOUSE"
        elif "ruko" in lowered:
            building_type = "RUKO"
        elif "gedung" in lowered:
            building_type = "BUILDING"
        elif "gudang" in lowered:
            building_type = "WAREHOUSE"
        if building_type:
            dsl_lines.append(f"CREATE BUILDING TYPE {building_type}")
            entities.append({"type": "Building", "building_type": building_type})

        # Deteksi lantai
        storey = None
        if "1 lantai" in lowered or "satu lantai" in lowered:
            storey = 1
        elif "2 lantai" in lowered or "dua lantai" in lowered:
            storey = 2
        elif "3 lantai" in lowered or "tiga lantai" in lowered:
            storey = 3
        if storey:
            dsl_lines.append(f"STOREY {storey}")
            if entities:
                entities[0]["storeys"] = storey
            else:
                entities.append({"type": "Building", "storeys": storey})

        # Deteksi luas
        import re
        area_match = re.search(r"(\d+)\s*(?:m2|m²|meter persegi|m persegi|square meter)", lowered)
        if area_match:
            area = int(area_match.group(1))
            dsl_lines.append(f"AREA {area}")
            if entities:
                entities[0]["area"] = area
            else:
                entities.append({"type": "Building", "area": area})

        # Deteksi lokasi
        known_locations = ["bandung", "jakarta", "surabaya", "yogyakarta", "medan", "semarang"]
        for loc in known_locations:
            if loc in lowered:
                dsl_lines.append(f"LOCATION {loc.upper()}")
                if entities:
                    entities[0]["location"] = loc.upper()
                break

        # Deteksi material dinding
        wall_material = None
        if "hebel" in lowered or "aac" in lowered:
            wall_material = "AAC_BLOCK"
        elif "bata merah" in lowered:
            wall_material = "BATA_MERAH"
        elif "bata ringan" in lowered:
            wall_material = "AAC_BLOCK"
        if wall_material:
            dsl_lines.append(f"WALL MATERIAL {wall_material}")
            entities.append({"type": "Wall", "material": wall_material})

        # Deteksi atap
        roof_type = None
        if "baja ringan" in lowered:
            roof_type = "LIGHT_STEEL"
        elif "kayu" in lowered:
            roof_type = "WOOD"
        if roof_type:
            dsl_lines.append(f"ROOF STRUCTURE {roof_type}")
            entities.append({"type": "Roof", "structure": roof_type})

        if not dsl_lines:
            warnings.append("Tidak ada fitur dikenali, DSL kosong. Perlu input lebih detail.")

        dsl_text = "\n".join(dsl_lines)
        return DSLTranslationResult(
            source_text=text,
            dsl_text=dsl_text,
            entities=entities,
            needs_review=True,
            warnings=warnings,
        )

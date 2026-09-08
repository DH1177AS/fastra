# fastra_core/knowledge/domains/semantic.py

from __future__ import annotations

from types import MappingProxyType
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Inbound & Outbound DTOs – Pydantic Strict Gateway (Fail-Fast)
# ---------------------------------------------------------------------------
class TermQueryDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    term: str = Field(..., min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_\-\.\s\(\)\,\/]+$")


class TermSynonymManifestDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    standard_term: str = Field(..., min_length=2, max_length=128)
    synonyms: List[str] = Field(..., max_length=100)


# ---------------------------------------------------------------------------
# Repository Immutable Master Dictionary (Kamus Taksonomi Baku IQSI)
# ---------------------------------------------------------------------------
_SYNONYM_DICTIONARY_RAW: Dict[str, List[str]] = {
  
    "Pasangan Bata Merah": [
        "Pasangan batu bata", "Tembok bata", "Dinding bata",
        "Pasangan bata", "Pemasangan batu bata"
    ],
    "Bata Ringan": [
        "Hebel", "AAC Block", "Bata putih", "Bata ringan AAC",
        "Lightweight brick"
    ],
    "Plesteran": [
        "Lepa", "Plaster", "Plester", "Plasteran"
    ],
    "Acian": [
        "Semen halus", "Skim coat", "Aci", "Acian halus"
    ],
   
    "Beton Ready Mix": [
        "Beton cor", "Beton jadi", "Ready mix concrete",
        "Beton ready mix", "Concrete ready mix"
    ],
    "Bekisting": [
        "Cetakan", "Formwork", "Mal cor", "Bekisting kayu",
        "Form work"
    ],
    "Ring Balk": [
        "Balok latei", "Balok keliling", "Top beam",
        "Ring balok", "Ring beam"
    ],
    "Sloof": [
        "Balok pondasi", "Tie beam", "Sloof beton",
        "Balok sloof"
    ],
    "Pembesian": [
        "Penulangan", "Rebar", "Pemasangan besi",
        "Pekerjaan besi", "Steel reinforcement"
    ],
   
    "Rangka Atap Baja Ringan": [
        "Rangka atap galvalum", "Truss atap", "Kuda-kuda baja ringan",
        "Rangka baja ringan"
    ],
    "Genteng Beton": [
        "Genteng beton flat", "Concrete tile", "Genteng semen"
    ],
    "Lisplang": [
        "Lisplank", "Fascia board", "Papan lisplang"
    ],
   
    "Keramik Lantai": [
        "Tile lantai", "Ubin keramik", "Keramik",
        "Lantai keramik"
    ],
    "Granit Lantai": [
        "Granite tile", "Lantai granit", "Homogeneous tile"
    ],
   
    "Instalasi Listrik": [
        "Pemasangan listrik", "Electrical installation",
        "Pekerjaan elektrikal"
    ],
    "Instalasi Plumbing": [
        "Pemasangan pipa", "Plumbing work", "Pekerjaan plumbing",
        "Instalasi pipa"
    ],
   
    "Pekerja": [
        "Labour", "Buruh", "Kenek", "Helper", "Unskilled worker"
    ],
    "Tukang": [
        "Craftsman", "Skilled worker", "Artisan"
    ],
    "Mandor": [
        "Foreman", "Supervisor lapangan", "Overseer"
    ],
}

SYNONYM_DICTIONARY: MappingProxyType = MappingProxyType(_SYNONYM_DICTIONARY_RAW)

_SYNONYM_LOOKUP: Dict[str, str] = {}
for _std_term, _syns in SYNONYM_DICTIONARY.items():
    _SYNONYM_LOOKUP[_std_term.lower().strip()] = _std_term
    for _s in _syns:
        _SYNONYM_LOOKUP[_s.lower().strip()] = _std_term


# ---------------------------------------------------------------------------
# Core Lexical Query Logic – Pure Semantic Matching (QS-Safe)
# ---------------------------------------------------------------------------
def get_standard_term(term: str) -> str:
   
    query_dto = TermQueryDTO(term=term)
    cleaned_term = query_dto.term.lower().strip()
   
    return _SYNONYM_LOOKUP.get(cleaned_term, query_dto.term)


def get_synonyms(standard_term: str) -> List[str]:
    
    if not standard_term or not standard_term.strip():
        return []

    cleaned_key = standard_term.strip()
    
    if cleaned_key in SYNONYM_DICTIONARY:
        synonyms_pool = list(SYNONYM_DICTIONARY[cleaned_key])

        output_payload = {
            "standard_term": cleaned_key,
            "synonyms": synonyms_pool,
        }
       
        validated_manifest = TermSynonymManifestDTO.model_validate(output_payload)
        return list(validated_manifest.synonyms)

    return []
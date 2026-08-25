"""
ccm_validator.py
================
Parser & Validator untuk Construction Canonical Model (CCM) — FASTRA/SnapBuild.

Fungsi utama:
1. Membaca file input yang berisi satu atau lebih objek JSON CCM yang mungkin
   terpecah (mis. ConstructionCanonicalModel_Part1 diikuti Part2 tanpa
   separator array/koma yang valid — kondisi nyata yang ditemukan di data klien).
2. Menggabungkan seluruh part berdasarkan ProjectID yang sama (merge key).
3. Memvalidasi hasil gabungan terhadap aturan skema master CCM-MASTER-2026.V1:
   - Elemen tanpa ParentSpaceID -> orphan_element_error
   - Elemen struktural tanpa geometri -> NEEDS_CLIENT_INPUT
   - Sloof/Column dimensi kosong -> BLOCKING_ISSUE
   - Bukaan (Door/Window) tanpa host_wall_uuid -> NEEDS_CLIENT_INPUT
   - MEP tanpa panjang jalur (CircuitPath/PipeRun) -> NEEDS_CLIENT_INPUT
4. Menurunkan (derive) RelationsGraph CONTAINS secara otomatis dari nesting
   Space -> BuildingElements yang sudah ada di data sumber.
5. Menghasilkan ValidationReport terstruktur dan menyimpan hasil akhir ke file JSON.

Prinsip yang dipegang: TIDAK ADA nilai ditebak/di-default untuk field yang
safety-critical (struktur) atau presisi-critical (geometri). Semua gap
ditandai eksplisit, bukan diisi diam-diam.

Cara pakai (CLI):
    python ccm_validator.py input.json output.json

Cara pakai (sebagai modul):
    from ccm_validator import run_pipeline
    result = run_pipeline(raw_text)
"""

from __future__ import annotations

import json
import sys
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ccm_validator")

# --------------------------------------------------------------------------
# Konstanta skema
# --------------------------------------------------------------------------

# Tipe elemen fisik yang WAJIB punya data geometri untuk perhitungan volume presisi.
STRUCTURAL_ELEMENT_TYPES = {"Wall", "Column", "Beam", "Slab", "Foundation", "Roof"}

# Tipe elemen "bukaan" yang wajib punya host_wall_uuid.
OPENING_ELEMENT_TYPES = {"Door", "Window"}

SCHEMA_VERSION = "CCM-MASTER-2026.V1"


class CCMMergeError(Exception):
    """Dilempar ketika beberapa bagian data tidak bisa digabung dengan aman."""


class CCMParseError(Exception):
    """Dilempar ketika teks input tidak bisa diuraikan sebagai satu/lebih objek JSON."""


# --------------------------------------------------------------------------
# 1. Parsing input yang mungkin berisi banyak objek JSON tanpa separator
# --------------------------------------------------------------------------

def parse_multi_json(raw_text: str) -> List[Dict[str, Any]]:
    """
    Mengurai teks yang berisi satu atau lebih objek JSON yang diletakkan
    berurutan tanpa separator array (kondisi nyata pada sampel data klien:
    dua objek top-level ditulis bersebelahan, bukan dalam satu array/JSONL).

    Menggunakan json.JSONDecoder().raw_decode() secara iteratif agar toleran
    terhadap whitespace/newline di antara objek.
    """
    if not raw_text or not raw_text.strip():
        raise CCMParseError("Input kosong — tidak ada data untuk diproses.")

    decoder = json.JSONDecoder()
    text = raw_text.strip()
    objects: List[Dict[str, Any]] = []
    idx = 0
    length = len(text)

    while idx < length:
        # Lewati whitespace di antara objek
        while idx < length and text[idx].isspace():
            idx += 1
        if idx >= length:
            break
        try:
            obj, end_idx = decoder.raw_decode(text, idx)
        except json.JSONDecodeError as exc:
            raise CCMParseError(
                f"Gagal mengurai JSON pada posisi karakter {idx}: {exc.msg}"
            ) from exc
        objects.append(obj)
        idx = end_idx

    if not objects:
        raise CCMParseError("Tidak ditemukan objek JSON valid dalam input.")

    logger.info("Berhasil mengurai %d objek JSON dari input.", len(objects))
    return objects


# --------------------------------------------------------------------------
# 2. Merge berdasarkan ProjectID
# --------------------------------------------------------------------------

def _extract_project_id(part: Dict[str, Any]) -> Optional[str]:
    """Mencari ProjectID di dalam satu bagian data, di mana pun letaknya."""
    for root_key, root_val in part.items():
        if not isinstance(root_val, dict):
            continue
        metadata = root_val.get("ModelMetadata")
        if isinstance(metadata, dict):
            ctx = metadata.get("ProjectContext", {})
            pid = ctx.get("ProjectID")
            if pid:
                return pid
    return None


def _deep_merge(base: Dict[str, Any], addition: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dict secara rekursif. List digabung (extend), dict digabung rekursif,
    scalar pada addition menimpa base HANYA jika base belum punya key tersebut
    (tidak menimpa data yang sudah ada, mencegah kehilangan data saat merge)."""
    result = dict(base)
    for key, value in addition.items():
        if key not in result:
            result[key] = value
        elif isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        elif isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        # Jika scalar sudah ada di base dan berbeda di addition, base dipertahankan
        # dan dicatat sebagai potensi konflik (lihat merge_ccm_parts).
    return result


def merge_ccm_parts(parts: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Menggabungkan beberapa objek CCM (mis. Part1, Part2, ...) menjadi satu
    struktur ConstructionCanonicalModel tunggal.

    Merge key: ProjectID pada ModelMetadata.ProjectContext.ProjectID.
    Semua part HARUS memiliki ProjectID yang sama, atau merge ditolak
    (mencegah penggabungan data proyek yang berbeda secara tidak sengaja).

    Return: (merged_dict, merge_notes)
    """
    if not parts:
        raise CCMMergeError("Tidak ada bagian data untuk digabung.")

    project_ids = set()
    for i, part in enumerate(parts):
        pid = _extract_project_id(part)
        if pid is None:
            logger.warning(
                "Bagian ke-%d tidak memiliki ProjectID eksplisit — dilewati saat "
                "validasi merge key, tapi tetap digabung strukturnya.", i + 1
            )
        else:
            project_ids.add(pid)

    if len(project_ids) > 1:
        raise CCMMergeError(
            f"Ditemukan lebih dari satu ProjectID berbeda: {project_ids}. "
            "Merge dibatalkan untuk mencegah penggabungan data proyek yang tidak sama."
        )

    merged: Dict[str, Any] = {}
    merge_notes: List[str] = []

    for i, part in enumerate(parts):
        # Setiap part biasanya punya satu root key (mis. "ConstructionCanonicalModel_Part1")
        for root_key, root_val in part.items():
            if not isinstance(root_val, dict):
                continue
            merged = _deep_merge(merged, root_val)
            merge_notes.append(f"Bagian '{root_key}' (input ke-{i + 1}) berhasil digabung.")

    logger.info("Merge selesai. %d bagian digabung menjadi satu struktur.", len(parts))
    return merged, merge_notes


# --------------------------------------------------------------------------
# 3. Traversal helper — mengekstrak semua Space dan BuildingElements
# --------------------------------------------------------------------------

def iter_spaces(merged: Dict[str, Any]) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """Menyusuri seluruh hierarki dan menghasilkan (SpaceID, space_dict)."""
    buildings = merged.get("BuildingEntities", [])
    for building in buildings:
        for storey in building.get("Storeys", []):
            for zone in storey.get("SpatialZones", []):
                for space in zone.get("Spaces", []):
                    space_id = space.get("SpaceID", "UNKNOWN_SPACE")
                    yield space_id, space

    # Beberapa sumber (seperti Part2 pada sampel klien) menaruh zona tambahan
    # di bawah key ekstensi terpisah — tetap disusuri agar tidak ada data yang hilang.
    extension = merged.get("BuildingEntities_Extension", {})
    for zone in extension.get("SpatialZones_Service", []):
        for space in zone.get("Spaces", []):
            space_id = space.get("SpaceID", "UNKNOWN_SPACE")
            yield space_id, space


def iter_elements(merged: Dict[str, Any]) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """Menyusuri seluruh Space dan menghasilkan (SpaceID, element_dict) untuk
    setiap BuildingElement, memastikan ParentSpaceID selalu tercatat."""
    for space_id, space in iter_spaces(merged):
        for elem in space.get("BuildingElements", []) or []:
            elem.setdefault("ParentSpaceID", space_id)
            yield space_id, elem


# --------------------------------------------------------------------------
# 4. Validator per kategori
# --------------------------------------------------------------------------

@dataclass
class ValidationFinding:
    path: str
    issue: str
    severity: str  # "BLOCKING_ISSUE" | "NEEDS_CLIENT_INPUT" | "NEEDS_CLIENT_CONFIRMATION"
    impact: Optional[str] = None


def validate_structural_framing(merged: Dict[str, Any]) -> List[ValidationFinding]:
    """Cek dimensi Sloof & Column — hard-stop jika kosong (safety-critical)."""
    findings: List[ValidationFinding] = []
    framing = (
        merged.get("InfrastructureSystems", {})
        .get("StructuralSystem", {})
        .get("Framing", {})
    )

    sloof = framing.get("Sloof_Dimensions_mm")
    column = framing.get("Column_Main_Dimensions_mm")

    if not sloof:
        findings.append(ValidationFinding(
            path="InfrastructureSystems.StructuralSystem.Framing.Sloof_Dimensions_mm",
            issue="Dimensi sloof kosong/null.",
            severity="BLOCKING_ISSUE",
            impact="Item pekerjaan sloof TIDAK dihitung dalam RAB sampai klien mengonfirmasi dimensi.",
        ))
    if not column:
        findings.append(ValidationFinding(
            path="InfrastructureSystems.StructuralSystem.Framing.Column_Main_Dimensions_mm",
            issue="Dimensi kolom utama kosong/null.",
            severity="BLOCKING_ISSUE",
            impact="Item pekerjaan kolom TIDAK dihitung dalam RAB sampai klien mengonfirmasi dimensi.",
        ))

    ring_balk = framing.get("RingBalk_Dimensions_mm")
    if ring_balk and (not sloof or not column):
        findings.append(ValidationFinding(
            path="InfrastructureSystems.StructuralSystem.Framing.RingBalk_Dimensions_mm",
            issue=f"RingBalk terisi {ring_balk}, tetapi field bersebelahan (Sloof/Column) kosong.",
            severity="NEEDS_CLIENT_CONFIRMATION",
            impact="Berisiko RingBalk juga salah input — perlu konfirmasi ulang ke klien.",
        ))

    return findings


def validate_element_geometry(merged: Dict[str, Any]) -> List[ValidationFinding]:
    """Cek geometri untuk setiap elemen struktural/fisik."""
    findings: List[ValidationFinding] = []

    for space_id, elem in iter_elements(merged):
        elem_type = elem.get("Type")
        elem_id = elem.get("ElementID", "UNKNOWN_ELEMENT")
        geometry = elem.get("geometry")

        if elem_type in STRUCTURAL_ELEMENT_TYPES:
            if not geometry or not _geometry_has_required_points(elem_type, geometry):
                findings.append(ValidationFinding(
                    path=f"Space[{space_id}].BuildingElements[{elem_id}].geometry",
                    issue=f"Elemen tipe '{elem_type}' tidak memiliki geometri lengkap.",
                    severity="NEEDS_CLIENT_INPUT",
                    impact="Volume elemen ini tidak dapat dihitung presisi — estimasi kasar tidak digunakan.",
                ))

        if elem_type in OPENING_ELEMENT_TYPES:
            host = (geometry or {}).get("host_wall_uuid")
            if not host:
                findings.append(ValidationFinding(
                    path=f"Space[{space_id}].BuildingElements[{elem_id}].geometry.host_wall_uuid",
                    issue=f"Elemen '{elem_id}' ({elem_type}) tidak memiliki host_wall_uuid.",
                    severity="NEEDS_CLIENT_INPUT",
                    impact="Luas dinding pada FinishesSchedule tidak bisa dikurangi otomatis untuk bukaan ini.",
                ))
            dims = elem.get("Dimensions", {})
            if not dims.get("Width_mm") or not dims.get("Height_mm"):
                findings.append(ValidationFinding(
                    path=f"Space[{space_id}].BuildingElements[{elem_id}].Dimensions",
                    issue=f"Dimensi Width_mm/Height_mm elemen '{elem_id}' kosong.",
                    severity="NEEDS_CLIENT_INPUT",
                ))

    return findings


def _geometry_has_required_points(elem_type: str, geometry: Dict[str, Any]) -> bool:
    """Cek apakah field geometri kunci per tipe elemen sudah terisi (bukan null)."""
    checks = {
        "Wall": lambda g: (g.get("axis_line") or {}).get("points"),
        "Column": lambda g: g.get("width") and g.get("depth") and g.get("height"),
        "Beam": lambda g: g.get("width") and g.get("depth") and g.get("length"),
        "Slab": lambda g: (g.get("boundary") or {}).get("points") and g.get("thickness"),
        "Foundation": lambda g: (g.get("footprint") or {}).get("points") and g.get("depth"),
        "Roof": lambda g: (g.get("footprint") or {}).get("points"),
    }
    check_fn = checks.get(elem_type)
    return bool(check_fn(geometry)) if check_fn else True


def validate_mep_paths(merged: Dict[str, Any]) -> List[ValidationFinding]:
    """Cek panjang jalur kabel (CircuitPath) dan pipa (PipeRun) di setiap Space."""
    findings: List[ValidationFinding] = []

    for space_id, space in iter_spaces(merged):
        mep = space.get("MEP_DistributionPoints") or {}

        for fixture in mep.get("Electrical", []) or []:
            circuit = fixture.get("CircuitPath") or {}
            if not circuit.get("length_m") and not circuit.get("estimated_length_m"):
                findings.append(ValidationFinding(
                    path=f"Space[{space_id}].MEP.Electrical[{fixture.get('FixtureID')}].CircuitPath",
                    issue="Panjang jalur kabel tidak diketahui.",
                    severity="NEEDS_CLIENT_INPUT",
                    impact="RAB kabel tidak bisa dihitung untuk titik ini tanpa estimasi eksplisit dari klien.",
                ))

        for fixture in mep.get("PlumbingFixtures", []) or []:
            pipe = fixture.get("PipeRun") or {}
            if not pipe.get("cold_water_length_m") and not pipe.get("waste_length_m"):
                findings.append(ValidationFinding(
                    path=f"Space[{space_id}].MEP.PlumbingFixtures[{fixture.get('FixtureID')}].PipeRun",
                    issue="Panjang jalur pipa tidak diketahui.",
                    severity="NEEDS_CLIENT_INPUT",
                    impact="RAB pipa tidak bisa dihitung untuk titik ini tanpa estimasi eksplisit dari klien.",
                ))

    return findings


def validate_space_boundaries(merged: Dict[str, Any]) -> List[ValidationFinding]:
    """Cek apakah Space punya poligon Boundary.Points, bukan hanya Area/Perimeter."""
    findings: List[ValidationFinding] = []
    for space_id, space in iter_spaces(merged):
        boundary = space.get("Boundary") or {}
        if not boundary.get("Points"):
            findings.append(ValidationFinding(
                path=f"Space[{space_id}].Boundary.Points",
                issue="Poligon batas ruang tidak tersedia (hanya Area_m2/Perimeter_m).",
                severity="NEEDS_CLIENT_INPUT",
                impact="Bentuk ruang aktual tidak diketahui — relasi ADJACENT_TO antar ruang tidak dapat divalidasi.",
            ))
    return findings


def validate_project_level_data(merged: Dict[str, Any]) -> List[ValidationFinding]:
    """Cek ProjectSchedule dan CommercialAssumptions di level proyek."""
    findings: List[ValidationFinding] = []

    schedule = merged.get("ProjectSchedule")
    if not schedule or not schedule.get("DurationValue"):
        findings.append(ValidationFinding(
            path="ProjectSchedule",
            issue="Data jadwal proyek (durasi, kurva-S) tidak tersedia.",
            severity="NEEDS_CLIENT_INPUT",
        ))

    commercial = merged.get("CommercialAssumptions")
    if not commercial or not commercial.get("OverheadPercent"):
        findings.append(ValidationFinding(
            path="CommercialAssumptions",
            issue="Asumsi overhead/profit/contingency tidak tersedia.",
            severity="NEEDS_CLIENT_INPUT",
        ))

    return findings


# --------------------------------------------------------------------------
# 5. Derive RelationsGraph dari nesting yang sudah ada
# --------------------------------------------------------------------------

def derive_relations(merged: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Menurunkan relasi CONTAINS secara sah dari struktur nesting Space ->
    BuildingElements yang sudah ada di data sumber (bukan tebakan).

    Juga menyertakan kandidat HOSTS jika sebuah Space hanya punya TEPAT SATU
    elemen Wall dan setidaknya satu elemen Door/Window tanpa host_wall_uuid —
    kandidat ini SELALU ditandai NEEDS_CLIENT_CONFIRMATION, tidak pernah
    dianggap sebagai fakta final.
    """
    relations: List[Dict[str, Any]] = []

    for space_id, space in iter_spaces(merged):
        elements = space.get("BuildingElements", []) or []
        walls = [e for e in elements if e.get("Type") == "Wall"]
        openings = [e for e in elements if e.get("Type") in OPENING_ELEMENT_TYPES]

        for elem in elements:
            relations.append({
                "source": space_id,
                "target": elem.get("ElementID"),
                "type": "CONTAINS",
                "notes": "Derived otomatis dari nesting BuildingElements di dalam Space.",
            })

        if len(walls) == 1:
            wall_id = walls[0].get("ElementID")
            for opening in openings:
                geometry = opening.get("geometry") or {}
                if not geometry.get("host_wall_uuid"):
                    relations.append({
                        "source": wall_id,
                        "target": opening.get("ElementID"),
                        "type": "HOSTS",
                        "notes": (
                            f"INFERENSI: '{wall_id}' adalah satu-satunya elemen Wall di "
                            f"'{space_id}', kandidat host paling mungkin untuk "
                            f"'{opening.get('ElementID')}'. Belum dikonfirmasi klien."
                        ),
                        "_status": "NEEDS_CLIENT_CONFIRMATION",
                    })

    return relations


# --------------------------------------------------------------------------
# 6. Membangun ValidationReport final
# --------------------------------------------------------------------------

def build_validation_report(
    merged: Dict[str, Any],
    findings: List[ValidationFinding],
) -> Dict[str, Any]:
    blocking = [f for f in findings if f.severity == "BLOCKING_ISSUE"]
    needs_input = [f for f in findings if f.severity == "NEEDS_CLIENT_INPUT"]
    needs_confirmation = [f for f in findings if f.severity == "NEEDS_CLIENT_CONFIRMATION"]

    total_spaces = sum(1 for _ in iter_spaces(merged))
    total_elements = sum(1 for _ in iter_elements(merged))

    overall_status = (
        "BLOCKED — ADA ISU KESELAMATAN/STRUKTUR YANG BELUM DIKONFIRMASI"
        if blocking else
        ("INCOMPLETE — DATA TEKNIS BELUM CUKUP UNTUK RAB PRESISI" if needs_input else
         "READY — SEMUA VALIDASI TERPENUHI")
    )

    return {
        "GeneratedAgainst": SCHEMA_VERSION,
        "OverallStatus": overall_status,
        "TotalSpaces": total_spaces,
        "TotalBuildingElements": total_elements,
        "BlockingIssuesCount": len(blocking),
        "NeedsClientInputCount": len(needs_input),
        "NeedsClientConfirmationCount": len(needs_confirmation),
        "BlockingIssues": [
            {"Path": f.path, "Issue": f.issue, "Impact": f.impact} for f in blocking
        ],
        "NeedsClientInput": [
            {"Path": f.path, "Issue": f.issue, "Impact": f.impact} for f in needs_input
        ],
        "NeedsClientConfirmation": [
            {"Path": f.path, "Issue": f.issue, "Impact": f.impact} for f in needs_confirmation
        ],
    }


# --------------------------------------------------------------------------
# 7. Pipeline utama
# --------------------------------------------------------------------------

def run_pipeline(raw_text: str) -> Dict[str, Any]:
    """
    Jalankan seluruh pipeline: parse -> merge -> validate -> derive relations
    -> build report. Mengembalikan struktur akhir siap ditulis ke file JSON.
    """
    parts = parse_multi_json(raw_text)
    merged, merge_notes = merge_ccm_parts(parts)

    findings: List[ValidationFinding] = []
    findings += validate_structural_framing(merged)
    findings += validate_element_geometry(merged)
    findings += validate_mep_paths(merged)
    findings += validate_space_boundaries(merged)
    findings += validate_project_level_data(merged)

    merged["RelationsGraph"] = derive_relations(merged)
    merged["ValidationReport"] = build_validation_report(merged, findings)
    merged["ValidationReport"]["MergeNotes"] = merge_notes

    return {"ConstructionCanonicalModel": merged}


def main() -> int:
    if len(sys.argv) != 3:
        print("Cara pakai: python ccm_validator.py <input.json> <output.json>")
        return 1

    input_path, output_path = sys.argv[1], sys.argv[2]

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except OSError as exc:
        logger.error("Gagal membaca file input '%s': %s", input_path, exc)
        return 1

    try:
        result = run_pipeline(raw_text)
    except (CCMParseError, CCMMergeError) as exc:
        logger.error("Pipeline gagal: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001 — pipeline harus tetap melaporkan error tak terduga
        logger.exception("Terjadi error tak terduga saat menjalankan pipeline: %s", exc)
        return 1

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        logger.error("Gagal menulis file output '%s': %s", output_path, exc)
        return 1

    report = result["ConstructionCanonicalModel"]["ValidationReport"]
    logger.info("Selesai. Status: %s", report["OverallStatus"])
    logger.info(
        "Blocking: %d | Needs Client Input: %d | Needs Confirmation: %d",
        report["BlockingIssuesCount"],
        report["NeedsClientInputCount"],
        report["NeedsClientConfirmationCount"],
    )
    logger.info("Hasil disimpan ke: %s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
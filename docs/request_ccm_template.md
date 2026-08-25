# Permintaan Data CCM — FASTRA

## Prinsip Umum
- Format JSON, versi 1.0.0
- Semua entitas wajib UUID valid dan unik
- Relasi antar-entitas di array `relationships`

## Struktur CCM
{
  "ccm_version": "1.0.0",
  "project_uuid": "00000000-0000-0000-0000-000000000000",
  "entities": [],
  "relationships": []
}

## Tipe Entitas Didukung
| Tipe | Geometri Minimal |
|------|------------------|
| Wall | axis_line.points (min 2), height, thickness |
| Column | width, depth, height |
| Beam | width, depth, length |
| Slab | boundary.points (min 3), thickness |
| Foundation | footprint.points (min 3), depth |
| Roof | footprint.points (min 3), slope |
| Door | width, height |
| Window | width, height, sill_height |
| Stairs | number_of_risers, riser_height, tread_depth, width |
| Ramp | length, width, slope |
| Room | boundary.points (min 3, tertutup) |

## Contoh CCM Sederhana
{
  "ccm_version": "1.0.0",
  "project_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "entities": [
    {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "entity_type": "Physical",
      "type": "Wall",
      "name": "Dinding Depan",
      "geometry": {
        "axis_line": {"points": [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0}]},
        "height": 3.5,
        "thickness": 0.15
      },
      "construction_type": "BATA_MERAH",
      "openings": []
    }
  ],
  "relationships": []
}

## Aturan Kualitas Data
- Poligon harus tertutup (titik pertama = titik terakhir)
- Koordinat tidak boleh NaN/Infinity
- Volume, luas, panjang > 0
- UUID unik
- Z boleh 0 untuk model 2D

## Perlindungan Data
- Kirim melalui NDA
- FASTRA tidak menyimpan CCM tanpa izin
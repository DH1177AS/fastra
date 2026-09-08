from __future__ import annotations

import logging
import threading
from typing import Any, Callable, List

from .wi_pra_konstruksi import load_wi_pra_konstruksi
from .wi_struktur_bawah import load_wi_struktur_bawah
from .wi_struktur_atas import load_wi_struktur_atas
from .wi_atap import load_wi_atap
from .wi_dinding_kusen import load_wi_dinding_kusen
from .wi_finishing import load_wi_finishing
from .wi_elektrikal import load_wi_elektrikal
from .wi_plumbing import load_wi_plumbing
from .wi_interior import load_wi_interior
from .wi_taman import load_wi_taman
from .wi_kolam_renang import load_wi_kolam_renang
from .wi_jalan import load_wi_jalan
from .wi_jembatan import load_wi_jembatan
from .wi_irigasi import load_wi_irigasi
from .wi_trotoar import load_wi_trotoar
from .wi_dermaga import load_wi_dermaga
from .wi_terowongan import load_wi_terowongan
from .wi_olahraga import load_wi_olahraga
from .wi_pertanian import load_wi_pertanian
from .wi_lapangan_terbang import load_wi_lapangan_terbang
from .wi_rumah_sakit import load_wi_rumah_sakit
from .wi_sekolah import load_wi_sekolah
from .wi_gedung_pemerintah import load_wi_gedung_pemerintah
from .wi_gudang import load_wi_gudang
from .wi_pasar import load_wi_pasar
from .wi_gondola import load_wi_gondola
from .wi_kolam_ikan import load_wi_kolam_ikan
from .wi_dekorasi_luar import load_wi_dekorasi_luar
from .wi_komponen_mikro import load_wi_komponen_mikro
from .wi_pengujian_qc import load_wi_pengujian_qc
from .wi_pre_furnishing import load_wi_pre_furnishing
from .wi_serah_terima import load_wi_serah_terima
from .wi_tambahan_relasi import load_wi_tambahan_relasi
from .wi_auto_generated import load_wi_auto_generated

logger = logging.getLogger("fastra.knowledge.work_item")

_LOADER_LOCK = threading.Lock()


def load_all_work_items(kg: Any) -> None:
    """
    Orchestrator utama untuk memuat seluruh item pekerjaan lintas domain ke Knowledge Graph.
    Menerapkan strict fail-fast validation, isolasi transaksi, rollback total atomik,
    serta thread-safety locks untuk mencegah korupsi state pada concurrent ingestion.
    """
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    if not hasattr(kg, "work_items") or not isinstance(kg.work_items, dict):
        raise AttributeError("INVALID_KNOWLEDGE_GRAPH_STATE_MISSING_WORK_ITEMS_CONTAINER")

    loaders: List[Callable[[Any], None]] = [
        load_wi_pra_konstruksi,
        load_wi_struktur_bawah,
        load_wi_struktur_atas,
        load_wi_atap,
        load_wi_dinding_kusen,
        load_wi_finishing,
        load_wi_elektrikal,
        load_wi_plumbing,
        load_wi_interior,
        load_wi_taman,
        load_wi_kolam_renang,
        load_wi_jalan,
        load_wi_jembatan,
        load_wi_irigasi,
        load_wi_trotoar,
        load_wi_dermaga,
        load_wi_terowongan,
        load_wi_olahraga,
        load_wi_pertanian,
        load_wi_lapangan_terbang,
        load_wi_rumah_sakit,
        load_wi_sekolah,
        load_wi_gedung_pemerintah,
        load_wi_gudang,
        load_wi_pasar,
        load_wi_gondola,
        load_wi_kolam_ikan,
        load_wi_dekorasi_luar,
        load_wi_komponen_mikro,
        load_wi_pengujian_qc,
        load_wi_pre_furnishing,
        load_wi_serah_terima,
        load_wi_tambahan_relasi,
        load_wi_auto_generated,
    ]

    for loader in loaders:
        if not callable(loader):
            raise TypeError(f"WORK_ITEM_LOADER_MUST_BE_CALLABLE: {loader!r}")

    with _LOADER_LOCK:
        initial_snapshot: dict = dict(kg.work_items)
        executed_loaders: List[str] = []
        current_loader_name: str = "UNKNOWN"

        try:
            for loader in loaders:
                current_loader_name = loader.__name__
                loader(kg)
                executed_loaders.append(current_loader_name)

        except Exception as global_pipeline_exception:
            logger.error(
                "CRITICAL_PIPELINE_FAILURE at loader %s. Executed loaders before crash: %s. Initiating total rollback of work_items container.",
                current_loader_name,
                executed_loaders,
            )

            kg.work_items.clear()
            kg.work_items.update(initial_snapshot)

            logger.info("Global rollback completed. work_items restored to initial snapshot of %d entries.", len(initial_snapshot))

            raise RuntimeError(
                f"GLOBAL_TRANSACTION_SAFE_BATCH_INGEST_FAILED_TOTAL_ROLLBACK_EXECUTED. "
                f"Failed loader: {current_loader_name}. Completed before crash: {executed_loaders}. "
                f"Error: {str(global_pipeline_exception)}"
            ) from global_pipeline_exception

        logger.info("TOTAL ITEM PEKERJAAN DIMUAT: %d", len(kg.work_items))

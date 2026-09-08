"""
FASTRA Backend Runner Engine
Menjalankan API Digital Twin Secure (port 8000) dan API AI Secure (port 8001)
secara bersamaan dalam satu proses menggunakan multiprocessing terisolasi.
Dengan logging terstruktur, health check, dan sinyal OS yang aman.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import signal
import sys
import time
from typing import Any, List, Optional

import uvicorn
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logger = logging.getLogger("fastra_core.backend_runner")
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
DIGITAL_TWIN_PORT = int(os.getenv("FASTRA_DT_PORT", "8000"))
AI_LAYER_PORT = int(os.getenv("FASTRA_AI_PORT", "8001"))
FORWARDED_ALLOW_IPS = os.getenv("FASTRA_FORWARDED_ALLOW_IPS", "127.0.0.1")


# ------------------------------------------------------------------------------
# 1. SUBPROCESS EXECUTORS
# ------------------------------------------------------------------------------
def run_digital_twin() -> None:
    os.environ['FASTRA_DATABASE_URL'] = os.getenv('FASTRA_DT_DB_URL', 'sqlite:///fastra_dt_dev.db')
    """Menjalankan API Digital Twin Secure Server."""
    try:
        uvicorn.run(
            "api_digital_twin_secure:app",
            host="0.0.0.0",
            port=DIGITAL_TWIN_PORT,
            log_level="info",
            workers=1,  # sudah multiproses di level atas
            proxy_headers=True,
            forwarded_allow_ips=FORWARDED_ALLOW_IPS,
        )
    except Exception as exc:
        logger.critical("Digital Twin subprocess crashed: %s", exc, exc_info=True)
        sys.exit(1)


def run_ai_layer() -> None:
    os.environ['FASTRA_DATABASE_URL'] = os.getenv('FASTRA_AI_DB_URL', 'sqlite:///fastra_ai_dev.db')
    """Menjalankan API AI Layer Secure Server."""
    try:
        uvicorn.run(
            "api_ai:app",
            host="0.0.0.0",
            port=AI_LAYER_PORT,
            log_level="info",
            workers=1,
            proxy_headers=True,
            forwarded_allow_ips=FORWARDED_ALLOW_IPS,
        )
    except Exception as exc:
        logger.critical("AI Layer subprocess crashed: %s", exc, exc_info=True)
        sys.exit(1)


# ------------------------------------------------------------------------------
# 2. HEALTH CHECK UTILITY
# ------------------------------------------------------------------------------
def _wait_for_port(port: int, timeout: float = 30.0) -> bool:
    """Tunggu hingga port siap menerima koneksi (health check sederhana)."""
    import socket

    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                return True
        except OSError:
            time.sleep(0.5)
    return False


# ------------------------------------------------------------------------------
# 3. CONTROLLER / ORCHESTRATOR
# ------------------------------------------------------------------------------
def main() -> None:
    """Fungsi utama untuk mengelola siklus hidup proses multiprosesor FASTRA."""
    if sys.platform != "win32":
        try:
            multiprocessing.set_start_method("spawn", force=True)
        except RuntimeError as exc:
            logger.warning("Gagal set start method spawn: %s", exc)

    load_dotenv()

    # Validasi environment (fail-fast)
    env_state = os.getenv("FASTRA_ENV", "development").strip().lower()
    secret_key = os.getenv("FASTRA_DT_SECRET_KEY", "").strip()
    api_key = os.getenv("FASTRA_DT_API_KEY", "").strip()

    if env_state == "production":
        if not secret_key or "change-me" in secret_key or len(secret_key) < 32:
            logger.critical("FASTRA_DT_SECRET_KEY is insecure for production. Aborting.")
            sys.exit(1)
        if not api_key or "change-me" in api_key or len(api_key) < 16:
            logger.critical("FASTRA_DT_API_KEY is insecure for production. Aborting.")
            sys.exit(1)

    # Daftar proses
    processes: List[multiprocessing.Process] = [
        multiprocessing.Process(target=run_digital_twin, name="FASTRA-DigitalTwin"),
        multiprocessing.Process(target=run_ai_layer, name="FASTRA-AI"),
    ]

    logger.info("Memulai inisialisasi subproses internal FASTRA...")

    for proc in processes:
        proc.start()

    # Tunggu sebentar agar server memiliki waktu untuk bind
    logger.info("Menunggu server siap...")

    dt_ready = _wait_for_port(DIGITAL_TWIN_PORT)
    ai_ready = _wait_for_port(AI_LAYER_PORT)

    if not dt_ready or not ai_ready:
        logger.error(
            "Salah satu server gagal start (DT ready=%s, AI ready=%s). Terminasi.",
            dt_ready,
            ai_ready,
        )
        for proc in processes:
            if proc.is_alive():
                proc.terminate()
        for proc in processes:
            proc.join(timeout=5)
        sys.exit(1)

    logger.info("============================================================")
    logger.info("FASTRA Security Architecture Production-Ready Infrastructure")
    logger.info("  - Digital Twin Secure Gateway : http://127.0.0.1:%d", DIGITAL_TWIN_PORT)
    logger.info("  - AI Layer Secure Engine       : http://127.0.0.1:%d", AI_LAYER_PORT)
    logger.info("============================================================")
    logger.info("Tekan Ctrl+C untuk melakukan terminasi server secara aman.")

    # Install signal handler untuk SIGTERM dan SIGINT
    stop_event = multiprocessing.Event()

    def _signal_handler(signum, frame):
        logger.info("Sinyal %s diterima, memulai shutdown...", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not stop_event.is_set():
            # Cek kesehatan proses
            for proc in processes:
                if not proc.is_alive():
                    logger.error("Subprocess %s mati mendadak.", proc.name)
                    stop_event.set()
                    break
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt diterima.")
    finally:
        logger.info("Memulai pembersihan proses...")
        # Kirim SIGTERM ke semua proses anak
        for proc in processes:
            if proc.is_alive():
                logger.info("Mengirim sinyal terminasi ke %s...", proc.name)
                proc.terminate()

        # Beri waktu untuk graceful shutdown
        for proc in processes:
            proc.join(timeout=10.0)
            if proc.is_alive():
                logger.warning("Subprocess %s tidak berhenti, paksa kill.", proc.name)
                proc.kill()
                proc.join()

        logger.info("Seluruh kluster server FASTRA berhasil dihentikan secara aman.")


if __name__ == "__main__":
    main()

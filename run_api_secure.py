"""
FASTRA Production Web Server Bootstrapper
Menjalankan API Digital Twin Secure dengan Uvicorn secara aman.
Mendukung enkripsi TLS jika sertifikat disediakan via environment variables.
Dengan logging terstruktur, validasi ketat, dan penguncian proxy headers.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logger = logging.getLogger("fastra_core.web_server")
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
DEFAULT_WORKERS = 4
DEFAULT_FORWARDED_ALLOW_IPS = "127.0.0.1"  # Hanya izinkan dari loopback/reverse proxy lokal


# ------------------------------------------------------------------------------
# 1. CONFIGURATION DOMAIN
# ------------------------------------------------------------------------------
class SecureServerConfigurationDomain:
    """Model representasi bisnis untuk validasi parameter runtime server web Uvicorn."""

    def __init__(self, raw_env: Dict[str, str]) -> None:
        self.host = raw_env.get("FASTRA_HOST", "0.0.0.0").strip()
        if not self.host:
            raise ValueError("host_cannot_be_empty")

        self.port = self._parse_port(raw_env.get("FASTRA_PORT", "8000"))
        self.workers = self._parse_workers(raw_env.get("FASTRA_WORKERS", str(DEFAULT_WORKERS)))
        self.forwarded_allow_ips = raw_env.get(
            "FASTRA_FORWARDED_ALLOW_IPS", DEFAULT_FORWARDED_ALLOW_IPS
        ).strip()

        # Validasi TLS: keduanya harus diisi atau kosong
        ssl_keyfile = self._validate_file_path(raw_env.get("FASTRA_SSL_KEYFILE"))
        ssl_certfile = self._validate_file_path(raw_env.get("FASTRA_SSL_CERTFILE"))

        if bool(ssl_keyfile) != bool(ssl_certfile):
            raise ValueError("both_ssl_keyfile_and_certfile_are_required_together")

        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile

        # Validasi mode produksi: tidak boleh menggunakan forwarded_allow_ips="*"
        env_state = raw_env.get("FASTRA_ENV", "development").strip().lower()
        if env_state == "production" and self.forwarded_allow_ips == "*":
            raise ValueError("wildcard_forwarded_allow_ips_is_forbidden_in_production")

    def _parse_port(self, port_str: str) -> int:
        try:
            port = int(str(port_str).strip())
            if port < 1024 or port > 65535:
                raise ValueError
            return port
        except (TypeError, ValueError):
            raise ValueError(f"invalid_port_number: {port_str}")

    def _parse_workers(self, workers_str: str) -> int:
        try:
            workers = int(str(workers_str).strip())
            if workers < 1 or workers > 16:  # batasi untuk mencegah overcommit
                raise ValueError
            return workers
        except (TypeError, ValueError):
            raise ValueError(f"invalid_workers_count: {workers_str}")

    def _validate_file_path(self, path_str: Optional[str]) -> Optional[str]:
        if path_str is None:
            return None
        clean_str = str(path_str).strip()
        if not clean_str:
            return None
        target_file = Path(clean_str).resolve()
        if not target_file.is_file():
            raise FileNotFoundError(f"target_cryptographic_file_missing: {clean_str}")
        return str(target_file)


# ------------------------------------------------------------------------------
# 2. CONTROLLER / INITIALIZATION ENTRYPOINT
# ------------------------------------------------------------------------------
def bootstrapper() -> None:
    """Inisialisasi utama penapis variabel lingkungan produksi peladen."""
    environment_payload = {
        "FASTRA_HOST": os.getenv("FASTRA_HOST", "0.0.0.0"),
        "FASTRA_PORT": os.getenv("FASTRA_PORT", "8000"),
        "FASTRA_WORKERS": os.getenv("FASTRA_WORKERS", str(DEFAULT_WORKERS)),
        "FASTRA_SSL_KEYFILE": os.getenv("FASTRA_SSL_KEYFILE", ""),
        "FASTRA_SSL_CERTFILE": os.getenv("FASTRA_SSL_CERTFILE", ""),
        "FASTRA_FORWARDED_ALLOW_IPS": os.getenv(
            "FASTRA_FORWARDED_ALLOW_IPS", DEFAULT_FORWARDED_ALLOW_IPS
        ),
        "FASTRA_ENV": os.getenv("FASTRA_ENV", "development"),
    }

    try:
        config = SecureServerConfigurationDomain(environment_payload)
    except Exception as exc:
        logger.critical("Fatal Fail-Fast Web Server Configuration Interruption: %s", exc)
        sys.exit(1)

    app_module_path = "fastra_core.api_digital_twin_secure:app"

    logger.info("Memulai server aman pada %s:%d (workers=%d)", config.host, config.port, config.workers)
    if config.ssl_certfile:
        logger.info("Protokol Keamanan Enkripsi TLS AKTIF.")
    else:
        logger.warning("TLS tidak aktif. Pastikan reverse proxy menangani SSL.")

    try:
        uvicorn.run(
            app_module_path,
            host=config.host,
            port=config.port,
            ssl_keyfile=config.ssl_keyfile,
            ssl_certfile=config.ssl_certfile,
            reload=False,
            workers=config.workers,
            proxy_headers=True,
            forwarded_allow_ips=config.forwarded_allow_ips,
            server_header=False,
            date_header=False,
        )
    except Exception as runtime_exc:
        logger.critical("Critical execution error in Uvicorn Engine: %s", runtime_exc)
        sys.exit(1)


if __name__ == "__main__":
    bootstrapper()
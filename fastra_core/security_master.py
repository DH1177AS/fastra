# fastra_core\security_master.py

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastra_security.auth.local_auth import (
    setup_master_password,
    verify_master_password,
    generate_totp_secret,
    verify_totp,
    generate_totp_qr_base64,
)
from fastra_security.audit.append_only_log import SecureAuditLog
from fastra_security.crypto.file_vault import generate_file_key, encrypt_file, decrypt_file
from fastra_security.runtime.anti_debug import anti_debug_check
from fastra_security.runtime.memory_guard import secure_string, wipe_string

logger = logging.getLogger("fastra_core.security_master")

PRODUCTION_ENV_TOKEN = "production"


class MasterSecurity(BaseModel):
    """
    Pintu Masuk Orkestrasi Utama Sistem Keamanan Tingkat Tinggi FASTRA (Security Master).
    Menangani orkestrasi otorisasi multi-faktor, kriptografi brankas berkas,
    dan mekanisme perlindungan memori runtime anti-debugging.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
        strict=True,
        extra="forbid",
        allow_inf_nan=False,
    )

    master_hash: bytes = Field(..., description="Hash satu arah dari kata sandi master")
    audit_log: Any = Field(..., description="Instansiasi mesin SecureAuditLog append-only terenkripsi")
    file_key: bytes = Field(..., description="Kunci kriptografis simetris untuk enkripsi berkas brankas")

    @field_validator("master_hash", "file_key", mode="after")
    @classmethod
    def validate_bytes_fields(cls, value: Any) -> bytes:
        if not isinstance(value, bytes) or len(value) == 0:
            logger.error("SECURITY_MASTER_BYTES_FIELD_INVALID: %r", value)
            raise ValueError("FIELD_MUST_BE_NON_EMPTY_BYTES")
        return value

    @field_validator("audit_log", mode="after")
    @classmethod
    def validate_audit_log_type(cls, value: Any) -> Any:
        if not isinstance(value, SecureAuditLog):
            logger.error("AUDIT_LOG_MUST_BE_SECURE_AUDIT_LOG_INSTANCE: %r", type(value).__name__)
            raise TypeError("AUDIT_LOG_MUST_BE_AN_INSTANCE_OF_SECURE_AUDIT_LOG")
        return value

    @classmethod
    def initialize_master_subsystem(
        cls,
        master_password: Optional[str] = None,
        audit_log_path: str = "audit/secure_audit.log",
    ) -> "MasterSecurity":
        """
        Named constructor formal untuk merakit sistem keamanan utama secara atomik.
        Mengeksekusi penapisan entropi kunci rahasia dan pembersihan memori string mentah.
        """
        # Ambil password dari argumen atau env
        raw_password = master_password or os.getenv("FASTRA_MASTER_PASSWORD", "")
        if not isinstance(raw_password, str) or not raw_password.strip():
            logger.error("MASTER_PASSWORD_MISSING_OR_EMPTY")
            raise ValueError("SECURITY_MASTER_ERROR: Environment variable 'FASTRA_MASTER_PASSWORD' is not configured.")

        clean_password = raw_password.strip()
        if len(clean_password) < 12:
            logger.error("MASTER_PASSWORD_ENTROPY_VIOLATION")
            raise ValueError(
                "SECURITY_MASTER_ERROR: Master password entropy policy violation. Minimum required length is 12 characters."
            )

        # Audit secret check
        audit_secret = os.getenv("FASTRA_MASTER_AUDIT_SECRET", "")
        if not isinstance(audit_secret, str) or not audit_secret.strip():
            logger.error("AUDIT_SECRET_MISSING_OR_EMPTY")
            raise ValueError(
                "CRITICAL_SECURITY_VIOLATION: 'FASTRA_MASTER_AUDIT_SECRET' is missing or empty."
            )
        if audit_secret.strip() == "change-me-secret-key":
            logger.error("AUDIT_SECRET_DEFAULT_INSECURE")
            raise ValueError(
                "CRITICAL_SECURITY_VIOLATION: Insecure or default key identified within "
                "'FASTRA_MASTER_AUDIT_SECRET'. Production deployment initialization terminated."
            )

        if not isinstance(audit_log_path, str) or not audit_log_path.strip():
            logger.error("AUDIT_LOG_PATH_EMPTY")
            raise ValueError("AUDIT_LOG_PATH_CANNOT_BE_EMPTY_OR_WHITESPACE")

        password_bytes = clean_password.encode("utf-8")
        clean_password_copy = clean_password  # keep for hashing below

        try:
            # 1. Hitung hash password master
            computed_hash: bytes = setup_master_password(clean_password_copy)

            # 2. Inisialisasi audit log
            computed_audit_log = SecureAuditLog(audit_log_path.strip(), audit_secret.strip())

            # 3. Generate file key
            computed_file_key: bytes = generate_file_key(clean_password_copy)

            instance = cls(
                master_hash=computed_hash,
                audit_log=computed_audit_log,
                file_key=computed_file_key,
            )
            logger.info("Master security subsystem initialized successfully")
            return instance

        finally:
            # Pembersihan memori mutlak
            if "password_bytes" in locals():
                wipe_string(password_bytes)
            # Hapus referensi lokal terhadap password plaintext
            del clean_password_copy
            del clean_password
            del raw_password

    def verify_master(self, password: str) -> bool:
        """
        Memverifikasi keabsahan masukan kata sandi master terhadap hash simpanan.
        """
        if not isinstance(password, str):
            logger.error("VERIFY_MASTER_PASSWORD_NOT_STRING")
            raise TypeError("PASSWORD_PARAMETER_MUST_BE_A_PURE_STRING")

        password_bytes = password.encode("utf-8")
        try:
            result = bool(verify_master_password(password, self.master_hash))
            logger.debug("Master password verification result: %s", result)
            return result
        finally:
            wipe_string(password_bytes)

    def generate_totp_secret(self) -> str:
        """
        Menghasilkan kunci rahasia baru untuk pembuatan Token Otentikasi Dua Faktor (TOTP Secret).
        """
        secret = str(generate_totp_secret())
        logger.debug("Generated new TOTP secret")
        return secret

    def verify_totp(self, secret: str, code: str) -> bool:
        """
        Memverifikasi token MFA (TOTP Code) temporal yang dikirimkan oleh operator.
        """
        if not isinstance(secret, str) or not isinstance(code, str):
            logger.error("TOTP_PARAMS_NOT_STRINGS")
            raise TypeError("TOTP_PARAMETERS_MUST_BE_PURE_STRINGS")
        result = bool(verify_totp(secret.strip(), code.strip()))
        logger.debug("TOTP verification result: %s", result)
        return result

    def generate_totp_qr(self, secret: str, username: str) -> str:
        if not isinstance(secret, str) or not isinstance(username, str):
            logger.error("TOTP_QR_PARAMS_NOT_STRINGS")
            raise TypeError("TOTP_QR_PARAMETERS_MUST_BE_PURE_STRINGS")
        qr_b64 = str(generate_totp_qr_base64(secret.strip(), username.strip()))
        logger.debug("Generated TOTP QR code for user %s", username)
        return qr_b64

    def audit(self, user: str, action: str, details: Dict[str, Any]) -> None:
        """
        Mencatatkan rekaman aktivitas pengguna menuju berkas Secure Log append-only terenkripsi.
        """
        if not isinstance(user, str) or not isinstance(action, str) or not isinstance(details, dict):
            logger.error("AUDIT_TRAIL_INVALID_PARAM_TYPES")
            raise TypeError("AUDIT_TRAIL_PARAMETERS_CONTAIN_INVALID_DATA_TYPES")

        clean_user = re.sub(r"[\r\n]", " ", user).strip()
        clean_action = re.sub(r"[\r\n]", " ", action).strip()

        if not clean_user or not clean_action:
            logger.error("AUDIT_TRAIL_IDENTITY_TOKENS_EMPTY")
            raise ValueError("AUDIT_TRAIL_IDENTITY_TOKENS_CANNOT_BE_EMPTY")

        self.audit_log.add_entry(clean_user, clean_action, details)
        logger.debug("Audit entry added: user=%s action=%s", clean_user, clean_action)

    def verify_audit_integrity(self) -> bool:
        """
        Memverifikasi keabsahan tanda tangan kriptografis rangkaian baris log berkas audit secara real-time.
        """
        result = bool(self.audit_log.verify_integrity())
        if not result:
            logger.error("AUDIT_INTEGRITY_VERIFICATION_FAILED")
        return result

    def encrypt_file(self, file_path: str) -> str:
        """
        Mengeksekusi enkripsi berkas penampung (Vault Encryption) menggunakan kunci simetris terikat.
        """
        if not isinstance(file_path, str) or not file_path.strip():
            logger.error("FILE_PATH_EMPTY_OR_WHITESPACE")
            raise ValueError("FILE_PATH_CANNOT_BE_EMPTY_OR_WHITESPACE")
        encrypted_path = str(encrypt_file(file_path.strip(), self.file_key))
        logger.info("File encrypted: %s -> %s", file_path, encrypted_path)
        return encrypted_path

    def decrypt_file(self, enc_path: str) -> str:
        """
        Mengeksekusi dekripsi berkas penampung (Vault Decryption) secara terisolasi.
        """
        if not isinstance(enc_path, str) or not enc_path.strip():
            logger.error("ENC_PATH_EMPTY_OR_WHITESPACE")
            raise ValueError("ENCRYPTED_FILE_PATH_CANNOT_BE_EMPTY_OR_WHITESPACE")
        decrypted_path = str(decrypt_file(enc_path.strip(), self.file_key))
        logger.info("File decrypted: %s -> %s", enc_path, decrypted_path)
        return decrypted_path

    def secure_string(self, data: bytes) -> bytes:
        if not isinstance(data, bytes):
            logger.error("SECURE_STRING_DATA_NOT_BYTES")
            raise TypeError("DATA_MUST_BE_PROVIDED_IN_RAW_BYTES_FORMAT")
        return bytes(secure_string(data))

    def wipe_string(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            logger.error("WIPE_STRING_DATA_NOT_BYTES")
            raise TypeError("DATA_MUST_BE_PROVIDED_IN_RAW_BYTES_FORMAT")
        wipe_string(data)

    def runtime_check(self) -> None:
        """
        Mengeksekusi pengujian berkala terhadap integritas lingkungan proses aplikasi (Runtime Anti-Tampering).
        Mengaktifkan proteksi anti-debugging secara ketat di lingkungan produksi.
        """
        environment_token = str(os.getenv("FASTRA_ENV", "development")).strip().lower()
        if environment_token == PRODUCTION_ENV_TOKEN:
            # Memanggil mesin pertahanan murni untuk mendeteksi perasukan gancu proses (GDB/PTrace attachments)
            anti_debug_check()
            logger.info("Runtime anti-debug check passed in production environment")
        else:
            logger.debug("Runtime anti-debug check skipped (non-production)")

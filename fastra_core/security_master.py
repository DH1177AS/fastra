"""
Integrasi Master Fastra Security ke FASTRA.
Menyediakan master password, TOTP, audit file, file vault, dan runtime protection.
"""
from __future__ import annotations

import os
from typing import Optional

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


class MasterSecurity:
    """Pintu masuk utama untuk fitur keamanan lanjutan FASTRA."""

    def __init__(self, master_password: Optional[str] = None, audit_log_path: str = "audit/secure_audit.log") -> None:
        self.master_password = master_password or os.getenv("FASTRA_MASTER_PASSWORD", "")
        if not self.master_password:
            raise ValueError("FASTRA_MASTER_PASSWORD tidak diatur")
        self.master_hash = setup_master_password(self.master_password)
        secret = os.getenv("FASTRA_MASTER_AUDIT_SECRET", "change-me-secret-key")
        self.audit_log = SecureAuditLog(audit_log_path, secret)
        self.file_key = generate_file_key(self.master_password)

    def verify_master(self, password: str) -> bool:
        return verify_master_password(password, self.master_hash)

    def generate_totp_secret(self) -> str:
        return generate_totp_secret()

    def verify_totp(self, secret: str, code: str) -> bool:
        return verify_totp(secret, code)

    def generate_totp_qr(self, secret: str, username: str) -> str:
        return generate_totp_qr_base64(secret, username)

    def audit(self, user: str, action: str, details: dict) -> None:
        self.audit_log.add_entry(user, action, details)

    def verify_audit_integrity(self) -> bool:
        return self.audit_log.verify_integrity()

    def encrypt_file(self, file_path: str) -> str:
        return encrypt_file(file_path, self.file_key)

    def decrypt_file(self, enc_path: str) -> str:
        return decrypt_file(enc_path, self.file_key)

    def secure_string(self, data: bytes) -> bytes:
        return secure_string(data)

    def wipe_string(self, data: bytes) -> None:
        wipe_string(data)

    def runtime_check(self) -> None:
        if os.getenv("FASTRA_ENV") == "production":
            anti_debug_check()

import hashlib, os, base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def derive_encryption_key(master_password: str, salt: bytes = None) -> bytes:
    if salt is None:
        salt = os.urandom(16)
    argon2_hash = hashlib.pbkdf2_hmac('sha256', master_password.encode(), salt, 200000)
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=b"fastra-db-enc", backend=default_backend())
    return hkdf.derive(argon2_hash)
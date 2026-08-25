from cryptography.fernet import Fernet
import hashlib, base64, os

def generate_file_key(master_password: str, salt: bytes = None) -> bytes:
    if salt is None:
        salt = os.urandom(16)
    kdf = hashlib.pbkdf2_hmac('sha256', master_password.encode(), salt, 100000)
    return base64.urlsafe_b64encode(kdf)

def encrypt_file(file_path: str, key: bytes) -> str:
    f = Fernet(key)
    with open(file_path, 'rb') as file:
        original = file.read()
    encrypted = f.encrypt(original)
    enc_path = file_path + ".enc"
    with open(enc_path, 'wb') as file:
        file.write(encrypted)
    os.remove(file_path)
    return enc_path

def decrypt_file(enc_path: str, key: bytes) -> str:
    f = Fernet(key)
    with open(enc_path, 'rb') as file:
        encrypted = file.read()
    decrypted = f.decrypt(encrypted)
    original_path = enc_path.replace(".enc", "")
    with open(original_path, 'wb') as file:
        file.write(decrypted)
    os.remove(enc_path)
    return original_path
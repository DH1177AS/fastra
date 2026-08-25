from passlib.context import CryptContext
import pyotp, qrcode
from io import BytesIO
import base64

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def setup_master_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_master_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(secret: str, username: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="Fastra")

def generate_totp_qr_base64(secret: str, username: str) -> str:
    uri = get_totp_uri(secret, username)
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
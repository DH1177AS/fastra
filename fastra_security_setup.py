from setuptools import setup, find_packages

setup(
    name="fastra-security",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "aiosqlite",
        "passlib[argon2]",
        "python-jose",
        "cryptography",
        "loguru",
        "slowapi",
        "qrcode",
        "pyotp",
        "pillow",
    ],
    python_requires=">=3.11",
)
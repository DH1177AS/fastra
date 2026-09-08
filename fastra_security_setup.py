"""
Setup configuration metadata for the FASTRA Security Backend Package.
Strictly enforced dependencies, modern secure cryptographic backends, and zero legacy bloat.
"""

from __future__ import annotations

import sys
from pathlib import Path

from setuptools import find_packages, setup

# ------------------------------------------------------------------------------
# Fail-fast Python version enforcement
# ------------------------------------------------------------------------------
if sys.version_info < (3, 11):
    sys.exit("FASTRA Security requires Python 3.11 or higher")

# ------------------------------------------------------------------------------
# Long description from README (if present)
# ------------------------------------------------------------------------------
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="fastra-security",
    version="1.0.0",
    description="FASTRA military-grade security backend for construction estimation platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FASTRA Engineering",
    author_email="security@fastra.local",
    url="https://fastra.local",
    license="Proprietary",
    packages=find_packages(
        include=["fastra_security", "fastra_security.*"],
        exclude=["tests", "tests.*", "docs", "docs.*"],
    ),
    install_requires=[
        # Web framework
        "fastapi>=0.110.0,<1.0.0",
        "uvicorn[standard]>=0.29.0,<0.30.0",
        # Database
        "sqlalchemy>=2.0.25,<3.0.0",
        "aiosqlite>=0.20.0,<0.21.0",
        # Cryptography & authentication
        "argon2-cffi>=23.1.0,<24.0.0",
        "PyJWT>=2.8.0,<3.0.0",
        "cryptography>=42.0.0,<43.0.0",
        # Structured logging
        "structlog>=24.1.0,<25.0.0",
        # Rate limiting
        "slowapi>=0.1.9,<0.2.0",
        # Two-factor authentication support
        "qrcode>=7.4.2,<8.0.0",
        "pyotp>=2.9.0,<3.0.0",
        "pillow>=10.2.0,<11.0.0",
        # Validation
        "pydantic>=2.6.0,<3.0.0",
    ],
    extras_require={
        # Optional Redis support for distributed rate limiting/caching
        "redis": ["redis>=5.0.0,<6.0.0"],
        # Development and security auditing tools
        "dev": [
            "pytest>=8.0.0,<9.0.0",
            "mypy>=1.8.0,<2.0.0",
            "bandit>=1.7.7,<2.0.0",
            "ruff>=0.3.0,<0.4.0",
        ],
    },
    python_requires=">=3.11",
    zip_safe=False,
    include_package_data=True,
    package_data={
        "fastra_security": [
            "py.typed",
            "*.json",
            "*.pem",
            "*.key",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: Other/Proprietary License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
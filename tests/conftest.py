import os
import warnings
warnings.filterwarnings(
    "ignore",
    message=r".*default datetime adapter.*",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r".*HMAC key is.*",
    category=Warning,
    module=r"jwt\.api_jwt"
)

# Set environment variables BEFORE any test module is imported
os.environ.setdefault("FASTRA_DT_ADMIN_PASSWORD", "dummy_admin_pass_123!")
os.environ.setdefault("FASTRA_DT_API_KEY", "dummy_api_key_1234567890abcdef")
os.environ.setdefault("FASTRA_DT_QS_PASSWORD", "dummy_qs_pass_123!")
os.environ.setdefault("FASTRA_DT_SECRET_KEY", "dummy_secret_key_1234567890123456789012345678901234567890")
os.environ.setdefault("FASTRA_DT_VIEWER_PASSWORD", "dummy_viewer_pass_123!")
os.environ.setdefault("FASTRA_ENV", "testing")
os.environ.setdefault("FASTRA_DATABASE_URL", "sqlite:///./fastra_test.db")
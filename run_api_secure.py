"""
Menjalankan API Digital Twin Secure dengan Uvicorn.
Mendukung SSL jika sertifikat disediakan via environment variables.
"""
import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("FASTRA_HOST", "0.0.0.0")
    port = int(os.getenv("FASTRA_PORT", "8000"))
    ssl_keyfile = os.getenv("FASTRA_SSL_KEYFILE")
    ssl_certfile = os.getenv("FASTRA_SSL_CERTFILE")
    uvicorn.run(
        "api_digital_twin_secure:app",
        host=host,
        port=port,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload=False,
    )

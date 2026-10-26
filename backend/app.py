"""
CustomerVault Application Entry Point (app.py)
Allows running `python backend/app.py` directly.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import os
    import uvicorn
    is_cloud = bool(os.environ.get("PORT") or os.environ.get("RENDER"))
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0" if is_cloud else "127.0.0.1")
    browser_host = "localhost" if host == "0.0.0.0" else host
    print(f"Starting CustomerVault on http://{browser_host}:{port} ...")
    uvicorn.run("main:app", host=host, port=port, reload=False, app_dir=str(backend_dir))
else:
    from main import app  # noqa: F401

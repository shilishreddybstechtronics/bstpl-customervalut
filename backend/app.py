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
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting CustomerVault on http://{host}:{port} ...")
    uvicorn.run("main:app", host=host, port=port, reload=False, app_dir=str(backend_dir))
else:
    from main import app  # noqa: F401

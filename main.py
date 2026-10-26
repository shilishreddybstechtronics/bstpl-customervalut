"""
CustomerVault Root Entrypoint
Allows running:
    python -m uvicorn main:app
    uvicorn main:app --reload
directly from the project root directory without needing --app-dir backend.
"""
import importlib.util
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load the FastAPI app from backend/main.py
spec = importlib.util.spec_from_file_location("backend_app_module", BACKEND_DIR / "main.py")
backend_module = importlib.util.module_from_spec(spec)
sys.modules["backend_app_module"] = backend_module
spec.loader.exec_module(backend_module)

app = backend_module.app

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting CustomerVault on http://{host}:{port} ...")
    uvicorn.run("main:app", host=host, port=port, reload=False)

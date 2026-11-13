"""
CustomerVault Root Entrypoint (main.py)
Allows running:
    python -m uvicorn main:app
    uvicorn main:app --reload
directly from the project root directory without needing --app-dir backend.
"""
import importlib.util
import sys
from pathlib import Path

# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Establish Project Root and Backend Directory Paths:
# Resolves the repository root and backend directories, then adds the backend
# directory to sys.path so modules like 'models', 'database', and 'auth' can be
# imported without path errors.
# ==============================================================================
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Dynamic Module Loading:
# Loads backend/main.py as a module under the name 'backend_app_module' and
# extracts the instantiated FastAPI application object ('app'). This allows
# cloud servers (Render, Procfile, Docker) and local CLI commands to target
# `main:app` directly from the project root.
# ==============================================================================
spec = importlib.util.spec_from_file_location("backend_app_module", BACKEND_DIR / "main.py")
backend_module = importlib.util.module_from_spec(spec)
sys.modules["backend_app_module"] = backend_module
spec.loader.exec_module(backend_module)

# Expose the FastAPI app instance to ASGI servers
app = backend_module.app


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Port Conflict Protection:
# Tests socket binding sequentially from `starting_port` upwards. If port 8000
# is in use by another instance or system service, it finds the next open port
# (e.g. 8001, 8002) so the server never crashes on startup.
# ==============================================================================
def find_available_port(host: str, starting_port: int, max_attempts: int = 20) -> int:
    import socket
    for p in range(starting_port, starting_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, p))
                return p
            except OSError:
                continue
    return starting_port


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Direct Execution Runner:
# When executing `python main.py` directly from the project root:
# 1. Reads cloud environment variables ($PORT and $RENDER).
# 2. Configures the network host (0.0.0.0 in cloud, 127.0.0.1 locally).
# 3. Chooses the port (cloud port or first free local port).
# 4. Boots the Uvicorn ASGI server.
# ==============================================================================
if __name__ == "__main__":
    import os
    import uvicorn

    # Cloud environment detection (Render, Railway, etc.)
    is_cloud = bool(os.environ.get("PORT") or os.environ.get("RENDER"))
    env_port = os.environ.get("PORT")
    host = os.environ.get("HOST", "0.0.0.0" if is_cloud else "127.0.0.1")

    # Port allocation logic
    if env_port:
        port = int(env_port)
    else:
        req_port = 8000
        port = find_available_port(host, req_port)
        if port != req_port:
            print(f"\n⚠️  Port {req_port} is already in use by another process.")
            print(f"👉 Automatically switching to free port {port}.")
            print(f"   (To use port {req_port}, stop the other process occupying it)\n")

    browser_host = "localhost" if host == "0.0.0.0" else host
    print(f"Starting CustomerVault on http://{browser_host}:{port} ...")
    uvicorn.run("main:app", host=host, port=port, reload=False)

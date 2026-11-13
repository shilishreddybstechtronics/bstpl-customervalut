"""
CustomerVault Application Entry Point (app.py)
Allows running `python backend/app.py` directly from terminal or IDE.
"""
import sys
import socket
from pathlib import Path

# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Resolve the absolute path of the backend directory and inject it into Python's
# sys.path module lookup list. This ensures all internal imports (e.g. `import models`,
# `import database`, `from auth import ...`) resolve smoothly whether app.py is invoked
# from inside the backend directory or from the root repository folder.
# ==============================================================================
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Automated Port Availability Checker:
# Probes network sockets starting from `starting_port` (default: 8000) up to
# `starting_port + max_attempts`. If another process (e.g. orphan python, IIS,
# Docker) already occupies port 8000, this function intercepts the collision and
# returns the first verified open port to prevent socket access errors ([WinError 10013]).
# ==============================================================================
def find_available_port(host: str, starting_port: int, max_attempts: int = 20) -> int:
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
# Server Startup Execution Block:
# When app.py is executed as the main script:
# 1. Detects cloud hosting environment variables (e.g. Render assigns $PORT and $RENDER).
# 2. Defaults to host 0.0.0.0 for cloud or 127.0.0.1 for local safe development.
# 3. Allocates the target port (using $PORT if present, or finding an available port).
# 4. Launches the Uvicorn ASGI server with live reloading enabled for rapid development.
# ==============================================================================
if __name__ == "__main__":
    import os
    import uvicorn

    # Check whether running in cloud environment (e.g. Render, Railway)
    is_cloud = bool(os.environ.get("PORT") or os.environ.get("RENDER"))
    env_port = os.environ.get("PORT")
    host = os.environ.get("HOST", "0.0.0.0" if is_cloud else "127.0.0.1")

    # Determine port: use cloud-provided port or dynamically allocate a free port
    if env_port:
        port = int(env_port)
    else:
        req_port = 8000
        port = find_available_port(host, req_port)
        if port != req_port:
            print(f"\n⚠️  Port {req_port} is already in use by another process.")
            print(f"👉 Automatically switching to free port {port}.")
            print(f"   (To use port {req_port}, stop the process occupying it)\n")

    browser_host = "localhost" if host == "0.0.0.0" else host
    print(f"Starting CustomerVault on http://{browser_host}:{port} ...")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        app_dir=str(backend_dir),
        reload_excludes=[
            "*.log",
            "*.json",
            "*.xlsx",
            "*.env",
            "*.bak",
            "*_cache*",
            "logs/*",
            "sensorise/logs/*",
            "telematics_cache.json"
        ]
    )
else:
    # Expose FastAPI 'app' instance for external ASGI runners (gunicorn, uvicorn CLI)
    from main import app  # noqa: F401

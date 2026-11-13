#!/usr/bin/env python3
"""
CustomerVault Application Entry Point (app.py)
Allows running directly from repository root:
    app.py --host 0.0.0.0 --port $PORT
    python app.py --host 0.0.0.0 --port $PORT
    uvicorn app:app --host 0.0.0.0 --port $PORT
"""
import os
import sys
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Expose FastAPI 'app' instance
from main import app  # noqa: F401


def run():
    import uvicorn
    parser = argparse.ArgumentParser(description="CustomerVault Server Runner")
    parser.add_argument("--host", default=None, help="Host interface to bind")
    parser.add_argument("--port", type=int, default=None, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", default=None, help="Enable auto-reload")
    args, _ = parser.parse_known_args()

    is_cloud = bool(os.environ.get("PORT") or os.environ.get("RENDER"))
    env_port = os.environ.get("PORT")
    host = args.host or os.environ.get("HOST", "0.0.0.0" if is_cloud else "127.0.0.1")
    port = args.port or (int(env_port) if env_port else 8000)
    do_reload = args.reload if args.reload is not None else (not is_cloud)

    print(f"Starting CustomerVault on http://{host}:{port} ...")
    uvicorn.run("app:app", host=host, port=port, reload=do_reload)


if __name__ == "__main__":
    run()


"""
Vercel Serverless Function Entrypoint for CustomerVault FastAPI backend.
Vercel detects any Python file in api/ and routes requests to the `app` instance.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path so all internal imports (models, auth, etc.) resolve
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the FastAPI instance
from main import app  # noqa: F401, E402

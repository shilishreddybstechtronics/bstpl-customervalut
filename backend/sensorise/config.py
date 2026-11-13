import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

def _read_env_key(key: str, default: str = "") -> str:
    """Reads a key from environment, falling back to reading .env directly."""
    val = os.getenv(key)
    if val and val.strip():
        return val.strip()
    sensorise_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(sensorise_dir, ".."))
    project_root = os.path.abspath(os.path.join(backend_dir, ".."))
    for env_path in [
        os.path.join(sensorise_dir, ".env"),
        os.path.join(backend_dir, ".env"),
        os.path.join(project_root, ".env"),
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith(f"{key}="):
                            v = line.strip().split("=", 1)[1].strip()
                            if v:
                                return v
            except Exception:
                pass
    return default

# ==============================================================================
# MySQL / TiDB Cloud Database Configuration
# ==============================================================================

DB_USER = _read_env_key("DB_USER", os.getenv("DB_USER") or "2qvzCb4ckY28YTR.root")
DB_PASSWORD = _read_env_key("DB_PASSWORD", os.getenv("DB_PASSWORD") or "TkUlyIt79g9JLww0")
DB_HOST = _read_env_key("DB_HOST", os.getenv("DB_HOST") or "gateway01.ap-northeast-1.prod.aws.tidbcloud.com")
DB_PORT = int(_read_env_key("DB_PORT", os.getenv("DB_PORT") or "4000") or 4000)
DB_NAME = _read_env_key("DB_NAME", os.getenv("DB_NAME") or "customer_database")

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# ==============================================================================
# Sensorise SenseLCM Company Server Configuration (Production)
# ==============================================================================
SENSORISE_PROD_BASE_URL = "https://senselcm.sensorise.net/sense-lcm-services-prod"
SENSORISE_PROD_URL = "https://senselcm.sensorise.net/sense-lcm-services-prod/checkSIMBulk/v2/"
SENSORISE_PROD_RELATION_ID = "SENSE1019"
SENSORISE_PROD_SHARED_KEY = "$2a$10$b1f9QK4O6/iXj7TUxhhEhOVPeyoZNK7NMbPhqpS66R9RVfW7Lzu2K"

# Backward compatibility aliases
SENSORISE_UAT_URL = SENSORISE_PROD_URL
SENSORISE_UAT_SHARED_KEY = SENSORISE_PROD_SHARED_KEY

# Active Environment & Settings (Production)
SENSORISE_ENV = os.getenv("SENSORISE_ENV", "PROD").upper()
SENSORISE_SERVER_URL = _read_env_key("SENSORISE_SERVER_URL", SENSORISE_PROD_URL).rstrip("/")
SENSORISE_RELATION_ID = _read_env_key("SENSORISE_RELATION_ID", SENSORISE_PROD_RELATION_ID)
SENSORISE_SHARED_KEY = _read_env_key("SENSORISE_SHARED_KEY", SENSORISE_PROD_SHARED_KEY)

# Official SenseLCM Service Endpoints
ENDPOINT_GENERATE_API_TOKEN = "generateAPIToken"
ENDPOINT_CHECK_SIM_BULK_V1 = "checkSIMBulk/v1/"
ENDPOINT_CHECK_SIM_BULK_V2 = "checkSIMBulk/v2/"

# Complete Endpoint URLs
SENSORISE_PROD_BULK_V2_URL = f"{SENSORISE_PROD_BASE_URL.rstrip('/')}/checkSIMBulk/v2/"
SENSORISE_PROD_TOKEN_URL = f"{SENSORISE_PROD_BASE_URL.rstrip('/')}/generateAPIToken"

# Auth fields
SENSORISE_API_KEY = _read_env_key("SENSORISE_API_KEY", SENSORISE_SHARED_KEY)
SENSORISE_AUTH_TOKEN = _read_env_key("SENSORISE_AUTH_TOKEN", "$2a$10$Tqgfc/ZUwm5YK2wVhkn3u.nLSwWv0pn.gbCKxij/x8Jl8fEUQCgD.")
SENSORISE_TOKEN_EXPIRY = _read_env_key("SENSORISE_TOKEN_EXPIRY", "2026-11-14 10:08:54")
SENSORISE_CLIENT_ID = os.getenv("SENSORISE_CLIENT_ID", SENSORISE_RELATION_ID)
SENSORISE_CLIENT_SECRET = os.getenv("SENSORISE_CLIENT_SECRET", SENSORISE_SHARED_KEY)
SENSORISE_ACCOUNT_ID = os.getenv("SENSORISE_ACCOUNT_ID", SENSORISE_RELATION_ID)

# ==============================================================================
# Basic Sensorise SIM list (Device SR No / IMEI / ICCID)
# ==============================================================================
BASIC_FILE_PATH = os.getenv(
    "BASIC_FILE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Sensorise_SIMs_basic.xlsx"),
)


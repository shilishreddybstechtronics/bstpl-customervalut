"""
BSTPL - FastAPI Backend Server
Provides REST API endpoints for database connectivity, file ingestion,
and MySQL storage with support for Excel (.xlsx/.xls), CSV, TSV, and JSON.
"""

import os
import sys
import platform

if sys.platform == "win32":
    if hasattr(platform, "_wmi_query"):
        def _fast_wmi_query(*args, **kwargs):
            raise OSError("WMI query disabled to prevent system wait timeouts")
        platform._wmi_query = _fast_wmi_query

    try:
        if not getattr(platform, "_uname_cache", None):
            import collections
            win_ver = sys.getwindowsversion()
            arch = os.environ.get("PROCESSOR_ARCHITECTURE", "AMD64")
            _Uname = collections.namedtuple(
                "uname_result",
                ["system", "node", "release", "version", "machine", "processor"]
            )
            platform._uname_cache = _Uname(
                system="Windows",
                node=os.environ.get("COMPUTERNAME", "localhost"),
                release=str(win_ver.major),
                version=f"{win_ver.major}.{win_ver.minor}.{win_ver.build}",
                machine=arch,
                processor=os.environ.get("PROCESSOR_IDENTIFIER", arch)
            )
    except Exception:
        pass

import io
import datetime
import asyncio
from typing import List, Any, Optional, Dict
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from starlette.types import ASGIApp, Scope, Receive, Send

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    from config import SERVER_HOST, SERVER_PORT
    import db
    import sensorise
    from sensorise import sensorise_client, SensoriseClient
    import app_logger
except ImportError:
    try:
        from backend.sensorise import config, db, sensorise, app_logger
        from backend.sensorise.config import SERVER_HOST, SERVER_PORT
        from backend.sensorise.sensorise import sensorise_client, SensoriseClient
    except ImportError:
        from sensorise import config, db, sensorise, app_logger
        from sensorise.config import SERVER_HOST, SERVER_PORT
        from sensorise.sensorise import sensorise_client, SensoriseClient

@asynccontextmanager
async def app_lifespan(app_instance: FastAPI):
    try:
        db.init_db()
        db.ensure_sensorise_basic_table()
    except Exception as e:
        print(f"[Notice] DB init on startup: {e}")
    try:
        yield
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        pass

app = FastAPI(
    title="BSTPL Sensorise Backend API",
    description="Python backend with MySQL database integration for file data inspection and Sensorise SenseLCM services.",
    version="1.0.0",
    lifespan=app_lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SafeCancellationMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        except Exception as exc:
            if "ClientDisconnect" in type(exc).__name__:
                pass
            else:
                raise exc

app.add_middleware(SafeCancellationMiddleware)

# Request Models
class SaveDataPayload(BaseModel):
    filename: str
    headers: List[str]
    rows: List[List[Any]]

class SensoriseConfigPayload(BaseModel):
    server_url: Optional[str] = None
    relation_id: Optional[str] = None
    shared_key: Optional[str] = None
    env: Optional[str] = None
    api_key: Optional[str] = None
    auth_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    account_id: Optional[str] = None

class TokenUpdatePayload(BaseModel):
    auth_token: str

class GenerateTokenPayload(BaseModel):
    relation_id: Optional[str] = None
    shared_key: Optional[str] = None
    access_key: Optional[str] = None
    token_validity: Optional[int] = 24
    token_transactions: Optional[int] = 100
    payload: Optional[Dict[str, Any]] = None

class ExecutePostPayload(BaseModel):
    endpoint: Optional[str] = "/checkSIMBulk/v2/"
    full_url: Optional[str] = None
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

class CheckSimBulkPayload(BaseModel):
    iccids: Optional[List[str]] = None
    version: Optional[str] = "v2"
    api_token: Optional[str] = None

class ICCIDSearchPayload(BaseModel):
    iccid: str
    mapping: Optional[Dict[str, str]] = None

class SensoriseSyncICCIDPayload(BaseModel):
    iccids: Optional[List[str]] = None

class SensoriseFetchPayload(BaseModel):
    count: Optional[int] = 100
    status_filter: Optional[str] = None
    save_to_db: Optional[bool] = True

class SensoriseSyncFilePayload(BaseModel):
    max_rows: Optional[int] = 500
    file_path: Optional[str] = None

class ColumnMappingPayload(BaseModel):
    mapping: Dict[str, str]

class InspectColumnsPayload(BaseModel):
    iccid: str

# Endpoints
@app.get("/api/status", tags=["System Health"])
def get_system_status():
    db_status = db.test_db_status()
    return {
        "backend": "online",
        "service": "BSTPL Sensorise Engine",
        "database": db_status
    }

@app.get("/api/logs/latest", tags=["System Health"])
def get_latest_diagnostic_log():
    return {
        "log_directories": app_logger.get_log_directories(),
        "latest_error": app_logger.get_latest_error_summary()
    }

@app.get("/api/sensorise/status", tags=["Authentication"])
@app.get("/api/sensorise/config", tags=["Authentication"])
def get_sensorise_status():
    conn_info = sensorise_client.test_connection()
    db_stats = db.get_sensorise_summary_stats()
    return {
        "server_status": conn_info,
        "database_stats": db_stats,
        "token_lifecycle": {
            "has_token": bool(sensorise_client.auth_token),
            "is_valid": sensorise_client.is_token_valid(),
            "transactions_remaining": sensorise_client.token_transactions_remaining,
            "expiry": sensorise_client.get_token_expiry(),
            "token": sensorise_client.auth_token
        },
        "config": {
            "server_url": sensorise_client.base_url,
            "relation_id": sensorise_client.relation_id,
            "has_shared_key": bool(sensorise_client.shared_key),
            "has_api_key": bool(sensorise_client.api_key),
            "has_auth_token": bool(sensorise_client.auth_token),
            "has_client_id": bool(sensorise_client.client_id)
        }
    }

@app.post("/api/sensorise/config", tags=["Authentication"])
def update_sensorise_config(payload: SensoriseConfigPayload):
    if payload.server_url is not None:
        sensorise_client.base_url = payload.server_url.rstrip("/")
    if payload.relation_id is not None:
        sensorise_client.relation_id = payload.relation_id
    if payload.shared_key is not None:
        sensorise_client.shared_key = payload.shared_key
    if payload.api_key is not None:
        sensorise_client.api_key = payload.api_key
    if payload.auth_token is not None:
        sensorise_client.auth_token = payload.auth_token
    elif payload.api_key is not None:
        sensorise_client.auth_token = payload.api_key
    if payload.client_id is not None:
        sensorise_client.client_id = payload.client_id
    if payload.client_secret is not None:
        sensorise_client.client_secret = payload.client_secret
    if payload.account_id is not None:
        sensorise_client.account_id = payload.account_id

    sensorise_client.save_config_to_env(
        server_url=payload.server_url,
        relation_id=payload.relation_id,
        shared_key=payload.shared_key,
        auth_token=payload.auth_token or payload.api_key
    )

    test_res = sensorise_client.test_connection()
    return {
        "success": True,
        "message": "Sensorise server configuration updated and persisted to .env file.",
        "config": {
            "server_url": sensorise_client.base_url,
            "relation_id": sensorise_client.relation_id,
            "has_shared_key": bool(sensorise_client.shared_key),
            "has_auth_token": bool(sensorise_client.auth_token)
        },
        "test_result": test_res
    }

@app.post("/api/sensorise/update-token-file", tags=["Authentication"])
def update_token_file(payload: TokenUpdatePayload):
    return sensorise_client.upload_or_update_token(payload.auth_token)

@app.get("/api/sensorise/test-connection", tags=["Authentication"])
@app.post("/api/sensorise/test-connection", tags=["Authentication"])
def test_sensorise_connection():
    return sensorise_client.test_connection()

@app.get("/api/sensorise/sensecrypt-key", tags=["Authentication"])
def get_sensecrypt_access_key(key: Optional[str] = None, date: Optional[str] = None, relation_id: Optional[str] = None):
    date_used = date or datetime.datetime.now().strftime("%Y%m%d")
    rel = relation_id or sensorise_client.relation_id or "SENSE1019"
    computed = sensorise_client.generate_sense_access_key(pre_shared_key=key, date_str=date_used, relation_id=rel)
    return {
        "accessKey": computed,
        "date_used": date_used,
        "relation_id": rel,
        "key_algorithm": "HMAC-SHA512 (SenseCrypt Java spec: formattedDate + relationId)"
    }

@app.post("/api/sensorise/generate-token", tags=["Authentication"])
def generate_sensorise_api_token(payload: Optional[GenerateTokenPayload] = None):
    rel_id = payload.relation_id if payload else None
    s_key = payload.shared_key if payload else None
    acc_key = payload.access_key if payload else None
    validity = payload.token_validity if payload and payload.token_validity else 24
    txns = payload.token_transactions if payload and payload.token_transactions else 100
    c_payload = payload.payload if payload else None
    return sensorise_client.generate_api_token(
        relation_id=rel_id,
        shared_key=s_key,
        access_key=acc_key,
        token_validity=validity,
        token_transactions=txns,
        custom_payload=c_payload
    )

@app.get("/api/sensorise/diagnose", tags=["Authentication"])
def diagnose_sensorise_connection():
    return sensorise_client.diagnose_connection()

@app.post("/api/sensorise/execute-post", tags=["Sensorise Services"])
def execute_inbuilt_sensorise_post(payload: ExecutePostPayload):
    return sensorise_client.execute_custom_post_request(
        endpoint=payload.endpoint,
        full_url=payload.full_url,
        body=payload.body,
        custom_headers=payload.headers
    )

@app.post("/api/sensorise/check-sim-bulk", tags=["Sensorise Services"])
def check_sensorise_sim_bulk(payload: Optional[CheckSimBulkPayload] = None):
    iccids = payload.iccids if payload and payload.iccids else None
    if not iccids:
        basic_records = db.get_sensorise_basic_records(limit=80, fetch_all=True)
        iccids = [r[2] for r in basic_records.get("rows", []) if len(r) > 2 and r[2]]

    ver = (payload.version if payload and payload.version else "v2").lower()
    tok = payload.api_token if payload else None
    if ver == "v1":
        res = sensorise_client.check_sim_bulk_v1(iccids=iccids)
    else:
        res = sensorise_client.check_sim_bulk_v2(iccids=iccids, api_token=tok)

    try:
        regen_res = sensorise_client.generate_api_token()
        if isinstance(res, dict) and regen_res.get("success"):
            res["token_regenerated"] = True
            res["apiToken"] = regen_res.get("apiToken")
            res["tokenExpiry"] = regen_res.get("tokenExpiry")
    except Exception:
        pass
    return res

@app.post("/api/sensorise/search-by-iccid", tags=["Sensorise Services"])
def search_sim_by_iccid(payload: ICCIDSearchPayload):
    return db.search_and_update_sim_by_iccid(payload.iccid, mapping=payload.mapping)

@app.post("/api/sensorise/sync-by-iccid", tags=["Sensorise Services"])
def sync_sensorise_by_iccid(payload: Optional[SensoriseSyncICCIDPayload] = None):
    iccids = payload.iccids if payload else None
    return db.sync_and_match_iccids_from_server(iccids=iccids)

@app.post("/api/sensorise/fetch-basic-telematics", tags=["Sensorise Services"])
def fetch_basic_telematics_from_server():
    return db.fetch_and_update_basic_sims_telematics()

@app.post("/api/sensorise/fetch-and-sync", tags=["Sensorise Services"])
def fetch_and_sync_sensorise(payload: SensoriseFetchPayload):
    fetch_count = payload.count or 100
    records = sensorise_client.fetch_sims_from_server(
        limit=fetch_count,
        status_filter=payload.status_filter
    )
    
    saved_to_db = False
    db_result = {}
    if payload.save_to_db and db.is_db_configured():
        db_result = db.upsert_sensorise_records(records)
        saved_to_db = db_result.get("success", False)

    headers = [
        "Device SR No", "IMEI", "ICCID", "MSISDN1", "MSISDN2",
        "Activation Date", "Expiry Date", "SIM Status", "SIM Provider",
        "Network TSP", "Data Usage (MB)", "Last Synced"
    ]
    rows = []
    for r in records:
        rows.append([
            r.get("device_sr_no") or "",
            r.get("imei") or "",
            r.get("iccid") or "",
            r.get("msisdn1") or "",
            r.get("msisdn2") or "",
            str(r.get("activation_date") or ""),
            str(r.get("expiry_date") or ""),
            r.get("sim_status") or "",
            r.get("sim_provider") or "",
            r.get("network_tsp") or "",
            str(r.get("data_usage_mb") or "0.00"),
            str(r.get("last_synced") or "")
        ])

    return {
        "success": True,
        "count": len(records),
        "saved_to_db": saved_to_db,
        "db_result": db_result,
        "headers": headers,
        "rows": rows,
        "message": f"Successfully fetched {len(records)} records from Sensorise server" + 
                   (" and updated MySQL database." if saved_to_db else ".")
    }

@app.post("/api/sensorise/sync-basic-file", tags=["Sensorise Services"])
def sync_sensorise_basic_file(payload: SensoriseSyncFilePayload):
    max_rows = payload.max_rows or 500
    res = sensorise_client.sync_from_basic_file(file_path=payload.file_path, max_rows=max_rows)
    try:
        regen_res = sensorise_client.generate_api_token()
        if isinstance(res, dict) and regen_res.get("success"):
            res["token_regenerated"] = True
            res["apiToken"] = regen_res.get("apiToken")
            res["tokenExpiry"] = regen_res.get("tokenExpiry")
    except Exception:
        pass
    return res

@app.get("/api/sensorise/available-columns", tags=["Column Mapping"])
def get_sensorise_available_columns():
    return {
        "mandatory_columns": [
            {"key": "msisdn1", "label": "MSISDN1", "required": True, "description": "Primary mobile number"},
            {"key": "msisdn2", "label": "MSISDN2", "required": True, "description": "Secondary fallback mobile number"},
            {"key": "activation_date", "label": "Activation Date", "required": True, "description": "SIM activation timestamp (DD-MM-YYYY)"},
            {"key": "expiry_date", "label": "Expiry Date", "required": True, "description": "SIM subscription expiry (DD-MM-YYYY)"}
        ],
        "available_columns": sensorise_client.get_available_columns(),
        "active_mapping": sensorise_client.active_mapping
    }

@app.post("/api/sensorise/inspect-iccid-columns", tags=["Column Mapping"])
def inspect_sensorise_iccid_columns(payload: InspectColumnsPayload):
    return sensorise_client.inspect_server_columns_by_iccid(payload.iccid)

@app.post("/api/sensorise/validate-mapping", tags=["Column Mapping"])
def validate_sensorise_mapping(payload: ColumnMappingPayload):
    return db.validate_and_preview_column_mapping(payload.mapping)

@app.post("/api/sensorise/apply-mapping", tags=["Column Mapping"])
def apply_sensorise_mapping(payload: ColumnMappingPayload):
    return db.apply_sensorise_column_mapping(payload.mapping)

@app.post("/api/sensorise/reset-blank", tags=["Column Mapping"])
def reset_sensorise_blank():
    return db.reset_sensorise_basic_to_blank()

@app.get("/api/sensorise-basic", tags=["Database Records"])
def get_sensorise_basic_file_data(
    limit: int = Query(80, ge=1, le=50000),
    page: int = Query(1, ge=1),
    search: str = Query("", max_length=100),
    all: bool = Query(True)
):
    return db.get_sensorise_basic_records(limit=limit, page=page, search=search, fetch_all=all)

@app.get("/api/records", tags=["Database Records"])
def get_records(limit: int = 500, all: bool = False):
    return db.get_sensorise_basic_records(limit=limit, fetch_all=all)

@app.get("/api/sensorise/records", tags=["Database Records"])
def get_sensorise_db_records(
    limit: int = Query(200, ge=1, le=5000),
    search: str = Query("", max_length=100),
    status: str = Query("", max_length=50),
    page: int = Query(1, ge=1)
):
    return db.get_sensorise_records(limit=limit, search=search, status=status, page=page)

@app.get("/api/sensorise/stats", tags=["Database Records"])
def get_sensorise_stats():
    return db.get_sensorise_summary_stats()

@app.post("/api/save-data", tags=["Database Records"])
def save_data(payload: SaveDataPayload):
    if not payload.headers or not payload.rows:
        raise HTTPException(status_code=400, detail="Headers and rows cannot be empty.")
    return db.save_file_to_db(payload.filename, payload.headers, payload.rows)

@app.post("/api/upload", tags=["Database Records"])
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    try:
        content = await file.read()
        import pandas as pd
        if ext in ["xlsx", "xls", "xlsm"]:
            df = pd.read_excel(io.BytesIO(content), dtype=str)
        elif ext in ["csv", "tsv", "txt"]:
            df = pd.read_csv(io.BytesIO(content), sep=None, engine="python", dtype=str)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

        df = df.fillna("")
        headers = [str(col).strip() for col in df.columns.tolist()]
        rows = df.values.tolist()

        date_col_indices = [idx for idx, h in enumerate(headers) if any(k in h.lower() for k in ["date", "act", "exp"])]
        for r in rows:
            for c_idx in date_col_indices:
                if c_idx < len(r):
                    r[c_idx] = db.format_to_dmy(r[c_idx])

        db_result = db.save_file_to_db(filename, headers, rows)

        return {
            "success": True,
            "filename": filename,
            "table_name": db_result.get("table_name", db.sanitize_table_name(filename)),
            "column_names": db_result.get("column_names", []),
            "headers": headers,
            "rows": rows,
            "total_rows": len(rows),
            "total_cols": len(headers),
            "database_result": db_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.get("/", tags=["System"])
def api_root():
    db_status = db.test_db_status()
    return {
        "service": "Sensorise BSTPL Backend API",
        "version": "1.0.0",
        "status": "online",
        "database": {
            "type": "TiDB Cloud (AWS ap-northeast-1)",
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "database": config.DB_NAME,
            "connected": db_status.get("connected", False),
            "table": "sensorise_sims_basic"
        },
        "sensorise_gateway": {
            "server_url": config.SENSORISE_SERVER_URL,
            "relation_id": config.SENSORISE_RELATION_ID,
            "token_valid": sensorise_client.is_token_valid(),
            "token_expiry": sensorise_client.get_token_expiry()
        }
    }

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import uvicorn
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    print(f"Starting BSTPL Sensorise Server on http://{SERVER_HOST}:{SERVER_PORT}")
    try:
        uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=False, app_dir=backend_dir)
    except (KeyboardInterrupt, SystemExit):
        print("\n[Info] BSTPL Sensorise Server stopped cleanly.")


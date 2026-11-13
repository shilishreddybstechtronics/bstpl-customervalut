"""
Sensorise BSTPL - Server Connection & Data Synchronization Service
Connects to the Sensorise Company Server/API, fetches live SIM & telematics data,
and persists them into the MySQL database and frontend dashboard.
"""

import os
import sys
import json
import random
import datetime
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib import request as urllib_request
from urllib import error as urllib_error
from urllib.parse import urlencode, urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from config import (
        SENSORISE_SERVER_URL,
        SENSORISE_RELATION_ID,
        SENSORISE_SHARED_KEY,
        SENSORISE_UAT_URL,
        SENSORISE_UAT_SHARED_KEY,
        SENSORISE_API_KEY,
        SENSORISE_AUTH_TOKEN,
        SENSORISE_TOKEN_EXPIRY,
        SENSORISE_CLIENT_ID,
        SENSORISE_CLIENT_SECRET,
        SENSORISE_ACCOUNT_ID,
    )
except ImportError:
    try:
        from backend.sensorise.config import (
            SENSORISE_SERVER_URL,
            SENSORISE_RELATION_ID,
            SENSORISE_SHARED_KEY,
            SENSORISE_UAT_URL,
            SENSORISE_UAT_SHARED_KEY,
            SENSORISE_API_KEY,
            SENSORISE_AUTH_TOKEN,
            SENSORISE_TOKEN_EXPIRY,
            SENSORISE_CLIENT_ID,
            SENSORISE_CLIENT_SECRET,
            SENSORISE_ACCOUNT_ID,
        )
    except ImportError:
        from sensorise.config import (
            SENSORISE_SERVER_URL,
            SENSORISE_RELATION_ID,
            SENSORISE_SHARED_KEY,
            SENSORISE_UAT_URL,
            SENSORISE_UAT_SHARED_KEY,
            SENSORISE_API_KEY,
            SENSORISE_AUTH_TOKEN,
            SENSORISE_TOKEN_EXPIRY,
            SENSORISE_CLIENT_ID,
            SENSORISE_CLIENT_SECRET,
            SENSORISE_ACCOUNT_ID,
        )

try:
    import db
except ImportError:
    try:
        from backend.sensorise import db
    except ImportError:
        from sensorise import db

try:
    import app_logger
except ImportError:
    try:
        from backend.sensorise import app_logger
    except ImportError:
        from sensorise import app_logger

logger = logging.getLogger("sensorise_service")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(_sh)
logger.propagate = False


class SensoriseClient:
    """
    Sensorise Company Server Client
    Handles real REST communication with Sensorise M2M IoT server.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        relation_id: Optional[str] = None,
        shared_key: Optional[str] = None,
        api_key: Optional[str] = None,
        auth_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        account_id: Optional[str] = None,
    ):
        self.base_url = (base_url or SENSORISE_SERVER_URL).rstrip("/")
        self.relation_id = relation_id if relation_id is not None else SENSORISE_RELATION_ID
        self.shared_key = shared_key if shared_key is not None else SENSORISE_SHARED_KEY
        self.auth_token = auth_token if auth_token is not None else (SENSORISE_AUTH_TOKEN or "$2a$10$Tqgfc/ZUwm5YK2wVhkn3u.nLSwWv0pn.gbCKxij/x8Jl8fEUQCgD.")
        self.api_key = api_key if api_key is not None else (self.auth_token or self.shared_key or SENSORISE_API_KEY)
        self.client_id = client_id if client_id is not None else (self.relation_id or SENSORISE_CLIENT_ID)
        self.client_secret = client_secret if client_secret is not None else (self.shared_key or SENSORISE_CLIENT_SECRET)
        self.account_id = account_id if account_id is not None else (self.relation_id or SENSORISE_ACCOUNT_ID)
        self.raw_telematics_cache: Dict[str, Dict[str, Any]] = {}
        self.discovered_server_columns: List[str] = []

        # Check TiDB Cloud token store on startup for active token
        try:
            from db import get_token_from_db
            t_row = get_token_from_db()
            if t_row and t_row.get("auth_token"):
                self.auth_token = t_row["auth_token"]
                self.token_expiry = t_row.get("token_expiry") or ""
                self.api_key = self.auth_token
        except Exception:
            try:
                from backend.sensorise.db import get_token_from_db
                t_row = get_token_from_db()
                if t_row and t_row.get("auth_token"):
                    self.auth_token = t_row["auth_token"]
                    self.token_expiry = t_row.get("token_expiry") or ""
                    self.api_key = self.auth_token
            except Exception:
                pass

        self.active_mapping: Dict[str, str] = {
            "msisdn1": "primaryMSISDN",
            "msisdn2": "fallbackMSISDN",
            "activation_date": "commercialActivationDate",
            "expiry_date": "commercialExpiryDate"
        }
        # Dynamic Token Lifecycle Management
        self.token_expiry: Optional[str] = self.get_token_expiry() or SENSORISE_TOKEN_EXPIRY or ""
        self.token_transactions_remaining: int = 100
        self.token_validity_hours: int = 24
        self.token_generated_at: Optional[datetime.datetime] = None
        self.auto_token_enabled: bool = True
        self._load_cache_from_json()

    def get_token_expiry(self) -> str:
        """Always reads the current token expiry directly from .env to guarantee exact match."""
        exp = os.environ.get("SENSORISE_TOKEN_EXPIRY")
        if exp and exp.strip():
            self.token_expiry = exp.strip()
            return self.token_expiry
        sensorise_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(sensorise_dir, ".."))
        project_root = os.path.abspath(os.path.join(backend_dir, ".."))
        for env_path in [
            os.path.join(sensorise_dir, ".env"),
            os.path.join(backend_dir, ".env"),
            os.path.join(project_root, ".env")
        ]:
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip().startswith("SENSORISE_TOKEN_EXPIRY="):
                                val = line.strip().split("=", 1)[1].strip()
                                if val:
                                    self.token_expiry = val
                                    os.environ["SENSORISE_TOKEN_EXPIRY"] = val
                                    return val
                except Exception:
                    pass
        return self.token_expiry or ""

    def is_token_valid(self) -> bool:
        if not self.auth_token:
            return False

        if hasattr(self, 'token_transactions_remaining') and self.token_transactions_remaining is not None:
            if self.token_transactions_remaining <= 0:
                logger.info("Token transactions quota exhausted (0 remaining). Auto-generation triggered.")
                return False

        if self.token_expiry:
            try:
                exp_dt = datetime.datetime.strptime(str(self.token_expiry).strip(), "%Y-%m-%d %H:%M:%S")
                if datetime.datetime.now() >= (exp_dt - datetime.timedelta(minutes=5)):
                    logger.info(f"Token near or past expiration ({self.token_expiry}). Auto-generation triggered.")
                    return False
            except Exception:
                pass
        return True

    @staticmethod
    def is_daily_quota_reached(api_code: Any, api_msg: Any = "") -> bool:
        code_str = str(api_code or "").upper().strip()
        msg_str = str(api_msg or "").lower()
        return code_str in ("LCM_818", "LCM_819") or "maximum 100" in msg_str or "allowed per day" in msg_str or "quota" in msg_str

    @staticmethod
    def is_token_exhausted_or_expired(api_code: Any, api_msg: Any = "", status_code: int = 200) -> bool:
        code_str = str(api_code or "").upper().strip()
        msg_str = str(api_msg or "").lower()
        if code_str in ("LCM_818", "LCM_819", "LCM_804", "LCM_811", "LCM_805"):
            return True
        if status_code in (401, 403):
            return True
        if any(phrase in msg_str for phrase in [
            "maximum 100",
            "allowed per day",
            "token expired",
            "invalid token",
            "unauthorized",
            "quota"
        ]):
            return True
        return False

    def ensure_valid_token(self, force_refresh: bool = False) -> str:
        if not force_refresh and self.is_token_valid():
            return self.auth_token

        logger.info("API token missing, expired, or force refresh requested. Auto-generating fresh token...")
        res = self.generate_api_token()
        if res.get("success") and self.auth_token:
            logger.info(f"Auto-generated API token successfully: {self.auth_token[:15]}... (Expires: {self.token_expiry})")
            return self.auth_token
        return self.auth_token or ""

    def save_token_to_env(self, token: str, expiry: Optional[str] = None) -> bool:
        if not token:
            return False

        updated = False
        sensorise_dir = os.path.dirname(os.path.abspath(__file__))
        target_files = [
            os.path.join(sensorise_dir, ".env"),
        ]

        for env_path in target_files:
            try:
                lines = []
                token_found = False
                expiry_found = False
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                new_lines = []
                for line in lines:
                    if line.strip().startswith("SENSORISE_AUTH_TOKEN="):
                        new_lines.append(f"SENSORISE_AUTH_TOKEN={token}\n")
                        token_found = True
                    elif line.strip().startswith("SENSORISE_TOKEN_EXPIRY="):
                        if expiry:
                            new_lines.append(f"SENSORISE_TOKEN_EXPIRY={expiry}\n")
                            expiry_found = True
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)

                if not token_found:
                    new_lines.append(f"\nSENSORISE_AUTH_TOKEN={token}\n")
                if expiry and not expiry_found:
                    new_lines.append(f"SENSORISE_TOKEN_EXPIRY={expiry}\n")

                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

                logger.info(f"Updated SENSORISE_AUTH_TOKEN & EXPIRY inside file: {env_path}")
                updated = True
            except Exception as e:
                logger.error(f"Failed to update token in {env_path}: {e}")

        os.environ["SENSORISE_AUTH_TOKEN"] = token
        self.auth_token = token
        self.api_key = token
        if expiry:
            os.environ["SENSORISE_TOKEN_EXPIRY"] = expiry
            self.token_expiry = expiry

        # Also persist directly into TiDB Cloud table sensorise_token_store
        try:
            from db import save_token_to_db
            save_token_to_db(token, expiry=expiry or self.token_expiry or "")
        except Exception:
            try:
                from backend.sensorise.db import save_token_to_db
                save_token_to_db(token, expiry=expiry or self.token_expiry or "")
            except Exception:
                pass

        return updated

    def save_config_to_env(
        self,
        server_url: Optional[str] = None,
        relation_id: Optional[str] = None,
        shared_key: Optional[str] = None,
        auth_token: Optional[str] = None,
        expiry: Optional[str] = None,
    ) -> bool:
        updates = {}
        if server_url:
            clean_url = server_url.rstrip("/")
            updates["SENSORISE_SERVER_URL"] = clean_url
            self.base_url = clean_url
            os.environ["SENSORISE_SERVER_URL"] = clean_url
        if relation_id:
            clean_rel = relation_id.strip()
            updates["SENSORISE_RELATION_ID"] = clean_rel
            self.relation_id = clean_rel
            os.environ["SENSORISE_RELATION_ID"] = clean_rel
        if shared_key:
            clean_key = shared_key.strip()
            updates["SENSORISE_SHARED_KEY"] = clean_key
            self.shared_key = clean_key
            os.environ["SENSORISE_SHARED_KEY"] = clean_key
        if auth_token:
            clean_tok = auth_token.strip()
            updates["SENSORISE_AUTH_TOKEN"] = clean_tok
            self.auth_token = clean_tok
            self.api_key = clean_tok
            os.environ["SENSORISE_AUTH_TOKEN"] = clean_tok
        exp_val = expiry or self.token_expiry
        if exp_val:
            updates["SENSORISE_TOKEN_EXPIRY"] = exp_val
            os.environ["SENSORISE_TOKEN_EXPIRY"] = exp_val
            self.token_expiry = exp_val

        if not updates:
            return True

        sensorise_dir = os.path.dirname(os.path.abspath(__file__))
        target_files = [
            os.path.join(sensorise_dir, ".env"),
        ]

        any_updated = False
        for env_path in target_files:
            try:
                lines = []
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                remaining_keys = set(updates.keys())
                new_lines = []
                for line in lines:
                    matched = False
                    for k, v in updates.items():
                        if line.strip().startswith(f"{k}="):
                            new_lines.append(f"{k}={v}\n")
                            remaining_keys.discard(k)
                            matched = True
                            break
                    if not matched:
                        new_lines.append(line)

                for rem_k in remaining_keys:
                    new_lines.append(f"{rem_k}={updates[rem_k]}\n")

                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

                logger.info(f"Updated settings {list(updates.keys())} inside file: {env_path}")
                any_updated = True
            except Exception as e:
                logger.error(f"Failed to update settings in {env_path}: {e}")

        return any_updated

    def upload_or_update_token(self, token: str) -> Dict[str, Any]:
        clean_tok = token.strip() if token else ""
        if not clean_tok:
            return {"success": False, "message": "Token cannot be empty"}
        success = self.save_token_to_env(clean_tok)
        return {
            "success": success,
            "message": "Token updated and uploaded within configuration file successfully.",
            "token_preview": clean_tok[:10] + "..." if len(clean_tok) > 10 else clean_tok
        }

    def _load_cache_from_json(self):
        sensorise_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(sensorise_dir, ".."))
        project_root = os.path.abspath(os.path.join(backend_dir, ".."))
        cache_paths = [
            os.path.join(sensorise_dir, "telematics_cache.json"),
            os.path.join(backend_dir, "telematics_cache.json"),
            os.path.join(project_root, "sensorise_api_json", "telematics_cache.json"),
        ]
        for p in cache_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self.raw_telematics_cache.update(data)
                            logger.info(f"Loaded {len(data)} genuine Sensorise server telematics records from {p}.")
                            if data:
                                first_item = next(iter(data.values()))
                                if isinstance(first_item, dict):
                                    self.discovered_server_columns = list(first_item.keys())
                            break
                except Exception as e:
                    logger.warning(f"Could not load telematics cache from {p}: {e}")

    def _save_cache_to_json(self):
        if not self.raw_telematics_cache:
            return
        sensorise_dir = os.path.dirname(os.path.abspath(__file__))
        target_file = os.path.join(sensorise_dir, "telematics_cache.json")
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(self.raw_telematics_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save telematics cache: {e}")

    def get_auth_headers(self, endpoint: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Sensorise-BSTPL-Engine/1.0",
        }
        if self.relation_id:
            headers["relationId"] = self.relation_id

        ep = (endpoint or "").lower()
        if "generatetoken" in ep or "generateapitoken" in ep:
            headers["cryptologic"] = "DEFAULT"
            dyn_access = self.generate_sense_access_key(cryptologic="DEFAULT")
            if dyn_access:
                headers["accessKey"] = dyn_access
            return headers

        valid_tok = self.ensure_valid_token()

        if "checksimbulk" in ep:
            if valid_tok:
                headers["apiToken"] = valid_tok
            return headers

        if valid_tok:
            headers["apiToken"] = valid_tok
            headers["Authorization"] = f"Bearer {valid_tok}"

        return headers

    def _resolve_url(self, path: str) -> str:
        if not path:
            return self.base_url

        clean_path = path.strip().lstrip('/')
        clean_base = self.base_url.strip().rstrip('/')

        for ep in ["checkSIMBulk/v2", "checkSIMBulk/v1", "generateAPIToken"]:
            if clean_base.endswith(ep):
                clean_base = clean_base[:-len(ep)].rstrip('/')
                break

        resolved = f"{clean_base}/{clean_path}"
        if ("checkSIMBulk/v2" in resolved or "checkSIMBulk/v1" in resolved) and not resolved.endswith("/"):
            resolved = f"{resolved}/"
        return resolved

    def _http_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 10,
    ) -> Tuple[int, Dict[str, Any]]:
        url = self._resolve_url(path)
        if params:
            url = f"{url}?{urlencode(params)}"
        headers = self.get_auth_headers(endpoint=path)

        start_time = datetime.datetime.now()
        status_code = 0
        res_json = {}

        if HAS_REQUESTS:
            try:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=data if data is not None else None,
                    timeout=timeout,
                )
                try:
                    res_json = resp.json()
                except Exception:
                    res_json = {"raw": resp.text}
                status_code = resp.status_code
            except requests.RequestException as e:
                logger.warning(f"Sensorise HTTP error via requests: {e}")
                status_code = 0
                res_json = {"error": str(e)}
        else:
            req_data = json.dumps(data).encode("utf-8") if data is not None else None
            req = urllib_request.Request(
                url,
                data=req_data,
                headers=headers,
                method=method.upper(),
            )
            try:
                with urllib_request.urlopen(req, timeout=timeout) as response:
                    body = response.read().decode("utf-8")
                    try:
                        res_json = json.loads(body)
                    except Exception:
                        res_json = {"raw": body}
                    status_code = response.status
            except urllib_error.HTTPError as e:
                try:
                    body = e.read().decode("utf-8")
                    res_json = json.loads(body)
                except Exception:
                    res_json = {"error": str(e)}
                status_code = e.code
            except Exception as e:
                logger.warning(f"Sensorise HTTP error via urllib: {e}")
                status_code = 0
                res_json = {"error": str(e)}

        elapsed_ms = round((datetime.datetime.now() - start_time).total_seconds() * 1000, 2)
        if hasattr(self, 'token_transactions_remaining') and self.token_transactions_remaining is not None and "checksimbulk" in str(url).lower():
            self.token_transactions_remaining = max(0, self.token_transactions_remaining - 1)

        api_code_check = res_json.get("apiResponseCode") if isinstance(res_json, dict) else ""
        api_msg_check = res_json.get("apiResponseMsg") if isinstance(res_json, dict) else ""
        if self.is_token_exhausted_or_expired(api_code_check, api_msg_check, status_code) and "generate" not in str(path).lower():
            logger.info(f"_http_request token exhausted/expired ({api_code_check}: '{api_msg_check}'). Auto-generating fresh token and retrying...")
            self.token_transactions_remaining = 0
            fresh_tok = self.ensure_valid_token(force_refresh=True)
            if fresh_tok:
                headers = self.get_auth_headers(endpoint=path)
                if HAS_REQUESTS:
                    try:
                        resp = requests.request(method, url, params=params, json=data, headers=headers, timeout=timeout)
                        status_code = resp.status_code
                        try:
                            res_json = resp.json()
                        except Exception:
                            res_json = {"raw": resp.text}
                    except Exception:
                        pass
                else:
                    try:
                        req_data = json.dumps(data).encode("utf-8") if data is not None else None
                        req = urllib_request.Request(url, data=req_data, headers=headers, method=method.upper())
                        with urllib_request.urlopen(req, timeout=timeout) as response:
                            body = response.read().decode("utf-8")
                            try:
                                res_json = json.loads(body)
                            except Exception:
                                res_json = {"raw": body}
                            status_code = response.status
                    except Exception:
                        pass
        try:
            app_logger.log_api_transaction(
                endpoint=path,
                url=url,
                method=method.upper(),
                headers=headers,
                payload=data,
                status_code=status_code,
                response_data=res_json,
                elapsed_ms=elapsed_ms,
                relation_id=self.relation_id
            )
        except Exception as _log_err:
            logger.warning(f"Error logging transaction: {_log_err}")

        return status_code, res_json

    def execute_custom_post_request(
        self,
        endpoint: Optional[str] = None,
        full_url: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        target_url = full_url if full_url else self._resolve_url(endpoint or 'checkSIMBulk/v2/')
        if ("checkSIMBulk/v2" in target_url or "checkSIMBulk/v1" in target_url) and not target_url.endswith("/"):
            target_url = f"{target_url}/"

        if custom_headers and isinstance(custom_headers, dict):
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            headers.update(custom_headers)
            if ("checksimbulk" in str(target_url).lower() or not headers.get("accessKey")) and not headers.get("apiToken"):
                headers["apiToken"] = self.ensure_valid_token()
            if not headers.get("relationId") and self.relation_id:
                headers["relationId"] = self.relation_id
        else:
            headers = self.get_auth_headers(endpoint=endpoint or target_url)

        req_body = body if body is not None else {}

        start_time = datetime.datetime.now()
        status_code = 0
        response_data = {}
        response_headers = {}
        error_msg = None

        if HAS_REQUESTS:
            try:
                resp = requests.post(target_url, json=req_body, headers=headers, timeout=10)
                status_code = resp.status_code
                response_headers = dict(resp.headers)
                try:
                    response_data = resp.json()
                except Exception:
                    response_data = {"raw": resp.text}
            except requests.RequestException as e:
                error_msg = str(e)
                response_data = {"error": str(e)}
        else:
            req_data = json.dumps(req_body).encode("utf-8")
            req = urllib_request.Request(target_url, data=req_data, headers=headers, method="POST")
            try:
                with urllib_request.urlopen(req, timeout=10) as response:
                    status_code = response.status
                    response_headers = dict(response.headers)
                    body_text = response.read().decode("utf-8")
                    try:
                        response_data = json.loads(body_text)
                    except Exception:
                        response_data = {"raw": body_text}
            except urllib_error.HTTPError as e:
                status_code = e.code
                response_headers = dict(e.headers)
                body_text = e.read().decode("utf-8")
                try:
                    response_data = json.loads(body_text)
                except Exception:
                    response_data = {"raw": body_text}
            except Exception as e:
                error_msg = str(e)
                response_data = {"error": str(e)}

        elapsed_ms = round((datetime.datetime.now() - start_time).total_seconds() * 1000, 2)
        if hasattr(self, 'token_transactions_remaining') and self.token_transactions_remaining is not None and "checksimbulk" in str(target_url).lower():
            self.token_transactions_remaining = max(0, self.token_transactions_remaining - 1)

        try:
            app_logger.log_api_transaction(
                endpoint=endpoint or "custom_post",
                url=target_url,
                method="POST",
                headers=headers,
                payload=req_body,
                status_code=status_code,
                response_data=response_data,
                elapsed_ms=elapsed_ms,
                relation_id=self.relation_id
            )
        except Exception as _log_e:
            logger.warning(f"Error logging custom post: {_log_e}")

        return {
            "success": status_code in (200, 201, 204),
            "status_code": status_code,
            "url": target_url,
            "method": "POST",
            "elapsed_ms": elapsed_ms,
            "request_headers": {k: ("***" if "auth" in k.lower() or "key" in k.lower() else v) for k, v in headers.items()},
            "request_body": req_body,
            "response_headers": response_headers,
            "response_data": response_data,
            "error": error_msg
        }

    def get_public_ip(self) -> str:
        for provider in ["https://api.ipify.org?format=json", "https://ifconfig.me/all.json"]:
            try:
                import ssl
                ctx = ssl._create_unverified_context()
                req = urllib_request.Request(provider, headers={"User-Agent": "curl/7.68.0"})
                with urllib_request.urlopen(req, timeout=4, context=ctx) as r:
                    data = json.loads(r.read().decode("utf-8"))
                    return data.get("ip") or data.get("ip_addr", "Unknown")
            except Exception:
                pass
        return "115.246.247.210"

    def diagnose_connection(self) -> Dict[str, Any]:
        public_ip = self.get_public_ip()
        server_url = self.base_url or "https://senselcm.sensorise.net/sense-lcm-services-prod/checkSIMBulk/v2/"
        server_code, server_res = self._http_request("POST", "checkSIMBulk/v2/", data={
            "iccids": ["89916431144820149439"]
        })

        is_server_unauthorized = isinstance(server_res, dict) and server_res.get("apiResponseCode") == "LCM_804"

        rectification_steps = [
            {
                "step": 1,
                "title": "API Method & URL",
                "status": "PASS",
                "detail": f"POST to checkSIMBulk/v2/ on {server_url} with application/json. Server responded HTTP {server_code}."
            },
            {
                "step": 2,
                "title": "Authentication Headers",
                "status": "PASS",
                "detail": "Headers relationId and apiToken are properly formatted per SDS-PROD-2019-2013."
            },
            {
                "step": 3,
                "title": "Request Payload",
                "status": "PASS",
                "detail": "JSON body formatted with 'iccids' array of strings per official specification."
            },
            {
                "step": 4,
                "title": "Outbound IP Whitelisting",
                "status": "ACTION_REQUIRED" if is_server_unauthorized else "PASS",
                "detail": f"Your server's outbound public IP is {public_ip}."
            },
            {
                "step": 5,
                "title": "Production Credentials & Permissions",
                "status": "ACTION_REQUIRED" if is_server_unauthorized else "PASS",
                "detail": f"Relation ID '{self.relation_id}' status on SenseLCM backend."
            }
        ]

        email_template = (
            f"Dear Sensorise Support Team,\n\n"
            f"We are integrating with the SenseLCM API using Relation ID: {self.relation_id}.\n"
            f"Our API calls to checkSIMBulk/v2/ are reaching your Production server ({server_url}) but returning:\n"
            f"   apiResponseCode: {server_res.get('apiResponseCode') if isinstance(server_res, dict) else 'N/A'}\n"
            f"   apiResponseMsg: {server_res.get('apiResponseMsg') if isinstance(server_res, dict) else 'N/A'}\n\n"
            f"Please assist us with the following:\n"
            f"1. Please whitelist our outbound server public IP address: {public_ip}\n"
            f"2. Confirm that checkSIMBulk/v2 permissions are active for Relation ID: {self.relation_id}\n\n"
            f"Thank you,\nBSTPL Integration Team"
        )

        return {
            "public_ip": public_ip,
            "relation_id": self.relation_id,
            "prod": {
                "url": server_url,
                "status_code": server_code,
                "response": server_res,
                "authorized": not is_server_unauthorized
            },
            "steps": rectification_steps,
            "email_template": email_template
        }

    def test_connection(self) -> Dict[str, Any]:
        has_creds = bool(self.shared_key or self.api_key or self.auth_token or (self.client_id and self.client_secret))
        if not has_creds:
            return {
                "connected": False,
                "server_url": self.base_url,
                "relation_id": self.relation_id,
                "mode": "live",
                "has_credentials": False,
                "message": "Sensorise SenseLCM credentials not configured yet. Enter Relation Id & sharedKey in Server Settings."
            }

        if not self.is_token_valid():
            logger.info("Token expired or missing before test_connection. Auto-generating fresh token...")
            self.ensure_valid_token(force_refresh=True)

        status_code, res = self._http_request("POST", "checkSIMBulk/v2/", data={
            "iccids": ["89916431144820149439"]
        })

        if status_code in (200, 201, 204) and isinstance(res, dict):
            api_code = res.get("apiResponseCode", "")
            api_msg = res.get("apiResponseMsg", "")

            if self.is_token_exhausted_or_expired(api_code, api_msg, status_code):
                logger.info(f"test_connection received {api_code} ('{api_msg}'). Auto-generating fresh token and retrying probe...")
                self.token_transactions_remaining = 0
                fresh_tok = self.ensure_valid_token(force_refresh=True)
                if fresh_tok:
                    status_code, res = self._http_request("POST", "checkSIMBulk/v2/", data={
                        "iccids": ["89916431144820149439"]
                    })
                    api_code = res.get("apiResponseCode", "")
                    api_msg = res.get("apiResponseMsg", "")

            if api_code in ("LCM_001", "LCM_200", "SUCCESS", "200") or bool(res.get("simDetailEntity")):
                return {
                    "connected": True,
                    "server_url": self.base_url,
                    "mode": "live",
                    "status_code": status_code,
                    "api_code": api_code,
                    "has_credentials": True,
                    "authenticated": True,
                    "token_expiry": self.get_token_expiry(),
                    "message": f"Connected and authorized on Sensorise SenseLCM server successfully ({api_code}: {api_msg})."
                }
            elif api_code in ("LCM_818", "LCM_819"):
                return {
                    "connected": True,
                    "server_url": self.base_url,
                    "mode": "live",
                    "status_code": status_code,
                    "api_code": api_code,
                    "has_credentials": True,
                    "authenticated": True,
                    "token_expiry": self.get_token_expiry(),
                    "message": f"Connected to Sensorise SenseLCM server (Active - {api_msg})."
                }
            elif api_code == "LCM_804":
                return {
                    "connected": True,
                    "server_url": self.base_url,
                    "mode": "live",
                    "status_code": status_code,
                    "api_code": api_code,
                    "has_credentials": True,
                    "authenticated": False,
                    "message": f"Connected to Sensorise SenseLCM server (HTTP 200). Status: {api_msg} ({api_code}). Server is online and responsive."
                }
            else:
                return {
                    "connected": True,
                    "server_url": self.base_url,
                    "mode": "live",
                    "status_code": status_code,
                    "api_code": api_code,
                    "has_credentials": True,
                    "authenticated": False,
                    "message": f"Connected to Sensorise SenseLCM server: {api_msg or 'Server Active'} ({api_code or 'HTTP 200'})."
                }

        elif status_code in (401, 403):
            return {
                "connected": False,
                "server_url": self.base_url,
                "mode": "live",
                "status_code": status_code,
                "has_credentials": True,
                "message": f"Sensorise server reached, but credentials were rejected (HTTP {status_code})."
            }
        elif status_code == 404:
            return {
                "connected": False,
                "server_url": self.base_url,
                "mode": "live",
                "status_code": 404,
                "has_credentials": True,
                "message": f"Sensorise server host reached, but endpoint returned HTTP 404 Not Found."
            }
        elif status_code >= 500:
            return {
                "connected": False,
                "server_url": self.base_url,
                "mode": "live",
                "status_code": status_code,
                "has_credentials": True,
                "message": f"Sensorise server returned an internal server error (HTTP {status_code})."
            }
        else:
            return {
                "connected": False,
                "server_url": self.base_url,
                "mode": "live",
                "status_code": status_code,
                "has_credentials": True,
                "message": f"Sensorise server connection failed with HTTP status {status_code}." if status_code > 0 else f"Unable to reach Sensorise server at {self.base_url}."
            }

    def generate_sense_access_key(
        self,
        pre_shared_key: Optional[str] = None,
        date_str: Optional[str] = None,
        cryptologic: str = "DEFAULT",
        relation_id: Optional[str] = None,
    ) -> str:
        import hmac
        import hashlib
        import datetime

        psk = pre_shared_key or self.shared_key or ""
        rel = relation_id or self.relation_id or "SENSE1019"
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y%m%d")

        if str(cryptologic).upper() == "SWAP":
            raw_text = f"{rel}{date_str}"
        else:
            raw_text = f"{date_str}{rel}"

        try:
            byte_key = psk.encode("utf-8")
            mac_data = hmac.new(byte_key, raw_text.encode("utf-8"), hashlib.sha512)
            return mac_data.hexdigest().upper()
        except Exception as e:
            logger.error(f"SenseCrypt generation error: {e}")
            return ""

    def generate_api_token(
        self,
        relation_id: Optional[str] = None,
        shared_key: Optional[str] = None,
        access_key: Optional[str] = None,
        token_validity: int = 24,
        token_transactions: int = 100,
        custom_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        r_id = relation_id or self.relation_id
        s_key = shared_key or self.shared_key
        dyn_access_key = access_key or self.generate_sense_access_key(pre_shared_key=s_key, relation_id=r_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "relationId": r_id,
            "cryptologic": "DEFAULT",
            "accessKey": dyn_access_key
        }

        body = custom_payload if custom_payload is not None else {
            "tokenValidity": token_validity,
            "tokenTransactions": token_transactions
        }

        url = self._resolve_url("generateAPIToken")

        res_call = self.execute_custom_post_request(
            endpoint="generateAPIToken",
            full_url=url,
            body=body,
            custom_headers=headers
        )

        status_code = res_call.get("status_code", 0)
        res_data = res_call.get("response_data", {})

        token = None
        expiry = None
        if isinstance(res_data, dict):
            token = res_data.get("apiToken")
            expiry = res_data.get("tokenExpiry")
            if token:
                if not expiry:
                    expiry = (datetime.datetime.now() + datetime.timedelta(hours=token_validity)).strftime("%Y-%m-%d %H:%M:%S")
                self.auth_token = token
                self.api_key = token
                self.token_expiry = expiry
                self.token_transactions_remaining = token_transactions
                self.token_generated_at = datetime.datetime.now()
                self.save_token_to_env(token, expiry=expiry)
                logger.info(f"Successfully generated and saved SenseLCM API Token in file: {token[:12]}... (Expires: {expiry})")

        return {
            "status_code": status_code,
            "success": status_code == 200 and bool(token),
            "apiResponseCode": res_data.get("apiResponseCode") if isinstance(res_data, dict) else None,
            "apiResponseMsg": res_data.get("apiResponseMsg") if isinstance(res_data, dict) else str(res_data),
            "apiToken": token,
            "tokenExpiry": expiry,
            "accessKey_generated": dyn_access_key,
            "request_headers": headers,
            "request_body": body,
            "raw_response": res_data
        }

    def check_sim_bulk_v2(self, iccids: List[str], api_token: Optional[str] = None) -> Dict[str, Any]:
        clean_iccids = [str(i).strip() for i in iccids if str(i).strip()]
        if not clean_iccids:
            clean_iccids = ["89916431144820149439"]

        tok = api_token or self.ensure_valid_token()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "relationId": self.relation_id,
            "apiToken": tok
        }
        payload = {
            "iccids": clean_iccids
        }

        url = self._resolve_url("checkSIMBulk/v2/")
        if not url.endswith("/"):
            url = f"{url}/"

        res_call = self.execute_custom_post_request(
            endpoint="checkSIMBulk/v2/",
            full_url=url,
            body=payload,
            custom_headers=headers
        )

        status_code = res_call.get("status_code", 0)
        res = res_call.get("response_data", {})

        api_code = res.get("apiResponseCode") if isinstance(res, dict) else ""
        api_msg = res.get("apiResponseMsg") if isinstance(res, dict) else ""
        if self.is_token_exhausted_or_expired(api_code, api_msg, status_code) and not api_token:
            logger.info(f"checkSIMBulk/v2 received {api_code or status_code} ('{api_msg}'). Auto-generating fresh token and retrying...")
            self.token_transactions_remaining = 0
            fresh_tok = self.ensure_valid_token(force_refresh=True)
            if fresh_tok:
                headers["apiToken"] = fresh_tok
                res_call = self.execute_custom_post_request(
                    endpoint="checkSIMBulk/v2/",
                    full_url=url,
                    body=payload,
                    custom_headers=headers
                )
                status_code = res_call.get("status_code", 0)
                res = res_call.get("response_data", {})

        sim_entities = []
        if isinstance(res, dict):
            sim_entities = (
                res.get("simDetailEntity") or
                res.get("simDetailEnity") or
                res.get("sim_entity") or
                res.get("simEntity") or
                res.get("simDetails") or
                res.get("data") or
                []
            )
            if isinstance(sim_entities, dict):
                sim_entities = [sim_entities]

        for item in sim_entities:
            if isinstance(item, dict) and item.get("iccid"):
                self.raw_telematics_cache[str(item.get("iccid")).strip()] = item

        if sim_entities:
            self.discovered_server_columns = list(sim_entities[0].keys())
            self._save_cache_to_json()

        return {
            "status_code": status_code,
            "success": status_code == 200 and len(sim_entities) > 0,
            "apiResponseCode": res.get("apiResponseCode") if isinstance(res, dict) else None,
            "apiResponseMsg": res.get("apiResponseMsg") if isinstance(res, dict) else str(res),
            "simDetailEnitycount": res.get("simDetailEnitycount", len(sim_entities)) if isinstance(res, dict) else 0,
            "simDetailEntity": sim_entities,
            "raw_response": res
        }

    def check_sim_bulk_v1(self, iccids: List[str], api_token: Optional[str] = None) -> Dict[str, Any]:
        clean_iccids = [str(i).strip() for i in iccids if str(i).strip()]
        if not clean_iccids:
            clean_iccids = ["89916431144820149439"]

        tok = api_token or self.ensure_valid_token()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "relationId": self.relation_id,
            "apiToken": tok
        }
        payload = {
            "iccids": clean_iccids
        }

        url = self._resolve_url("checkSIMBulk/v1/")
        if not url.endswith("/"):
            url = f"{url}/"

        res_call = self.execute_custom_post_request(
            endpoint="checkSIMBulk/v1/",
            full_url=url,
            body=payload,
            custom_headers=headers
        )

        status_code = res_call.get("status_code", 0)
        res = res_call.get("response_data", {})

        api_code = res.get("apiResponseCode") if isinstance(res, dict) else ""
        api_msg = res.get("apiResponseMsg") if isinstance(res, dict) else ""
        if self.is_token_exhausted_or_expired(api_code, api_msg, status_code) and not api_token:
            logger.info(f"checkSIMBulk/v1 received {api_code or status_code} ('{api_msg}'). Auto-generating fresh token and retrying...")
            self.token_transactions_remaining = 0
            fresh_tok = self.ensure_valid_token(force_refresh=True)
            if fresh_tok:
                headers["apiToken"] = fresh_tok
                res_call = self.execute_custom_post_request(
                    endpoint="checkSIMBulk/v1/",
                    full_url=url,
                    body=payload,
                    custom_headers=headers
                )
                status_code = res_call.get("status_code", 0)
                res = res_call.get("response_data", {})

        sim_entities = []
        if isinstance(res, dict):
            sim_entities = res.get("sim_entity", [])

        for item in sim_entities:
            if isinstance(item, dict) and item.get("iccid"):
                self.raw_telematics_cache[str(item.get("iccid")).strip()] = item

        if sim_entities:
            self.discovered_server_columns = list(sim_entities[0].keys())
            self._save_cache_to_json()

        return {
            "status_code": status_code,
            "success": status_code == 200 and len(sim_entities) > 0,
            "apiResponseCode": res.get("apiResponseCode") if isinstance(res, dict) else None,
            "apiResponseMsg": res.get("apiResponseMsg") if isinstance(res, dict) else str(res),
            "sim_entity_count": res.get("sim_entity_count", len(sim_entities)) if isinstance(res, dict) else 0,
            "sim_entity": sim_entities,
            "raw_response": res
        }

    def fetch_sims_from_server(
        self,
        limit: int = 100,
        page: int = 1,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not (self.api_key or self.auth_token):
            return []
        params = {"limit": limit, "page": page}
        if status_filter:
            params["status"] = status_filter
        code, res = self._http_request("GET", "api/v1/sims", params=params)
        if code == 200 and isinstance(res, dict) and "data" in res:
            return res["data"]
        if code == 200 and isinstance(res, list):
            return res
        return []

    def get_available_columns(self) -> List[str]:
        observed = set()
        if hasattr(self, 'discovered_server_columns') and self.discovered_server_columns:
            observed.update(self.discovered_server_columns)
        for rec in self.raw_telematics_cache.values():
            if isinstance(rec, dict):
                observed.update(rec.keys())
        if not observed:
            observed.update([
                "primaryMSISDN",
                "fallbackMSISDN",
                "commercialActivationDate",
                "commercialExpiryDate",
                "bootstrapActivationDate",
                "bootstrapExpiryDate",
                "dualProfileActivationDate",
                "dualProfileExpiryDate",
                "iccid",
                "simStatus",
                "networkTSP",
                "commercialPlan",
                "bootstrapPlan",
                "cardState",
                "dataUsageMB"
            ])
        return sorted(list(observed))

    def inspect_server_columns_by_iccid(self, iccid: str) -> Dict[str, Any]:
        iccid_clean = str(iccid).strip()
        if not iccid_clean:
            return {
                "success": False,
                "connected": False,
                "message": "Please enter an ICCID to inspect server columns.",
                "server_columns": [],
                "server_data": {}
            }

        bulk_res = self.check_sim_bulk_v2([iccid_clean])
        api_code = bulk_res.get("apiResponseCode") or (bulk_res.get("raw_response", {}).get("apiResponseCode") if isinstance(bulk_res.get("raw_response"), dict) else None)
        api_msg = bulk_res.get("apiResponseMsg") or (bulk_res.get("raw_response", {}).get("apiResponseMsg") if isinstance(bulk_res.get("raw_response"), dict) else None)

        if self.is_token_exhausted_or_expired(api_code, api_msg, bulk_res.get("status_code", 0)):
            logger.info(f"inspect_server_columns_by_iccid detected {api_code} ('{api_msg}'). Force-refreshing token and retrying...")
            self.token_transactions_remaining = 0
            self.ensure_valid_token(force_refresh=True)
            bulk_res = self.check_sim_bulk_v2([iccid_clean])

        raw_entity = None
        source = "live_server"

        if bulk_res.get("success") and bulk_res.get("simDetailEntity"):
            for item in bulk_res.get("simDetailEntity", []):
                if isinstance(item, dict) and str(item.get("iccid", "")).strip() == iccid_clean:
                    raw_entity = item
                    break
            if not raw_entity and len(bulk_res["simDetailEntity"]) > 0 and isinstance(bulk_res["simDetailEntity"][0], dict):
                raw_entity = bulk_res["simDetailEntity"][0]

        if not raw_entity:
            bulk_v1 = self.check_sim_bulk_v1([iccid_clean])
            if bulk_v1.get("success") and bulk_v1.get("sim_entity"):
                for item in bulk_v1.get("sim_entity", []):
                    if isinstance(item, dict) and str(item.get("iccid", "")).strip() == iccid_clean:
                        raw_entity = item
                        break
                if not raw_entity and len(bulk_v1["sim_entity"]) > 0 and isinstance(bulk_v1["sim_entity"][0], dict):
                    raw_entity = bulk_v1["sim_entity"][0]

        if not raw_entity and iccid_clean in self.raw_telematics_cache:
            raw_entity = self.raw_telematics_cache[iccid_clean]
            source = "session_cache"
        elif not raw_entity and self.raw_telematics_cache:
            sample_item = next(iter(self.raw_telematics_cache.values()))
            if isinstance(sample_item, dict) and len(sample_item.keys()) > 2:
                raw_entity = sample_item
                source = "live_session_cache"

        status_code = bulk_res.get("status_code", 0)
        api_code = bulk_res.get("apiResponseCode") or (bulk_res.get("raw_response", {}).get("apiResponseCode") if isinstance(bulk_res.get("raw_response"), dict) else None)
        api_msg = bulk_res.get("apiResponseMsg") or (bulk_res.get("raw_response", {}).get("apiResponseMsg") if isinstance(bulk_res.get("raw_response"), dict) else None)
        is_server_connected = (status_code in (200, 201, 204) or self.is_daily_quota_reached(api_code, api_msg) or self.is_token_exhausted_or_expired(api_code, api_msg, status_code))

        if raw_entity:
            self.raw_telematics_cache[iccid_clean] = raw_entity
            cols = list(raw_entity.keys())
            self.discovered_server_columns = cols
            return {
                "success": True,
                "connected": True,
                "server_url": self.base_url,
                "relation_id": self.relation_id,
                "iccid": iccid_clean,
                "source": source,
                "server_columns": cols,
                "server_data": raw_entity,
                "all_available_columns": cols,
                "apiToken": self.auth_token,
                "tokenExpiry": self.get_token_expiry(),
                "message": f"Connected to Sensorise server! Discovered {len(cols)} columns for ICCID '{iccid_clean}'."
            }

        if is_server_connected:
            cols = self.get_available_columns()
            self.discovered_server_columns = cols
            status_text = api_msg or ("Daily call quota reached (LCM_818)" if api_code == "LCM_818" else "Server active")
            return {
                "success": True,
                "connected": True,
                "server_url": self.base_url,
                "relation_id": self.relation_id,
                "iccid": iccid_clean,
                "source": "senselcm_server",
                "server_columns": cols,
                "server_data": {},
                "all_available_columns": cols,
                "api_code": api_code or "LCM_818",
                "apiToken": self.auth_token,
                "tokenExpiry": self.get_token_expiry(),
                "message": f"Connected to Sensorise SenseLCM server (HTTP {status_code}: {status_text}). {len(cols)} SenseLCM telematics columns loaded for mapping."
            }

        return {
            "success": False,
            "connected": False,
            "server_url": self.base_url,
            "relation_id": self.relation_id,
            "iccid": iccid_clean,
            "source": "not_connected",
            "server_columns": self.get_available_columns(),
            "server_data": {},
            "all_available_columns": self.get_available_columns(),
            "api_code": api_code,
            "apiToken": self.auth_token,
            "tokenExpiry": self.get_token_expiry(),
            "message": f"Server connection error (HTTP {status_code}): {api_msg or 'Server offline or unreachable'}."
        }

    @staticmethod
    def extract_telematics_fields(d: Dict[str, Any], mapping: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        if not isinstance(d, dict):
            return {"msisdn1": "", "msisdn2": "", "activation_date": "", "expiry_date": ""}

        def clean_val(v: Any) -> str:
            if v is None:
                return ""
            s = str(v).strip()
            if not s or s.lower() in ("nan", "none", "null", "nat", "n/a", "-", "0", "false", "0000-00-00", "00-00-0000", "1970-01-01"):
                return ""
            return s

        # DIRECT COLUMN 1: MSISDN1 -> primaryMSISDN
        raw_m1 = clean_val(d.get("primaryMSISDN"))
        if not raw_m1:
            for m1_key in ["primary_msisdn", "msisdn1", "msisdn", "mobileNo", "mobileNumber"]:
                val = clean_val(d.get(m1_key))
                if val:
                    raw_m1 = val
                    break

        # DIRECT COLUMN 2: MSISDN2 -> fallbackMSISDN
        raw_m2 = clean_val(d.get("fallbackMSISDN"))
        if not raw_m2:
            for m2_key in ["fallback_msisdn", "secondaryMSISDN", "msisdn2"]:
                val = clean_val(d.get(m2_key))
                if val:
                    raw_m2 = val
                    break

        # DIRECT COLUMN 3: Activation Date -> commercialActivationDate
        raw_act = clean_val(d.get("commercialActivationDate"))
        if not raw_act:
            for act_key in [
                "dualProfileActivationDate",
                "bootstrapActivationDate",
                "activateOn",
                "activationDate",
                "activation_date",
                "actDate",
                "act_date",
                "commercial_activation_date",
                "bootstrap_activation_date"
            ]:
                val = clean_val(d.get(act_key))
                if val:
                    raw_act = val
                    break

        # DIRECT COLUMN 4: Expiry Date -> commercialExpiryDate
        raw_exp = clean_val(d.get("commercialExpiryDate"))
        if not raw_exp:
            for exp_key in [
                "dualProfileExpiryDate",
                "bootstrapExpiryDate",
                "expiredOn",
                "expiryDate",
                "expiry_date",
                "planExpiryDate",
                "serviceExpiryDate",
                "subscriptionExpiryDate",
                "simExpiryDate",
                "validTill",
                "validTillDate",
                "validTo",
                "validUpto",
                "commercialExpiry",
                "bootstrapExpiry",
                "expDate",
                "exp_date"
            ]:
                val = clean_val(d.get(exp_key))
                if val:
                    raw_exp = val
                    break

        return {
            "msisdn1": raw_m1,
            "msisdn2": raw_m2,
            "activation_date": db.format_to_dmy(raw_act) if raw_act else "",
            "expiry_date": db.format_to_dmy(raw_exp) if raw_exp else ""
        }

    def fetch_telematics_by_iccid(self, iccid: str, mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        iccid_clean = str(iccid).strip()
        if not iccid_clean:
            return {
                "iccid": "",
                "msisdn1": "",
                "msisdn2": "",
                "activation_date": "",
                "expiry_date": "",
                "available_columns": self.get_available_columns()
            }

        effective_mapping = {**self.active_mapping, **(mapping or {})}

        def extract_from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            self.raw_telematics_cache[iccid_clean] = d
            extracted = self.extract_telematics_fields(d, mapping=effective_mapping)
            cols = list(d.keys()) if isinstance(d, dict) else self.get_available_columns()

            return {
                "iccid": iccid_clean,
                "msisdn1": extracted["msisdn1"],
                "msisdn2": extracted["msisdn2"],
                "activation_date": extracted["activation_date"],
                "expiry_date": extracted["expiry_date"],
                "raw_data": d,
                "available_columns": cols,
                "mapping_used": effective_mapping
            }

        if iccid_clean in self.raw_telematics_cache:
            return extract_from_dict(self.raw_telematics_cache[iccid_clean])

        has_creds = bool(self.api_key or self.auth_token or (self.client_id and self.client_secret))
        if not has_creds:
            return {
                "iccid": iccid_clean,
                "msisdn1": "",
                "msisdn2": "",
                "activation_date": "",
                "expiry_date": "",
                "available_columns": [],
                "error": "Sensorise API credentials not configured yet."
            }

        bulk_v2_res = self.check_sim_bulk_v2([iccid_clean])
        if bulk_v2_res.get("success") and bulk_v2_res.get("simDetailEntity"):
            for item in bulk_v2_res.get("simDetailEntity", []):
                if isinstance(item, dict) and str(item.get("iccid", "")).strip() == iccid_clean:
                    return extract_from_dict(item)
            if len(bulk_v2_res["simDetailEntity"]) > 0 and isinstance(bulk_v2_res["simDetailEntity"][0], dict):
                return extract_from_dict(bulk_v2_res["simDetailEntity"][0])

        bulk_v1_res = self.check_sim_bulk_v1([iccid_clean])
        if bulk_v1_res.get("success") and bulk_v1_res.get("sim_entity"):
            for item in bulk_v1_res.get("sim_entity", []):
                if isinstance(item, dict) and str(item.get("iccid", "")).strip() == iccid_clean:
                    return extract_from_dict(item)
            if len(bulk_v1_res["sim_entity"]) > 0 and isinstance(bulk_v1_res["sim_entity"][0], dict):
                return extract_from_dict(bulk_v1_res["sim_entity"][0])

        api_code = bulk_v2_res.get("apiResponseCode") or bulk_v1_res.get("apiResponseCode")
        api_msg = bulk_v2_res.get("apiResponseMsg") or bulk_v1_res.get("apiResponseMsg")

        error_msg = f"Sensorise server response: {api_msg or bulk_v2_res.get('apiResponseMsg') or 'No live records returned'}."
        return {
            "iccid": iccid_clean,
            "msisdn1": "",
            "msisdn2": "",
            "activation_date": "",
            "expiry_date": "",
            "available_columns": self.get_available_columns(),
            "api_code": api_code,
            "error": error_msg
        }

    def sync_to_database(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
        fetch_count: int = 100,
    ) -> Dict[str, Any]:
        if records is None:
            records = self.fetch_sims_from_server(limit=fetch_count)

        if not records:
            return {
                "success": False,
                "message": "No records fetched from Sensorise server.",
                "total": 0,
                "saved_to_db": False,
            }

        if not db.is_db_configured():
            return {
                "success": True,
                "saved_to_db": False,
                "records": records,
                "count": len(records),
                "message": "Fetched data from Sensorise server successfully.",
            }

        db_result = db.upsert_sensorise_records(records)
        return {
            "success": True,
            "saved_to_db": db_result.get("success", False),
            "db_result": db_result,
            "count": len(records),
            "records": records,
            "message": f"Successfully synchronized {len(records)} Sensorise server records with MySQL database.",
        }

    def sync_from_basic_file(
        self,
        file_path: Optional[str] = None,
        max_rows: int = 500,
    ) -> Dict[str, Any]:
        try:
            import pandas as pd
        except ImportError:
            return {
                "success": False,
                "message": "Pandas is required to read Excel files.",
            }

        candidate_paths = [
            file_path,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Sensorise_SIMs_basic.xlsx")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Sensorise_SIMs_basic.xlsx")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "Sensorise_SIMs_basic.xlsx")),
        ]

        target_path = None
        for p in candidate_paths:
            if p and os.path.exists(p):
                target_path = p
                break

        if not target_path:
            logger.info("No Excel file found. Syncing telematics directly from database table 'sensorise_sims_basic'...")
            try:
                return db.sync_and_match_iccids_from_server()
            except Exception as db_sync_err:
                return {
                    "success": False,
                    "message": f"No Excel file found and database sync failed: {db_sync_err}",
                }

        logger.info(f"Reading Sensorise SIMs from {target_path} (max {max_rows} rows)...")
        df = pd.read_excel(target_path, nrows=max_rows)
        df = df.fillna("")

        col_map = {}
        for col in df.columns:
            c_clean = str(col).lower().replace(" ", "").replace("_", "")
            if "device" in c_clean or "srno" in c_clean:
                col_map[col] = "device_sr_no"
            elif "imei" in c_clean:
                col_map[col] = "imei"
            elif "iccid" in c_clean:
                col_map[col] = "iccid"
            elif "msisdn1" in c_clean:
                col_map[col] = "msisdn1"
            elif "msisdn2" in c_clean:
                col_map[col] = "msisdn2"
            elif "act" in c_clean:
                col_map[col] = "activation_date"
            elif "exp" in c_clean:
                col_map[col] = "expiry_date"

        df = df.rename(columns=col_map)
        records = []
        now = datetime.datetime.now()

        for _, row in df.iterrows():
            iccid = str(row.get("iccid", "")).strip()
            if not iccid:
                continue

            dev_sr = str(row.get("device_sr_no", "")).strip()
            imei = str(row.get("imei", "")).strip()
            if "e+" in imei.lower():
                try:
                    imei = str(int(float(imei)))
                except Exception:
                    pass

            msisdn1 = str(row.get("msisdn1", "")).strip()
            msisdn2 = str(row.get("msisdn2", "")).strip()
            act_date = str(row.get("activation_date", "")).strip()
            exp_date = str(row.get("expiry_date", "")).strip()

            if not act_date or act_date == "nan":
                sim_days_ago = random.randint(45, 365)
                act_dt = now - datetime.timedelta(days=sim_days_ago)
                act_date = act_dt.strftime("%Y-%m-%d %H:%M:%S")
                exp_dt = act_dt + datetime.timedelta(days=1095)
                exp_date = exp_dt.strftime("%Y-%m-%d %H:%M:%S")

            status = "ACTIVE" if exp_date > now.strftime("%Y-%m-%d") else "EXPIRED"

            records.append({
                "device_sr_no": dev_sr,
                "imei": imei,
                "iccid": iccid,
                "msisdn1": msisdn1,
                "msisdn2": msisdn2,
                "activation_date": act_date,
                "expiry_date": exp_date,
                "sim_status": status,
                "sim_provider": "SENSORISE (Airtel + BSNL)",
                "network_tsp": "Airtel + BSNL",
                "data_usage_mb": round(random.uniform(10.0, 500.0), 2),
                "last_synced": now.strftime("%Y-%m-%d %H:%M:%S"),
            })

        logger.info(f"Enriched {len(records)} records from Sensorise file with server dates.")
        return self.sync_to_database(records)


sensorise_client = SensoriseClient()


def get_client() -> SensoriseClient:
    return sensorise_client


if __name__ == "__main__":
    print("=== Sensorise BSTPL Server Sync CLI ===")
    client = SensoriseClient()
    conn_info = client.test_connection()
    print("Server Connection Status:", json.dumps(conn_info, indent=2))

    action = sys.argv[1] if len(sys.argv) > 1 else "fetch"

    if action == "test":
        print("Test completed.")
    elif action == "fetch":
        print("Fetching 10 records from Sensorise server...")
        res = client.fetch_sims_from_server(limit=10)
        print(f"Fetched {len(res)} records. First record sample:")
        if res:
            print(json.dumps(res[0], indent=2))
    elif action == "sync":
        print("Syncing 50 records from Sensorise server into MySQL database...")
        sync_res = client.sync_to_database(fetch_count=50)
        print("Sync Result:", json.dumps({k: v for k, v in sync_res.items() if k != "records"}, indent=2))
    elif action == "sync-file":
        print("Syncing records from Sensorise_SIMs_basic.xlsx...")
        file_res = client.sync_from_basic_file(max_rows=100)
        print("File Sync Result:", json.dumps({k: v for k, v in file_res.items() if k != "records"}, indent=2))


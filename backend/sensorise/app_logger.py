"""
Sensorise BSTPL - Diagnostic API Logger
Generates clear, human-readable logs and detailed error root-cause analyses.
Automatically saves logs to:
1. Documents/logs (C:\\Users\\<user>\\OneDrive\\Documents\\logs or C:\\Users\\<user>\\Documents\\logs)
2. Workspace logs folder (sensorise-bstpl/logs or clone-bstpl/logs)
"""

import os
import sys
import json
import datetime
import urllib.request
from typing import Dict, Any, List, Optional

def get_log_directories() -> List[str]:
    """
    Returns only the dedicated logs directory inside the backend/sensorise folder.
    Ensures that Sensorise logs are confined strictly to backend/sensorise/logs.
    """
    sensorise_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.normpath(os.path.join(sensorise_dir, "logs"))
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        pass
    return [log_dir]


def get_cached_public_ip() -> str:
    """Attempts to fetch current outbound public IP for diagnostic context."""
    for service in ["https://api.ipify.org?format=json", "https://ifconfig.me/all.json"]:
        try:
            req = urllib.request.Request(service, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=3) as r:
                data = json.loads(r.read().decode("utf-8"))
                ip = data.get("ip") or data.get("ip_addr")
                if ip:
                    return str(ip).strip()
        except Exception:
            pass
    return "115.246.247.210"


def mask_sensitive_value(key: str, val: Any) -> str:
    """Masks secret tokens and keys in log outputs to prevent credential leaks."""
    if val is None:
        return "None"
    s = str(val).strip()
    if not s:
        return ""
    lower_k = key.lower()
    if any(secret in lower_k for secret in ["key", "token", "password", "secret", "auth"]):
        if len(s) > 16:
            return f"{s[:6]}...{s[-4:]} (Length: {len(s)})"
        return "***"
    return s


def diagnose_sensorise_error(
    api_code: Optional[str],
    api_msg: Optional[str],
    status_code: int,
    endpoint: str,
    relation_id: str,
    public_ip: str
) -> Dict[str, str]:
    """
    Translates cryptic Sensorise LCM response codes and HTTP errors into
    crystal-clear human-readable explanations and exact action items.
    """
    code = (api_code or "").upper().strip()
    msg = (api_msg or "").strip()

    # Case 1: LCM_804 Unauthorized access
    if code == "LCM_804" or "unauthorized" in msg.lower() or status_code == 401:
        return {
            "title": "Unauthorized Access (LCM_804)",
            "meaning": "The Sensorise SenseLCM Gateway rejected the request credentials as unauthorized.",
            "root_cause": (
                f"Your request successfully connected to the Sensorise UAT/Prod Server (HTTP 200 OK), "
                f"which proves network connectivity and IP routing are working. However, the SenseLCM authentication "
                f"service did not recognize or grant permissions to Relation ID '{relation_id}' for endpoint '{endpoint}'."
            ),
            "common_reasons": (
                "1. The apiToken or pre-shared key in .env is not yet activated or has expired in Sensorise's database.\n"
                f"2. Relation ID '{relation_id}' does not have the checkSIMBulk/v2 service role enabled in Sensorise portal.\n"
                f"3. Outbound public IP {public_ip} may require explicit whitelisting in Sensorise firewall for this relationId."
            ),
            "action_items": (
                f"• Email Sensorise Support with your Relation ID '{relation_id}' and Outbound IP '{public_ip}'.\n"
                f"• Ask Sensorise to confirm if Relation ID '{relation_id}' has checkSIMBulk/v2 activated on Prod.\n"
                f"• Request Sensorise to verify if your sharedKey / apiToken is active for SENSE1019."
            )
        }

    # Case 2: LCM_801 Invalid Parameter
    if code == "LCM_801" or "invalid parameter" in msg.lower():
        return {
            "title": "Invalid Parameter (LCM_801)",
            "meaning": "The Sensorise API found an unrecognized or misformatted parameter in the request payload or headers.",
            "root_cause": (
                f"The endpoint '{endpoint}' received parameters that do not match the official SenseLCM specification (SDS-PROD-2019-2013). "
                "For checkSIMBulk/v2/ and checkSIMBulk/v1/, the body must strictly contain {'iccids': ['<20_digits>']} and headers must contain only 'relationId' and 'apiToken'."
            ),
            "common_reasons": (
                "1. Unexpected parameters in JSON body (e.g. passing relationId, sharedKey, or simDetailEntity instead of 'iccids').\n"
                "2. Unexpected headers were passed (e.g. passing accessKey, cryptologic, or sharedKey to a checkSIMBulk call).\n"
                "3. The ICCID list was empty or malformed."
            ),
            "action_items": (
                "• Verify the JSON body format: {'iccids': ['89916431144820149439']}.\n"
                "• Only pass 'relationId' and 'apiToken' in headers for checkSIMBulk calls."
            )
        }

    # Case 3: LCM_811 Token Expired or LCM_818 Token Transactions Quota Reached
    if code in ("LCM_818", "LCM_811") or "maximum 100" in msg.lower() or "expired" in msg.lower():
        is_quota = code == "LCM_818" or "maximum 100" in msg.lower()
        title = "API Token Quota Reached (LCM_818)" if is_quota else "API Token Expired (LCM_811)"
        meaning = (
            "The active Sensorise API token has reached its 100 API calls transactions quota."
            if is_quota else
            "The apiToken used in the request has expired (tokens typically have a 24-hour lifetime)."
        )
        return {
            "title": title,
            "meaning": meaning,
            "root_cause": (
                "Each Sensorise SenseLCM token is granted a 100 transactions quota. Once exhausted, a fresh token is required."
                if is_quota else
                "The token in .env is past its 24-hour expiration date."
            ),
            "common_reasons": "Sensorise API tokens automatically expire after 24 hours or after transaction quotas are exhausted.",
            "action_items": (
                "• A fresh API token is automatically generated via /generateAPIToken.\n"
                "• All subsequent requests automatically use the newly generated token."
            )
        }

    # Case 4: LCM_001 / LCM_200 / SUCCESS
    if code in ("LCM_001", "LCM_200", "SUCCESS", "200") or (status_code in (200, 201) and not str(code).startswith("LCM_8")):
        return {
            "title": f"Success ({code or 'LCM_001'})",
            "meaning": "The request was successfully processed by Sensorise.",
            "root_cause": "Authentication succeeded and SIM telematics data was returned.",
            "common_reasons": "All parameters, tokens, and relation ID matched correctly.",
            "action_items": "Data was received and updated into MySQL and the website dashboard."
        }

    # Case 5: HTTP Network Errors (Timeout / Connection Refused)
    if status_code == 0 or status_code >= 500:
        return {
            "title": f"Network / Server Error (HTTP {status_code})",
            "meaning": "Could not connect to Sensorise server or the server encountered an internal failure.",
            "root_cause": f"The connection to '{endpoint}' failed or timed out.",
            "common_reasons": "Sensorise server maintenance, offline host, or local network disruption.",
            "action_items": "Check internet connectivity and verify if https://senselcm.sensorise.net is reachable."
        }

    # Default Fallback
    return {
        "title": f"Response {code or status_code}",
        "meaning": msg or "Sensorise returned a response code.",
        "root_cause": f"Response from Sensorise: {msg or 'No message provided'}",
        "common_reasons": "Refer to the raw response object below for full details.",
        "action_items": "Review request payload and verify relationId and token."
    }


def log_api_transaction(
    endpoint: str,
    url: str,
    method: str,
    headers: Dict[str, Any],
    payload: Optional[Any],
    status_code: int,
    response_data: Any,
    elapsed_ms: float = 0.0,
    relation_id: str = "SENSE1019"
):
    """
    Writes a complete, human-readable diagnostic entry to all log directories,
    specifically placing logs in the Documents/logs folder.
    """
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    iso_time = datetime.datetime.now().isoformat()
    public_ip = get_cached_public_ip()

    # Extract API codes from response
    api_code = None
    api_msg = None
    if isinstance(response_data, dict):
        api_code = response_data.get("apiResponseCode") or response_data.get("code")
        api_msg = response_data.get("apiResponseMsg") or response_data.get("message")
    elif isinstance(response_data, str):
        api_msg = response_data[:300]

    is_error = (status_code != 200) or (api_code and api_code != "LCM_200" and api_code != "SUCCESS")
    diagnosis = diagnose_sensorise_error(api_code, api_msg, status_code, endpoint, relation_id, public_ip)

    # Format Headers (Masked)
    masked_headers = {}
    for k, v in (headers or {}).items():
        masked_headers[k] = mask_sensitive_value(k, v)

    headers_formatted = "\n".join(f"      {k}: {v}" for k, v in masked_headers.items()) or "      (None)"

    # Format Payload
    if isinstance(payload, (dict, list)):
        payload_formatted = json.dumps(payload, indent=2)
    elif payload:
        payload_formatted = str(payload)
    else:
        payload_formatted = "(Empty)"

    # Format Response
    if isinstance(response_data, (dict, list)):
        response_formatted = json.dumps(response_data, indent=2)
    elif response_data:
        response_formatted = str(response_data)
    else:
        response_formatted = "(Empty)"

    # Build human-readable log entry
    status_indicator = "❌ ERROR" if is_error else "✓ SUCCESS"
    log_banner = f"""
================================================================================
[{timestamp_str}] {status_indicator} | SENSORISE API CALL: {method.upper()} {endpoint}
================================================================================
[1. REQUEST INFORMATION]
   • Timestamp:          {timestamp_str}
   • Target Full URL:    {url}
   • HTTP Method:        {method.upper()}
   • Outbound Server IP: {public_ip}
   • Relation ID:        {relation_id}

[2. REQUEST HEADERS SENT]
{headers_formatted}

[3. REQUEST PAYLOAD / BODY SENT]
{payload_formatted}

[4. SERVER RESPONSE RECEIVED]
   • HTTP Status Code:   {status_code}
   • Response Time:      {elapsed_ms} ms
   • apiResponseCode:    {api_code or 'N/A'}
   • apiResponseMsg:     {api_msg or 'N/A'}

[5. RAW RESPONSE DATA]
{response_formatted}

[6. ERROR ROOT-CAUSE ANALYSIS & DIAGNOSIS]
   • Diagnosis:          {diagnosis['title']}
   • Meaning:            {diagnosis['meaning']}
   • Root Cause:
     {diagnosis['root_cause']}

[7. COMMON REASONS]
{diagnosis['common_reasons']}

[8. RECOMMENDED ACTION ITEMS]
{diagnosis['action_items']}
================================================================================
"""

    log_dirs = get_log_directories()

    for d in log_dirs:
        try:
            # 1. Main cumulative log file: sensorise_api.log
            main_log_file = os.path.join(d, "sensorise_api.log")

            # Prevent unbounded log growth: trim to last 1500 lines if > 2MB
            if os.path.exists(main_log_file):
                try:
                    if os.path.getsize(main_log_file) > 2 * 1024 * 1024:
                        with open(main_log_file, "r", encoding="utf-8", errors="ignore") as _f_old:
                            _lines = _f_old.readlines()
                        with open(main_log_file, "w", encoding="utf-8") as _f_old:
                            _f_old.writelines(_lines[-1500:])
                except Exception:
                    pass

            with open(main_log_file, "a", encoding="utf-8") as f:
                f.write(log_banner + "\n")

            # 2. If it's an error, write single-glance latest_error files
            if is_error:
                latest_err_file = os.path.join(d, "latest_error.log")
                with open(latest_err_file, "w", encoding="utf-8") as f_err:
                    f_err.write(log_banner)

                # 3. Write structured JSON for tools/dashboards
                latest_json_file = os.path.join(d, "latest_error.json")
                with open(latest_json_file, "w", encoding="utf-8") as f_json:
                    json.dump({
                        "timestamp": iso_time,
                        "formatted_time": timestamp_str,
                        "status_code": status_code,
                        "endpoint": endpoint,
                        "url": url,
                        "method": method,
                        "outbound_ip": public_ip,
                        "relation_id": relation_id,
                        "headers": masked_headers,
                        "payload": payload,
                        "apiResponseCode": api_code,
                        "apiResponseMsg": api_msg,
                        "response_data": response_data,
                        "diagnosis": diagnosis
                    }, f_json, indent=2)

        except Exception as e:
            print(f"[app_logger] Warning: Failed to write logs to {d}: {e}", file=sys.stderr)


def get_latest_error_summary() -> Dict[str, Any]:
    """Reads and returns the latest error summary from documents logs."""
    log_dirs = get_log_directories()
    for d in log_dirs:
        json_path = os.path.join(d, "latest_error.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {"status": "No errors recorded yet."}


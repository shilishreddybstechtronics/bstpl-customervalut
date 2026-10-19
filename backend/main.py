#!/usr/bin/env python3
"""main.py - CustomerVault backend (FastAPI).

Serves the website (../frontend: HTML, CSS, JS) and the JSON API under /api/..., and talks to MySQL through database.py.

Setup:  pip install -r backend/requirements.txt
        copy backend/.env.example to backend/.env and enter your MySQL login
Run  :  python backend/main.py                      -> http://localhost:8000
   or   uvicorn main:app --reload --port 8000        (run inside the backend folder; auto-reload while you edit)
The database tables/columns are created automatically on start.
"""
import argparse
import json
import os
import re
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, unquote

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles

import database as db
from xlsxout import make_xlsx

BASE = os.path.dirname(os.path.abspath(__file__))              # backend/
FRONTEND = os.path.join(os.path.dirname(BASE), "frontend")     # the website files are served from ../frontend
PAGES = {"/": "index.html", "/index.html": "index.html", "/style.css": "style.css", "/script.js": "script.js"}   # everything else is in frontend/assets/
MAX_BODY = 100 * 1024 * 1024   # large Excel imports are sent as JSON
LOGIN_MAX_FAILS, LOGIN_WINDOW = 8, 300   # more than 8 wrong passwords from one address in 5 minutes -> wait
_FAILS = defaultdict(deque)               # ip -> times of recent failed logins
_FAILS_LOCK = threading.Lock()
TRUST_PROXY = os.environ.get("TRUST_PROXY", "").strip().lower() in ("1", "true", "yes", "on")   # or --trust-proxy: believe X-Forwarded-For (only behind your own reverse proxy)


def login_blocked(ip):
    now = time.time()
    with _FAILS_LOCK:
        q = _FAILS[ip]
        while q and now - q[0] > LOGIN_WINDOW:
            q.popleft()
        if not q:
            _FAILS.pop(ip, None)
        return len(q) >= LOGIN_MAX_FAILS


def login_failed(ip):
    with _FAILS_LOCK:
        _FAILS[ip].append(time.time())


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ---- what the Login Inventory records for every action that changes something: fn(body, response) -> (action, details)
def _f(b, name):
    for k, v in (b.get("fields") or {}).items():
        if str(k).strip().lower() == name:
            return str(v)
    return ""


def _dev_add(b, r):
    cust = b.get("new_customer") or db.customer_label(b.get("customer_id"))
    return "Added record", f"Customer: {cust}; IMEI: {_f(b, 'imei') or '-'}"


def _bulk(b, r):
    r = r or {}
    w = r.get("wiped")
    return "Bulk upload", ((f"REPLACED ALL DATA - deleted {w['customers']} customer(s) / {w['records']} record(s) / {w['cart']} Cart item(s) first; " if w else "")
                           + f"Imported {r.get('imported', 0)} record(s), " + (f"replaced values of {r.get('updated', 0)} existing record(s), " if b.get('on_duplicate') == 'replace' else "") + f"skipped {r.get('skipped', 0)} duplicate(s); "
                           f"customers: {', '.join(str(g.get('customer')) for g in (b.get('groups') or [])[:10])}")


ROUTES = {
    ("POST", "/devices"): _dev_add,
    ("POST", "/devices/bulk"): _bulk,
    ("POST", "/devices/sheet-upload"): lambda b, r: ("Sheet-name upload", f"Imported {(r or {}).get('imported', 0)} record(s), " + (f"replaced values of {(r or {}).get('updated', 0)} existing record(s), " if b.get('on_duplicate') == 'replace' else "") + f"skipped {(r or {}).get('skipped', 0)} duplicate(s); "
                                                   f"customers: {', '.join(str(g.get('customer')) for g in (b.get('groups') or [])[:10])}" + (f"; uses left: {(r or {}).get('left')}" if b.get('finish') else "")),
    ("POST", "/columns/delete"): lambda b, r: None if b.get("dry_run") else ("Deleted column", ", ".join(map(str, b.get("labels") or []))),
    ("POST", "/customers/rename-all"): lambda b, r: ("Renamed customers", f"{len(b.get('items') or [])} customer(s)"),
    ("POST", "/simdata/apply"): lambda b, r: None if b.get("dry_run") else ("SIM data upload", f"{b.get('provider') or 'provider file'}: updated {(r or {}).get('updated_records', 0)} record(s) in {len((r or {}).get('customers') or [])} customer(s), {(r or {}).get('provider_rows', 0)} file row(s), {(r or {}).get('not_found_total', 0)} ICCID(s) not found"),
    ("POST", "/export"): lambda b, r: ("Downloaded Excel", (r or {}).get("filename", "")),
    ("POST", "/change-password"): lambda b, r: ("Changed password", ""),
}


# ---- who may call what (see ROLES in config.py).  admin = everything; staff = everything except user management;
#      limited = only the routes listed here (fetch / download / insert / edit record details).
ANY_ROLE = {("GET", "/me"), ("POST", "/logout"), ("POST", "/change-password")}
ADMIN_ONLY = [("GET", r"/users"), ("POST", r"/users"), ("DELETE", r"/users/.+"),       # Manage Users
              ("GET", r"/activity"),                                                        # Login Inventory
              ("GET", r"/trash"), ("GET", r"/trash/\d+"), ("DELETE", r"/trash/\d+"), ("POST", r"/trash/\d+/restore"),   # Cart
              ("DELETE", r"/customers/\d+")]                                               # deleting a customer
LIMITED_OK = [("GET", r"/bootstrap"), ("GET", r"/devices"), ("GET", r"/alerts"), ("POST", r"/fetch/bulk"),
              ("POST", r"/devices"), ("POST", r"/devices/bulk/validate"), ("POST", r"/devices/bulk"),
              ("POST", r"/export"), ("PATCH", r"/devices/\d+")]


def allowed(role, method, p):
    if (method, p) in ANY_ROLE:
        return True
    if any(m == method and re.fullmatch(rx, p) for m, rx in ADMIN_ONLY):
        return role == "admin"
    if role in ("admin", "standard", "staff"):
        return True
    return any(m == method and re.fullmatch(rx, p) for m, rx in LIMITED_OK)


def describe(method, p):
    m = re.fullmatch(r"/users/(.+)", p)
    if m and method == "DELETE":
        return lambda b, r: ("Removed user", f"{(r or {}).get('name', '')} ({(r or {}).get('removed', unquote(m.group(1)))})")
    if (method, p) in ROUTES:
        return ROUTES[(method, p)]
    m = re.fullmatch(r"/devices/(\d+)", p)
    if m and method == "PATCH":
        return lambda b, r: ("Edited record", f"Record #{m.group(1)}; changed: {', '.join(map(str, (b.get('fields') or {}).keys())) or '-'}")
    if m and method == "DELETE":
        return lambda b, r: ("Deleted record", f"Record #{m.group(1)}; IMEI: {(r or {}).get('imei', '-')} (moved to Cart)")
    m = re.fullmatch(r"/customers/(\d+)/merge", p)
    if m and method == "POST":
        return lambda b, r: ("Merged customers", f"{(r or {}).get('from', '')} -> {(r or {}).get('into', '')} ({(r or {}).get('merged', 0)} record(s) moved)")
    m = re.fullmatch(r"/customers/(\d+)", p)
    if m and method == "PATCH":
        return lambda b, r: ("Renamed customer", f"Customer #{m.group(1)} -> {b.get('name')}")
    if m and method == "DELETE":
        return lambda b, r: ("Deleted customer", f"{(r or {}).get('name', b.get('name'))} ({(r or {}).get('records', 0)} record(s), moved to Cart)")
    m = re.fullmatch(r"/trash/(\d+)/restore", p)
    if m and method == "POST":
        return lambda b, r: ("Restored from Cart", f"{(r or {}).get('restored', '')}: {(r or {}).get('label', '')} ({(r or {}).get('name', '')}, {(r or {}).get('records', 0)} record(s))")
    m = re.fullmatch(r"/trash/(\d+)", p)
    if m and method == "DELETE":
        return lambda b, r: ("Permanently deleted", f"{(r or {}).get('kind', '')}: {(r or {}).get('label', '')} ({(r or {}).get('name', '')}, {(r or {}).get('records', 0)} record(s)) removed from the Cart")
    return None


class Ctx:
    """One API request: who is calling, the JSON body, the Login Inventory entry - and the routes themselves (api())."""

    def __init__(self, request, raw):
        self.request, self.raw = request, raw
        self._b = self._act = self._emp = None   # body cache / what to write in the login inventory / who is logged in

    def ip(self):   # X-Forwarded-For is a header anyone can fake, so it is ignored unless --trust-proxy is given
        fwd = self.request.headers.get("x-forwarded-for", "").split(",")[0].strip() if TRUST_PROXY else ""
        return fwd or (self.request.client.host if self.request.client else "")

    def audit(self, resp=None):   # called once the request succeeded: writes one line in the Login Inventory
        if self._act and self._emp:
            try:
                what = self._act(self._b or {}, resp)
            except Exception:
                what = None
            if what:
                db.log_activity(self._emp["id"], self._emp["name"], what[0], what[1], self.ip())
        self._act = None

    # ---- helpers
    def send_json(self, obj, status=200):
        if status < 400:
            self.audit(obj)
        return Response(json.dumps(obj), status_code=status, media_type="application/json; charset=utf-8",
                        headers={"Cache-Control": "no-store"})

    def send_bytes(self, data, ctype, filename):
        self.audit({"filename": filename})
        return Response(data, media_type=ctype, headers={"Content-Disposition": f'attachment; filename="{filename}"',
                                                         "Cache-Control": "no-store"})

    def body(self):
        if self._b is not None:
            return self._b
        if len(self.raw) > MAX_BODY:
            raise ApiError(413, "Upload is too large")
        data = json.loads(self.raw or b"{}")
        if not isinstance(data, dict):
            raise ApiError(400, "Invalid request")
        self._b = data
        return data

    def token(self):
        h = self.request.headers.get("authorization", "")
        return h[7:] if h.startswith("Bearer ") else ""

    def user(self):
        u = db.session_user(self.token())
        if not u:
            raise ApiError(401, "Session expired - please login again")
        return u

    # ---- the API routes
    def api(self, method, p, qs):
        # ---- public
        if (method, p) == ("POST", "/register"):
            b = self.body()
            db.register(b.get("name"), b.get("emp_id"), b.get("password"))
            db.log_activity(str(b.get("emp_id") or "").strip(), str(b.get("name") or "").strip(), "Registered", "New account created", self.ip())
            return self.send_json({"ok": True})
        if (method, p) == ("POST", "/login"):
            b = self.body()
            if login_blocked(self.ip()):
                raise ApiError(429, "Too many failed logins - wait a few minutes and try again")
            try:
                token, emp = db.login(b.get("user"), b.get("password"))
            except PermissionError:
                login_failed(self.ip())
                db.log_activity("", str(b.get("user") or "").strip()[:200], "Failed login", "Wrong ID/name or password", self.ip())
                raise
            db.log_activity(emp["id"], emp["name"], "Login", "Signed in", self.ip())
            return self.send_json({"token": token, "employee": emp})

        if (method, p) == ("GET", "/check-user"):   # registration form: is this name / ID already taken?
            return self.send_json(db.check_user(qs.get("name"), qs.get("emp_id")))

        # ---- everything below needs a logged-in employee
        emp = self.user()
        self._emp = emp
        self._act = describe(method, p)
        role = emp.get("role") if emp.get("role") in ("admin", "standard", "staff") else "limited"
        if not allowed(role, method, p):
            raise ApiError(403, "You do not have permission to do this")
        if (method, p) == ("GET", "/me"):
            return self.send_json({"employee": emp})
        if (method, p) == ("POST", "/logout"):
            db.log_activity(emp["id"], emp["name"], "Logout", "Signed out", self.ip())
            db.logout(self.token())
            return self.send_json({"ok": True})
        if (method, p) == ("POST", "/change-password"):
            b = self.body()
            return self.send_json(db.change_password(emp["id"], b.get("current"), b.get("new"), self.token()))
        if (method, p) == ("GET", "/activity"):   # Login Inventory: who did what, and when
            return self.send_json(db.list_activity(qs.get("emp"), qs.get("action"), qs.get("from"), qs.get("to"),
                                                   qs.get("q"), int(qs.get("limit") or 2000)))
        if (method, p) == ("GET", "/bootstrap"):
            return self.send_json(db.bootstrap(emp["id"], sync=bool(qs.get("sync"))))
        if (method, p) == ("GET", "/devices"):
            items = db.list_devices(qs.get("field", "*"), qs.get("q", ""), qs.get("customer_id"))
            return self.send_json({"items": items})
        if (method, p) == ("POST", "/devices"):   # add ONE record (the website itself uses Bulk Upload)
            b = self.body()
            return self.send_json(db.create_device(emp["id"], b.get("customer_id"), b.get("new_customer"), b.get("fields")))
        if (method, p) == ("POST", "/devices/bulk/validate"):   # Bulk Upload preview: valid / duplicate / invalid per row
            return self.send_json(db.bulk_validate(self.body().get("rows"), bool(self.body().get("replace_all"))))
        if (method, p) == ("POST", "/devices/bulk"):
            b = self.body()
            if b.get("replace_all") and role != "admin":   # deleting every customer is for admins only
                raise ApiError(403, "You do not have permission to delete all customers")
            r = db.import_groups(emp["id"], b.get("groups"), "replace" if b.get("on_duplicate") == "replace" else "skip", bool(b.get("replace_all")))
            return self.send_json(r)
        if (method, p) == ("POST", "/devices/sheet-upload"):   # Upload by Sheet Name (admin / staff only, limited number of uses)
            b = self.body()
            if not isinstance(b.get("groups"), list):
                raise ApiError(400, "Invalid request")
            return self.send_json(db.sheet_upload(emp["id"], b["groups"], bool(b.get("finish")), bool(b.get("saved_before")), b.get("on_duplicate") or "skip"))
        if (method, p) == ("POST", "/fetch/bulk"):   # Bulk Fetch: many values of one column -> matching records
            b = self.body()
            if not isinstance(b.get("values"), list):
                raise ApiError(400, "Invalid request")
            return self.send_json(db.bulk_fetch(b.get("column"), b["values"], b.get("customer_id") or None, b.get("sim_type") or None))
        if (method, p) == ("POST", "/simdata/apply"):   # SIM provider file (ICCID, MSISDN1, MSISDN2, ACT DATE, EXP DATE) -> every customer record with that ICCID
            b = self.body()
            if not isinstance(b.get("rows"), list):
                raise ApiError(400, "Invalid request")
            return self.send_json(db.apply_sim_data(b["rows"], b.get("overwrite", True) is not False, bool(b.get("dry_run")), b.get("provider") or ""))
        if (method, p) == ("GET", "/users"):   # Manage Users (admin only)
            return self.send_json({"items": db.list_users()})
        if (method, p) == ("POST", "/users"):   # Add Member (admin only): the new member is an admin
            b = self.body()
            r = db.create_member(b.get("name"), b.get("emp_id"), b.get("password"), "admin")
            db.log_activity(emp["id"], emp["name"], "Added user", f"{r['name']} ({r['id']}) as admin", self.ip())
            return self.send_json(r)
        m = re.fullmatch(r"/users/(.+)", p)
        if m and method == "DELETE":
            return self.send_json(db.delete_user(unquote(m.group(1)), emp["id"]))
        m = re.fullmatch(r"/devices/(\d+)", p)
        if m and method == "PATCH":
            fields = self.body().get("fields")
            if role == "limited" and isinstance(fields, dict):   # editing a record never creates a new column for this role
                with db.reader() as c:
                    known = {x["label"].lower() for x in db.get_columns(c)}
                bad = [k for k in fields if db.canon_label(k).lower() not in known]
                if bad:
                    raise ApiError(403, "You cannot add new columns: " + ", ".join(map(str, bad[:5])))
            return self.send_json(db.update_device(int(m.group(1)), fields))
        if m and method == "DELETE":
            return self.send_json(db.delete_device(int(m.group(1)), emp))
        if (method, p) == ("POST", "/customers/rename-all"):   # rename many customers at once
            return self.send_json(db.rename_customers(self.body().get("items")))
        m = re.fullmatch(r"/customers/(\d+)/merge", p)
        if m and method == "POST":   # merge this customer's records into another existing customer
            b = self.body()
            return self.send_json(db.merge_customers(int(m.group(1)), b.get("target_id"), b.get("source_name"), b.get("target_name")))
        m = re.fullmatch(r"/customers/(\d+)", p)
        if m and method == "PATCH":   # rename a customer
            return self.send_json(db.rename_customer(int(m.group(1)), self.body().get("name")))
        if m and method == "DELETE":   # delete a customer: its MySQL table + registry row
            return self.send_json(db.delete_customer(int(m.group(1)), self.body().get("name"), emp))
        # ---- Cart: deleted customers / records wait here until restored or deleted permanently
        if (method, p) == ("GET", "/trash"):
            return self.send_json({"items": db.list_trash()})
        m = re.fullmatch(r"/trash/(\d+)", p)
        if m and method == "GET":
            return self.send_json(db.trash_view(int(m.group(1))))
        if m and method == "DELETE":
            return self.send_json(db.purge_trash(int(m.group(1)), self.body().get("name")))
        m = re.fullmatch(r"/trash/(\d+)/restore", p)
        if m and method == "POST":
            return self.send_json(db.restore_trash(int(m.group(1)), emp))
        if (method, p) == ("POST", "/export"):   # table on screen -> real .xlsx file
            b = self.body()
            fname = re.sub(r"[^A-Za-z0-9._-]+", "_", str(b.get("filename") or "customer_data.xlsx"))
            fname = fname if fname.lower().endswith(".xlsx") else fname + ".xlsx"
            return self.send_bytes(make_xlsx(b.get("headers") or [], b.get("rows") or []),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", fname)
        if (method, p) == ("POST", "/columns/delete"):   # delete one or many (non-mandatory) columns from every customer table
            b = self.body()
            return self.send_json(db.delete_columns(b.get("labels"), bool(b.get("dry_run"))))
        if (method, p) == ("GET", "/alerts"):
            days = max(0, min(int(qs.get("days", 30)), 3650))
            after = qs.get("after")   # set = only devices expiring AFTER today+`after` days (used for "after 4 months")
            after = max(0, min(int(after), 3650)) if after not in (None, "") else None
            return self.send_json({"items": db.alerts(days, after)})
        raise ApiError(404, "Unknown API route")


def handle(request, raw, p, qs):
    """Runs one API request (in a worker thread - the MySQL code is blocking) and turns every error into the JSON the website expects."""
    ctx = Ctx(request, raw)
    try:
        return ctx.api(request.method, p, qs)
    except ApiError as e:
        return ctx.send_json({"error": str(e)}, e.status)
    except PermissionError as e:
        return ctx.send_json({"error": str(e)}, 401)
    except LookupError as e:
        return ctx.send_json({"error": str(e).strip("'\"")}, 404)
    except db.CustomerExists as e:   # renamed to a name another customer already has -> the website offers to merge
        return ctx.send_json({"error": str(e), "exists": e.info}, 409)
    except db.DuplicateIMEI as e:   # same IMEI already saved (any customer) -> the website shows a popup
        return ctx.send_json({"error": str(e), "duplicate": e.info}, 409)
    except ValueError as e:   # includes bad JSON
        return ctx.send_json({"error": str(e)}, 400)
    except Exception as e:
        traceback.print_exc()
        return ctx.send_json({"error": f"Server error: {type(e).__name__}: {e}"}, 500)


def watch_config():   # a customer table added / renamed / dropped directly in MySQL reaches the website within ~3 seconds
    last_err = ""
    while True:
        time.sleep(3)
        try:
            db.reconcile()
        except Exception as e:   # keep watching, but say so (once per distinct message) instead of failing silently
            if str(e) != last_err:
                last_err = str(e)
                sys.stderr.write(f"  note: background check of the customer tables failed: {e}\n")


@asynccontextmanager
async def lifespan(app):
    try:
        db.init_db()   # creates the system tables; every customer is its own table (see database.py)
    except Exception as e:
        msg = db.explain_connect_error(e) + "\nCheck backend/.env and that MySQL is running."
        sys.stderr.write("\n" + msg + "\n")
        raise RuntimeError(msg)
    threading.Thread(target=watch_config, daemon=True).start()
    print(f"Database                 ->  {db.DB_LABEL}")
    yield
    try:
        db.close_pool()
    except Exception:
        pass


app = FastAPI(title="CustomerVault", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


# Website on another address (Vercel): list its address(es) in CORS_ORIGINS, comma separated, e.g.
#   CORS_ORIGINS=https://my-site.vercel.app,https://vault.mycompany.com      (no trailing slash)
# Not needed when the backend serves the pages itself (local run). Login uses a Bearer token, not cookies.
_ORIGINS = [o.strip().rstrip("/") for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
if _ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=_ORIGINS, allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type"], expose_headers=["Content-Disposition"], max_age=600)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PATCH", "DELETE"], include_in_schema=False)
async def api_entry(path: str, request: Request):
    length = int(request.headers.get("content-length") or 0)
    if length > MAX_BODY:
        return Response(json.dumps({"error": "Upload is too large"}), status_code=413, media_type="application/json")
    raw = await request.body()
    # the path exactly as sent (still percent-encoded), minus "/api" - the same value the routes were written for
    p = (request.scope.get("raw_path") or request.url.path.encode()).decode("latin-1").split("?", 1)[0][4:]
    qs = {k: v[0] for k, v in parse_qs(request.url.query).items()}
    return await run_in_threadpool(handle, request, raw, p, qs)


def _page(name):
    def serve():
        f = os.path.join(FRONTEND, name)
        if not os.path.isfile(f):
            return Response(json.dumps({"error": "Not found"}), status_code=404, media_type="application/json")
        return FileResponse(f, headers={"Cache-Control": "no-cache"})
    return serve


for _url, _name in PAGES.items():
    app.add_api_route(_url, _page(_name), methods=["GET", "HEAD"], include_in_schema=False)
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND, "assets")), name="assets")   # extras.css / extras.js / logos / optional xlsx.full.min.js


def main():
    global TRUST_PROXY
    ap = argparse.ArgumentParser(description="CustomerVault server (FastAPI)")
    ap.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to let other computers on your network connect")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--trust-proxy", action="store_true", help="read the client address from X-Forwarded-For (only behind your own reverse proxy)")
    a = ap.parse_args()
    TRUST_PROXY = TRUST_PROXY or a.trust_proxy
    print(f"CustomerVault is starting ->  http://{'localhost' if a.host in ('127.0.0.1', '0.0.0.0') else a.host}:{a.port}   (Ctrl+C to stop)")
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")


if __name__ == "__main__":
    main()

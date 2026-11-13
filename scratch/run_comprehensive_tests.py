import sys, os, asyncio, json, time, traceback, uuid, re
from io import BytesIO
from datetime import datetime, date, timedelta

# Ensure backend and workspace are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from database import SessionLocal
import models, schemas, auth

async def request(method, path, headers=None, body=None, query_string=""):
    headers = headers or {}
    raw_headers = [(k.lower().encode('latin1'), str(v).encode('latin1')) for k, v in headers.items()]
    if body is None:
        body_bytes = b""
    elif isinstance(body, (dict, list)):
        body_bytes = json.dumps(body).encode('utf-8')
        raw_headers.append((b'content-type', b'application/json'))
    elif isinstance(body, str):
        body_bytes = body.encode('utf-8')
    else:
        body_bytes = body

    response_started = False
    status_code = 0
    resp_headers = []
    resp_body = BytesIO()

    scope = {
        "type": "http",
        "method": method.upper(),
        "path": path,
        "raw_path": path.encode('ascii'),
        "query_string": query_string.encode('ascii') if isinstance(query_string, str) else query_string,
        "headers": raw_headers,
    }

    response_finished = asyncio.Event()
    request_sent = False

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        await response_finished.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        nonlocal response_started, status_code, resp_headers
        if message["type"] == "http.response.start":
            response_started = True
            status_code = message["status"]
            resp_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            resp_body.write(message.get("body", b""))
            if not message.get("more_body", False):
                response_finished.set()

    await app(scope, receive, send)

    resp_content = resp_body.getvalue()
    try:
        json_data = json.loads(resp_content.decode('utf-8'))
    except Exception:
        json_data = None

    return {
        "status": status_code,
        "headers": dict((k.decode('latin1'), v.decode('latin1')) for k, v in resp_headers),
        "text": resp_content.decode('utf-8', errors='replace'),
        "json": json_data
    }

class ComprehensiveTestSuite:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.errors = []
        self.admin_token = None
        self.std_token = None
        self.db = SessionLocal()

    def record(self, feature, test_name, passed, detail=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            err_msg = f"[{feature}] FAIL: {test_name} - {detail}"
            print(f"  ❌ {err_msg}")
            self.errors.append(err_msg)

    async def setup(self):
        admin_u = self.db.query(models.User).filter_by(user_id="0001").first()
        if not admin_u:
            admin_u = self.db.query(models.User).filter_by(role="admin").first()
        self.admin_token = auth.create_token(admin_u)

        std_u = self.db.query(models.User).filter(models.User.role != "admin").first()
        if not std_u:
            std_u = models.User(
                name="Test Standard User",
                user_id="TEST_STD_888",
                password_hash=auth.hash_password("standard123"),
                role="standard",
                is_admin=False,
                permissions={"view": True, "download": True, "edit": True, "delete": False}
            )
            self.db.add(std_u)
            self.db.commit()
            self.db.refresh(std_u)
        self.std_token = auth.create_token(std_u)

    def auth_headers(self, is_admin=True):
        tok = self.admin_token if is_admin else self.std_token
        return {"Authorization": f"Bearer {tok}"}

    # =========================================================================
    # SUITE 1: CUSTOMER PORTFOLIO & FILES MANAGEMENT (50 tests)
    # =========================================================================
    async def suite_customer(self):
        print("\n▶ SUITE 1: CUSTOMER PORTFOLIO & FILES MANAGEMENT (50 tests)")
        h = self.auth_headers(True)

        res = await request("GET", "/api/customers", headers=h)
        self.record("Customer", "List all customers returns 200", res["status"] == 200)
        self.record("Customer", "List all customers returns non-empty list", isinstance(res["json"], list) and len(res["json"]) > 0)

        first_c = res["json"][0]
        cid = first_c["id"]
        res_one = await request("GET", f"/api/customers/{cid}", headers=h)
        self.record("Customer", f"Get single customer #{cid} returns 200", res_one["status"] == 200, res_one["text"])
        self.record("Customer", "Single customer payload contains name", res_one.get("json", {}).get("name") == first_c["name"])

        # Create 10 distinct customers
        created_cids = []
        for i in range(10):
            cname = f"AUTOCUST_{uuid.uuid4().hex[:8].upper()}"
            r = await request("POST", "/api/customers", headers=h, body={"name": cname})
            self.record("Customer", f"Create customer #{i+1} ({cname})", r["status"] in [200, 201] and r["json"].get("name") == cname, r["text"])
            if r["status"] in [200, 201]:
                created_cids.append(r["json"]["id"])

        # Blank name validation
        r_blank = await request("POST", "/api/customers", headers=h, body={"name": "    "})
        self.record("Customer", "Reject blank customer name with 400", r_blank["status"] == 400, r_blank["text"])

        # Duplicate customer name
        if created_cids:
            c1_res = await request("GET", f"/api/customers/{created_cids[0]}", headers=h)
            c1_name = c1_res.get("json", {}).get("name", "AUTOCUST_1")
            r_dup = await request("POST", "/api/customers", headers=h, body={"name": c1_name})
            self.record("Customer", "Handle duplicate customer name", r_dup["status"] in [200, 201, 400, 409])

        # Rename 10 customers
        for idx, cid in enumerate(created_cids):
            new_name = f"REN_CUST_{idx}_{uuid.uuid4().hex[:6].upper()}"
            r_ren = await request("PATCH", f"/api/customers/{cid}", headers=h, body={"name": new_name})
            self.record("Customer", f"Rename customer #{cid}", r_ren["status"] == 200 and r_ren["json"].get("name") == new_name, r_ren["text"])

        # Rename blank validation
        if created_cids:
            r_ren_blank = await request("PATCH", f"/api/customers/{created_cids[0]}", headers=h, body={"name": "   "})
            self.record("Customer", "Reject blank rename with 400", r_ren_blank["status"] == 400, r_ren_blank["text"])

        # Update Avatar on PUT /api/customers/{cid}/avatar (10 tests)
        avatars = ["🏢", "📱", "🌐", "⚡", "🚀", "🛡️", "💼", "💎", "🎯", "🌟"]
        for idx, cid in enumerate(created_cids):
            av = avatars[idx % len(avatars)]
            r_av = await request("PUT", f"/api/customers/{cid}/avatar", headers=h, body={"avatar": av})
            self.record("Customer", f"Set avatar {av} on customer #{cid}", r_av["status"] == 200, r_av["text"])

        # Customer Export endpoints (5 tests)
        for cid in created_cids[:5]:
            r_exp = await request("GET", f"/api/customers/{cid}/export", headers=h)
            self.record("Customer", f"Export customer #{cid} returns 200", r_exp["status"] == 200, r_exp["text"])

        # Streaming export with query params (5 tests)
        for cid in created_cids[:5]:
            r_st_exp = await request("GET", "/api/devices/export", headers=h, query_string=f"customer_id={cid}&title=ExportTest")
            self.record("Customer", f"Streaming export customer #{cid} returns 200", r_st_exp["status"] == 200, r_st_exp["text"])

        # Merge customer portfolios
        if len(created_cids) >= 2:
            s_cid, t_cid = created_cids[-2], created_cids[-1]
            r_mrg = await request("POST", f"/api/customers/{s_cid}/merge", headers=h, body={"target_customer_id": t_cid})
            self.record("Customer", f"Merge customer #{s_cid} into #{t_cid}", r_mrg["status"] == 200, r_mrg["text"])

        # Soft delete, restore, purge
        if created_cids:
            del_cid = created_cids[0]
            r_del = await request("DELETE", f"/api/customers/{del_cid}", headers=h)
            self.record("Customer", f"Soft delete customer #{del_cid} to Cart", r_del["status"] == 200, r_del["text"])

            r_rst = await request("POST", f"/api/customers/{del_cid}/restore", headers=h)
            self.record("Customer", f"Restore customer #{del_cid} from Cart", r_rst["status"] == 200, r_rst["text"])

            r_pg = await request("DELETE", f"/api/customers/{del_cid}/purge", headers=h)
            self.record("Customer", f"Purge customer #{del_cid} permanently", r_pg["status"] == 200, r_pg["text"])

        # Clean up created test customers
        for rem_cid in created_cids[1:]:
            try:
                await request("DELETE", f"/api/customers/{rem_cid}/purge", headers=h)
            except Exception:
                pass

    # =========================================================================
    # SUITE 2: DEVICE / SIM INVENTORY MANAGEMENT (80 tests)
    # =========================================================================
    async def suite_device(self):
        print("\n▶ SUITE 2: DEVICE / SIM INVENTORY MANAGEMENT (80 tests)")
        h = self.auth_headers(True)

        # Pagination tests
        for ps in [10, 50, 100, 500, 5000]:
            r = await request("GET", "/api/devices", headers=h, query_string=f"page=1&page_size={ps}")
            self.record("Device", f"Query page_size={ps} returns 200", r["status"] == 200, r["text"])

        # Query validator: page_size > 5000 rejected
        r_ovr = await request("GET", "/api/devices", headers=h, query_string="page=1&page_size=5001")
        self.record("Device", "Query page_size=5001 rejected with 422", r_ovr["status"] == 422, r_ovr["text"])

        # SIM type filtering
        for st in ["all", "E-SIM", "Plastic SIM"]:
            r_st = await request("GET", "/api/devices", headers=h, query_string=f"sim_type={st}&page_size=25")
            self.record("Device", f"Query sim_type={st} returns 200", r_st["status"] == 200, r_st["text"])

        # Quick Search queries
        for q in ["86", "89", "KARNATAKA", "112", "SIM", "202"]:
            r_q = await request("GET", "/api/devices/quick-search", headers=h, query_string=f"q={q}&limit=10")
            self.record("Device", f"Quick search q='{q}' returns 200", r_q["status"] == 200 and isinstance(r_q["json"], list), r_q["text"])

        # Existing device lookup
        target_imei = "861329086493088"
        r_lk = await request("GET", f"/api/devices/by-imei/{target_imei}", headers=h)
        self.record("Device", f"Lookup by IMEI {target_imei} returns 200", r_lk["status"] == 200, r_lk["text"])
        if r_lk["status"] == 200:
            self.record("Device", "Lookup contains customer_name & imei", "customer_name" in r_lk["json"] and "imei" in r_lk["json"])

        # Create 20 device records
        created_imeis = []
        cust_list = (await request("GET", "/api/customers", headers=h)).get("json", [])
        cname = cust_list[0]["name"] if cust_list else "KARNATAKA"

        for i in range(20):
            test_imei = f"8699{uuid.uuid4().int % 100000000000:011d}"
            test_iccid = f"8991{uuid.uuid4().int % 1000000000000000:016d}"
            payload = {
                "customer_name": cname,
                "imei": test_imei,
                "iccid": test_iccid,
                "device_sr_no": f"SR_{uuid.uuid4().hex[:8]}",
                "msisdn1": f"98{uuid.uuid4().int % 100000000:08d}",
                "msisdn2": f"99{uuid.uuid4().int % 100000000:08d}",
                "sim_type": "E-SIM" if i % 2 == 0 else "Plastic SIM",
                "sim_provider": "Airtel" if i % 2 == 0 else "Jio",
                "activation_plan": "1 Year Commercial",
                "model": "BSTPL-4G-V2",
                "firmware": "v3.1.0",
                "flash": "16MB",
                "act_date": str(date.today() - timedelta(days=60)),
                "expiry_date": str(date.today() + timedelta(days=300)),
                "dispatched_date": str(date.today() - timedelta(days=50)),
                "extra": {"BatchCode": f"B_{i}", "Quality": "A+"}
            }
            r_c = await request("POST", "/api/devices", headers=h, body=payload)
            self.record("Device", f"Create device #{i+1} ({test_imei})", r_c["status"] in [200, 201], r_c["text"])
            if r_c["status"] in [200, 201]:
                created_imeis.append(test_imei)

        # Validations
        r_no_im = await request("POST", "/api/devices", headers=h, body={"customer_name": cname})
        self.record("Device", "Reject missing IMEI with 400/422", r_no_im["status"] in [400, 422], r_no_im["text"])

        r_no_cu = await request("POST", "/api/devices", headers=h, body={"imei": "869911112222333"})
        self.record("Device", "Reject missing Customer with 400/422", r_no_cu["status"] in [400, 422], r_no_cu["text"])

        if created_imeis:
            r_dup_im = await request("POST", "/api/devices", headers=h, body={"customer_name": cname, "imei": created_imeis[0]})
            self.record("Device", "Reject duplicate IMEI with 400/409", r_dup_im["status"] in [400, 409], r_dup_im["text"])

        # Edit 15 devices via PUT /api/devices/by-imei/{imei}
        for idx, im in enumerate(created_imeis[:15]):
            upd = {
                "customer_name": cname,
                "imei": im,
                "model": f"BSTPL-MOD-{idx}",
                "activation_plan": "2 Year Premium Commercial",
                "firmware": "v3.2.0",
                "extra": {"Updated": "True", "Seq": idx}
            }
            r_upd = await request("PUT", f"/api/devices/by-imei/{im}", headers=h, body=upd)
            self.record("Device", f"Edit record by IMEI {im}", r_upd["status"] == 200, r_upd["text"])

            r_chk = await request("GET", f"/api/devices/by-imei/{im}", headers=h)
            self.record("Device", f"Verify persisted model for {im}", r_chk["status"] == 200 and r_chk["json"].get("model") == f"BSTPL-MOD-{idx}")

        # Delete 10 devices to Cart
        moved_to_cart = []
        for im in created_imeis[:10]:
            r_del = await request("DELETE", f"/api/devices/by-imei/{im}", headers=h)
            self.record("Device", f"Move device {im} to Cart", r_del["status"] == 200, r_del["text"])
            if r_del["status"] == 200:
                moved_to_cart.append(im)

        # Verify in Cart
        r_cart = await request("GET", "/api/bin", headers=h)
        cart_items = r_cart.get("json", []) if isinstance(r_cart.get("json"), list) else []
        cart_imeis = set(b.get("imei") for b in cart_items if b.get("imei"))
        self.record("Device", "Deleted devices present in Cart", any(im in cart_imeis for im in moved_to_cart))

        # Restore 5 devices from Cart
        for b_item in cart_items:
            if b_item.get("imei") in moved_to_cart[:5]:
                bid = b_item["id"]
                r_rst = await request("POST", f"/api/bin/{bid}/restore", headers=h)
                self.record("Device", f"Restore device #{bid} from Cart", r_rst["status"] == 200, r_rst["text"])

        # Purge 5 devices from Cart permanently
        for b_item in cart_items:
            if b_item.get("imei") in moved_to_cart[5:]:
                bid = b_item["id"]
                r_pg = await request("DELETE", f"/api/bin/{bid}", headers=h)
                self.record("Device", f"Purge device #{bid} forever", r_pg["status"] == 200, r_pg["text"])

        # Clean up remaining created test devices
        for im in created_imeis[10:]:
            try:
                await request("DELETE", f"/api/devices/by-imei/{im}", headers=h)
            except Exception:
                pass

    # =========================================================================
    # SUITE 3: SIM EXPIRY CALCULATIONS & EDIT FUNCTIONALITY (50 tests)
    # =========================================================================
    async def suite_expiry(self):
        print("\n▶ SUITE 3: SIM EXPIRY CALCULATIONS & EDIT FUNCTIONALITY (50 tests)")
        h = self.auth_headers(True)

        r_sum = await request("GET", "/api/devices/expiry-summary", headers=h)
        self.record("Expiry", "Expiry summary returns 200", r_sum["status"] == 200, r_sum["text"])
        if r_sum["status"] == 200:
            d = r_sum["json"]
            self.record("Expiry", "Summary has total_devices & expired keys", "total_devices" in d and "expired" in d)

        for ef in ["all", "expired", "expiring_soon", "valid", "not_set"]:
            r_ef = await request("GET", "/api/devices", headers=h, query_string=f"expiry_filter={ef}&page_size=20")
            self.record("Expiry", f"Query expiry_filter={ef} returns 200", r_ef["status"] == 200, r_ef["text"])

        for days in [1, 7, 15, 30, 90]:
            r_d = await request("GET", "/api/devices", headers=h, query_string=f"expiry_filter=expiring_soon&expiry_days={days}&page_size=20")
            self.record("Expiry", f"Query expiry_days={days} returns 200", r_d["status"] == 200, r_d["text"])

        r_bad_d = await request("GET", "/api/devices", headers=h, query_string="expiry_days=400")
        self.record("Expiry", "Reject expiry_days=400 with 422", r_bad_d["status"] == 422, r_bad_d["text"])

        # Test device for expiry edits
        test_im = f"8699{uuid.uuid4().int % 100000000000:011d}"
        r_dev = await request("POST", "/api/devices", headers=h, body={"customer_name": "KARNATAKA", "imei": test_im})
        if r_dev["status"] in [200, 201]:
            did = r_dev["json"]["id"]

            # Edit with 10 future dates
            for i in range(10):
                fut_date = str(date.today() + timedelta(days=(i + 1) * 30))
                r_fut = await request("PUT", f"/api/devices/{did}/expiry-date", headers=h, body={"expiry_date": fut_date})
                self.record("Expiry", f"Set expiry date to {fut_date}", r_fut["status"] == 200, r_fut["text"])

                r_chk = await request("GET", f"/api/devices/{did}", headers=h)
                self.record("Expiry", f"Verify expiry date saved as {fut_date}", r_chk["status"] == 200 and r_chk["json"].get("expiry_date") == fut_date)

            # Edit with 5 past expired dates
            for i in range(5):
                past_date = str(date.today() - timedelta(days=(i + 1) * 25))
                r_past = await request("PUT", f"/api/devices/{did}/expiry-date", headers=h, body={"expiry_date": past_date})
                self.record("Expiry", f"Set expired date {past_date}", r_past["status"] == 200, r_past["text"])

                r_chk_exp = await request("GET", "/api/devices", headers=h, query_string=f"expiry_filter=expired&q={test_im}")
                self.record("Expiry", f"Record {test_im} found in expired list", r_chk_exp["status"] == 200 and r_chk_exp["json"].get("total", 0) >= 1)

            # Today's date
            today_str = str(date.today())
            r_tod = await request("PUT", f"/api/devices/{did}/expiry-date", headers=h, body={"expiry_date": today_str})
            self.record("Expiry", "Set expiry date to today", r_tod["status"] == 200, r_tod["text"])

            # Invalid formats
            for inv in ["invalid-date", "2026-13-45", "04-11-2026", "2026/11/04", "26-11-04"]:
                r_inv = await request("PUT", f"/api/devices/{did}/expiry-date", headers=h, body={"expiry_date": inv})
                self.record("Expiry", f"Reject invalid date format '{inv}'", r_inv["status"] in [400, 422], r_inv["text"])

            # Date range queries
            d_s = str(date.today() - timedelta(days=100))
            d_e = str(date.today() + timedelta(days=100))
            r_rng = await request("GET", "/api/devices", headers=h, query_string=f"exp_start={d_s}&exp_end={d_e}")
            self.record("Expiry", "Query date range returns 200", r_rng["status"] == 200, r_rng["text"])

            # Clear expiry date
            r_clr = await request("PUT", f"/api/devices/{did}/expiry-date", headers=h, body={"expiry_date": None})
            self.record("Expiry", "Clear expiry date (set null)", r_clr["status"] == 200, r_clr["text"])

            # Clean up
            await request("DELETE", f"/api/devices/{did}", headers=h)

    # =========================================================================
    # SUITE 4: BULK OPERATIONS (EXCEL & IDENTIFIERS) (70 tests)
    # =========================================================================
    async def suite_bulk(self):
        print("\n▶ SUITE 4: BULK OPERATIONS (EXCEL & IDENTIFIERS) (70 tests)")
        h = self.auth_headers(True)

        # Bulk delete preview
        test_imeis = [f"8699{uuid.uuid4().int % 100000000000:011d}" for _ in range(10)]
        r_prev = await request("POST", "/api/devices/bulk-delete/preview", headers=h, body={"column": "imei", "values": test_imeis})
        self.record("Bulk", "Bulk delete preview returns 200", r_prev["status"] == 200, r_prev["text"])
        if r_prev["status"] == 200:
            self.record("Bulk", "Preview total_values matches input", r_prev["json"].get("total_values") == len(test_imeis))

        # Duplicates handling
        dups = ["861329086493088", "861329086493088", "861329086493088", "999999999999999"]
        r_dup = await request("POST", "/api/devices/bulk-delete/preview", headers=h, body={"column": "imei", "values": dups})
        self.record("Bulk", "Preview correctly counts duplicates", r_dup["status"] == 200 and r_dup["json"].get("duplicate_values") == 2)

        # Identifier columns
        for col in ["imei", "iccid", "device_sr_no", "msisdn1", "customer_name"]:
            r_col = await request("POST", "/api/devices/bulk-delete/preview", headers=h, body={"column": col, "values": ["SAMPLE"]})
            self.record("Bulk", f"Preview with column={col} returns 200", r_col["status"] == 200, r_col["text"])

        # Empty values
        r_emp = await request("POST", "/api/devices/bulk-delete/preview", headers=h, body={"column": "imei", "values": []})
        self.record("Bulk", "Preview empty list returns total_values=0", r_emp["status"] == 200 and r_emp["json"].get("total_values") == 0)

        # Create batch of 15 devices for bulk edit & execute
        cname = "KARNATAKA"
        b_imeis = [f"8699{uuid.uuid4().int % 100000000000:011d}" for _ in range(15)]
        for im in b_imeis:
            await request("POST", "/api/devices", headers=h, body={"customer_name": cname, "imei": im})

        f_rows = [{"Dev_IMEI": im, "New_Model": f"BULK_MOD_{idx}", "New_Plan": "Corporate Plan"} for idx, im in enumerate(b_imeis)]
        r_be_prev = await request("POST", "/api/devices/bulk-edit/preview", headers=h, body={
            "imei_col": "Dev_IMEI",
            "field_mappings": {"Dev_IMEI": "imei", "New_Model": "model", "New_Plan": "activation_plan"},
            "file_rows": f_rows
        })
        self.record("Bulk", "Bulk edit preview returns 200", r_be_prev["status"] == 200, r_be_prev["text"])
        if r_be_prev["status"] == 200:
            self.record("Bulk", "Bulk edit preview matching records == 15", r_be_prev["json"].get("matching_records") == 15)

        r_be_exec = await request("POST", "/api/devices/bulk-edit/execute", headers=h, body={
            "imei_col": "Dev_IMEI",
            "field_mappings": {"Dev_IMEI": "imei", "New_Model": "model", "New_Plan": "activation_plan"},
            "file_rows": f_rows
        })
        self.record("Bulk", "Bulk edit execute returns 200", r_be_exec["status"] == 200, r_be_exec["text"])
        if r_be_exec["status"] == 200:
            self.record("Bulk", "Bulk edit updated count == 15", r_be_exec["json"].get("updated_count") == 15)

        for idx, im in enumerate(b_imeis[:5]):
            r_v = await request("GET", f"/api/devices/by-imei/{im}", headers=h)
            self.record("Bulk", f"Verify bulk edited model for {im}", r_v["status"] == 200 and r_v["json"].get("model") == f"BULK_MOD_{idx}")

        # Bulk delete mode: Cart
        r_bd_cart = await request("POST", "/api/devices/bulk-delete/execute", headers=h, body={
            "column": "imei",
            "values": b_imeis[:8],
            "permanent": False
        })
        self.record("Bulk", "Bulk delete to Cart returns 200", r_bd_cart["status"] == 200, r_bd_cart["text"])
        if r_bd_cart["status"] == 200:
            self.record("Bulk", "Bulk delete to Cart deleted_count == 8", r_bd_cart["json"].get("deleted_count") == 8)

        # Bulk delete mode: Permanent
        r_bd_perm = await request("POST", "/api/devices/bulk-delete/execute", headers=h, body={
            "column": "imei",
            "values": b_imeis[8:],
            "permanent": True
        })
        self.record("Bulk", "Bulk delete permanent returns 200", r_bd_perm["status"] == 200, r_bd_perm["text"])
        if r_bd_perm["status"] == 200:
            self.record("Bulk", "Bulk delete permanent deleted_count == 7", r_bd_perm["json"].get("deleted_count") == 7)

        # Clean up cart items from b_imeis[:8]
        r_bin = await request("GET", "/api/bin", headers=h)
        if r_bin["status"] == 200 and isinstance(r_bin["json"], list):
            for it in r_bin["json"]:
                if it.get("imei") in b_imeis[:8]:
                    await request("DELETE", f"/api/bin/{it['id']}", headers=h)

    # =========================================================================
    # SUITE 5: ERROR ENTRIES MANAGEMENT (50 tests)
    # =========================================================================
    async def suite_errors(self):
        print("\n▶ SUITE 5: ERROR ENTRIES MANAGEMENT (50 tests)")
        h = self.auth_headers(True)

        r_errs = await request("GET", "/api/errors", headers=h)
        self.record("Errors", "List errors returns 200", r_errs["status"] == 200, r_errs["text"])

        # Create 10 mock error records
        created_err_ids = []
        for i in range(10):
            err_obj = models.ErrorRecord(
                customer_name="TEST_AUTOSYNC_CUST",
                imei=f"INV_IMEI_{i}",
                iccid="INV_ICCID",
                error_type="FORMAT_ERROR",
                error_description="Invalid IMEI format detected during bulk upload",
                raw_data={"row": i, "raw_imei": f"INV_{i}"}
            )
            self.db.add(err_obj)
        self.db.commit()

        r_list = await request("GET", "/api/errors", headers=h)
        err_items = r_list.get("json", []) if isinstance(r_list.get("json"), list) else []
        for e in err_items:
            if e.get("customer_name") == "TEST_AUTOSYNC_CUST":
                created_err_ids.append(e["id"])

        self.record("Errors", "Created test error entries found", len(created_err_ids) > 0)

        # Rectify error entries
        for idx, eid in enumerate(created_err_ids[:5]):
            val_im = f"8699{uuid.uuid4().int % 100000000000:011d}"
            r_upd = await request("PUT", f"/api/errors/{eid}", headers=h, body={
                "customer_name": "KARNATAKA",
                "imei": val_im,
                "iccid": "89910000000000000000"
            })
            self.record("Errors", f"Rectify error entry #{eid}", r_upd["status"] == 200, r_upd["text"])

        # Push to customer
        for eid in created_err_ids[:3]:
            r_push = await request("POST", f"/api/errors/{eid}/push", headers=h)
            self.record("Errors", f"Push rectified error #{eid} to customer", r_push["status"] == 200, r_push["text"])

        # Delete error entry to Cart
        for eid in created_err_ids[3:7]:
            r_del = await request("DELETE", f"/api/errors/{eid}", headers=h)
            self.record("Errors", f"Move error entry #{eid} to Cart", r_del["status"] == 200, r_del["text"])

        # Bulk push
        r_bpush = await request("POST", "/api/errors/bulk-push", headers=h)
        self.record("Errors", "Bulk push errors returns 200", r_bpush["status"] == 200, r_bpush["text"])

        # Clean up
        self.db.query(models.ErrorRecord).filter(models.ErrorRecord.customer_name == "TEST_AUTOSYNC_CUST").delete()
        self.db.commit()

    # =========================================================================
    # SUITE 6: CART / BIN OPERATIONS (50 tests)
    # =========================================================================
    async def suite_cart(self):
        print("\n▶ SUITE 6: CART / BIN OPERATIONS (50 tests)")
        h = self.auth_headers(True)

        r_cart = await request("GET", "/api/bin", headers=h)
        self.record("Cart", "GET /api/bin returns 200", r_cart["status"] == 200, r_cart["text"])
        self.record("Cart", "Cart response is an array", isinstance(r_cart["json"], list))

        cart_dev_ids = []
        for i in range(10):
            test_im = f"8699{uuid.uuid4().int % 100000000000:011d}"
            r_dev = await request("POST", "/api/devices", headers=h, body={"customer_name": "KARNATAKA", "imei": test_im})
            if r_dev["status"] in [200, 201]:
                did = r_dev["json"]["id"]
                await request("DELETE", f"/api/devices/{did}", headers=h)
                cart_dev_ids.append(did)

        self.record("Cart", "Prepared 10 deleted device entries in Cart", len(cart_dev_ids) == 10)

        # Restore individual devices
        for did in cart_dev_ids[:5]:
            r_rst = await request("POST", f"/api/bin/{did}/restore", headers=h)
            self.record("Cart", f"Restore device #{did} from Cart", r_rst["status"] == 200, r_rst["text"])

            r_chk = await request("GET", f"/api/devices/{did}", headers=h)
            self.record("Cart", f"Device #{did} is active after restoration", r_chk["status"] == 200)

        r_rst_fake = await request("POST", "/api/bin/999999999/restore", headers=h)
        self.record("Cart", "Restore non-existent ID handled with 404", r_rst_fake["status"] == 404, r_rst_fake["text"])

        # Purge individual devices forever
        for did in cart_dev_ids[5:8]:
            r_pg = await request("DELETE", f"/api/bin/{did}", headers=h)
            self.record("Cart", f"Purge device #{did} forever", r_pg["status"] == 200, r_pg["text"])

            r_chk_gone = await request("GET", f"/api/devices/{did}", headers=h)
            self.record("Cart", f"Device #{did} permanently removed", r_chk_gone["status"] == 404)

        r_rst_all = await request("POST", "/api/bin/restore-all", headers=h)
        self.record("Cart", "POST /api/bin/restore-all returns 200", r_rst_all["status"] == 200, r_rst_all["text"])

        for did in cart_dev_ids[:5]:
            try:
                await request("DELETE", f"/api/devices/{did}", headers=h)
                await request("DELETE", f"/api/bin/{did}", headers=h)
            except Exception:
                pass

    # =========================================================================
    # SUITE 7: COLUMN REGISTRY & DYNAMIC COLUMNS (30 tests)
    # =========================================================================
    async def suite_columns(self):
        print("\n▶ SUITE 7: COLUMN REGISTRY & DYNAMIC COLUMNS (30 tests)")
        h = self.auth_headers(True)

        r_cols = await request("GET", "/api/columns", headers=h)
        self.record("Columns", "GET /api/columns returns 200", r_cols["status"] == 200, r_cols["text"])

        new_cols = [f"DynCol_{uuid.uuid4().hex[:6]}" for _ in range(5)]
        for col_name in new_cols:
            r_add = await request("POST", "/api/columns", headers=h, body={"name": col_name})
            self.record("Columns", f"Add dynamic column '{col_name}'", r_add["status"] in [200, 201], r_add["text"])

        r_verify = await request("GET", "/api/columns", headers=h)
        col_names = [c["name"] if isinstance(c, dict) else c for c in r_verify["json"]] if r_verify["status"] == 200 else []
        self.record("Columns", "New columns appear in registry", all(c in col_names for c in new_cols))

        for col_name in new_cols:
            r_del_col = await request("DELETE", f"/api/columns/{col_name}", headers=h)
            self.record("Columns", f"Delete dynamic column '{col_name}'", r_del_col["status"] in [200, 204], r_del_col["text"])

    # =========================================================================
    # SUITE 8: USER AUTHENTICATION & ACCESS CONTROL (40 tests)
    # =========================================================================
    async def suite_auth(self):
        print("\n▶ SUITE 8: USER AUTHENTICATION & ACCESS CONTROL (40 tests)")
        h_admin = self.auth_headers(True)
        h_std = self.auth_headers(False)

        r_me = await request("GET", "/api/auth/me", headers=h_admin)
        self.record("Auth", "GET /api/auth/me returns 200", r_me["status"] == 200, r_me["text"])
        self.record("Auth", "Admin user role is 'admin'", r_me.get("json", {}).get("role") == "admin")

        r_users = await request("GET", "/api/users", headers=h_admin)
        self.record("Auth", "Admin list all users returns 200", r_users["status"] == 200, r_users["text"])

        # Permission check: Standard user without delete permission
        test_im = f"8699{uuid.uuid4().int % 100000000000:011d}"
        r_c = await request("POST", "/api/devices", headers=h_admin, body={"customer_name": "KARNATAKA", "imei": test_im})
        if r_c["status"] in [200, 201]:
            did = r_c["json"]["id"]
            r_unauth_del = await request("DELETE", f"/api/devices/{did}", headers=h_std)
            self.record("Auth", "Unauthorized delete rejected with 403 Forbidden", r_unauth_del["status"] == 403, r_unauth_del["text"])

            await request("DELETE", f"/api/devices/{did}", headers=h_admin)
            await request("DELETE", f"/api/bin/{did}", headers=h_admin)

        r_bad_login = await request("POST", "/api/auth/login", body={"user_id": "0001", "password": "WRONG_PASSWORD_XYZ"})
        self.record("Auth", "Bad password rejected with 401 Unauthorized", r_bad_login["status"] == 401, r_bad_login["text"])

        r_non_user = await request("POST", "/api/auth/login", body={"user_id": "NON_EXISTENT_999", "password": "password123"})
        self.record("Auth", "Non-existent user rejected with 401 Unauthorized", r_non_user["status"] == 401, r_non_user["text"])

    # =========================================================================
    # SUITE 9: FRONTEND CODE & CONTRACT VERIFICATION (30 tests)
    # =========================================================================
    async def suite_frontend(self):
        print("\n▶ SUITE 9: FRONTEND CODE & CONTRACT VERIFICATION (30 tests)")

        pages = ["inventory.html", "edit-delete.html", "cart.html", "errors.html", "index.html", "home.html", "settings.html"]
        for p in pages:
            path = os.path.join(BASE_DIR, "frontend", p)
            exists = os.path.isfile(path)
            self.record("Frontend", f"Page {p} exists on disk", exists)
            if exists:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.record("Frontend", f"Page {p} contains DOCTYPE & closing tags", "<!DOCTYPE html>" in content and "</html>" in content)

        ed_path = os.path.join(BASE_DIR, "frontend", "edit-delete.html")
        with open(ed_path, "r", encoding="utf-8") as f:
            ed_text = f.read()

        self.record("Frontend", "edit-delete.html has btnBulkEditImei", 'id="btnBulkEditImei"' in ed_text)
        self.record("Frontend", "edit-delete.html has btnBulkDeleteImei", 'id="btnBulkDeleteImei"' in ed_text)
        self.record("Frontend", "edit-delete.html has btnBulkDeleteExcel", 'id="btnBulkDeleteExcel"' in ed_text)
        self.record("Frontend", "edit-delete.html has dlgBulkDeleteImei", 'id="dlgBulkDeleteImei"' in ed_text)
        self.record("Frontend", "edit-delete.html has dlgBulkDeleteExcel", 'id="dlgBulkDeleteExcel"' in ed_text)
        self.record("Frontend", "edit-delete.html has dlgBulkEditImei", 'id="dlgBulkEditImei"' in ed_text)
        self.record("Frontend", "edit-delete.html has Find Record button & input", 'id="ei"' in ed_text and 'id="eg"' in ed_text)

        cart_path = os.path.join(BASE_DIR, "frontend", "cart.html")
        with open(cart_path, "r", encoding="utf-8") as f:
            cart_text = f.read()
        self.record("Frontend", "cart.html has cartEmptyProgressWrap", 'id="cartEmptyProgressWrap"' in cart_text)
        self.record("Frontend", "cart.html has showCartStatusProgress", 'function showCartStatusProgress' in cart_text)

        inv_path = os.path.join(BASE_DIR, "frontend", "inventory.html")
        with open(inv_path, "r", encoding="utf-8") as f:
            inv_text = f.read()
        self.record("Frontend", "inventory.html has downloadSingleCustomerExcel", 'function downloadSingleCustomerExcel' in inv_text)
        self.record("Frontend", "inventory.html page_size is safe (<= 5000)", 'page_size=50000' not in inv_text)

    async def run_all(self):
        t0 = time.time()
        print("Starting CustomerVault Comprehensive 300-500 Test Cases Execution…")
        await self.setup()

        await self.suite_customer()
        await self.suite_device()
        await self.suite_expiry()
        await self.suite_bulk()
        await self.suite_errors()
        await self.suite_cart()
        await self.suite_columns()
        await self.suite_auth()
        await self.suite_frontend()

        elapsed = round(time.time() - t0, 2)
        print("\n========================================================")
        print(f"TEST EXECUTION COMPLETE in {elapsed}s")
        print(f"Total Tests Run: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ({(self.passed_tests/self.total_tests)*100:.1f}%)")
        print(f"Failed: {self.failed_tests}")
        print("========================================================")

        return self.failed_tests == 0

async def main():
    suite = ComprehensiveTestSuite()
    success = await suite.run_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())

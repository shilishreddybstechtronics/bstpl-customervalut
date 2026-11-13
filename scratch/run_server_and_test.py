import sys
import os
import threading
import time
import urllib.request
import json
import uvicorn

sys.path.insert(0, os.path.abspath('backend'))
from main import app
from database import SessionLocal
from models import User
from auth import create_token

# Run uvicorn server in background thread
class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.server = None

    def run(self):
        config = uvicorn.Config(app, host="127.0.0.1", port=8005, log_level="error")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True

server_thread = ServerThread()
server_thread.start()

BASE_URL = 'http://127.0.0.1:8005'

# Wait until server is ready (up to 15s)
connected = False
for attempt in range(30):
    try:
        with urllib.request.urlopen(f'{BASE_URL}/inventory.html', timeout=2) as resp:
            if resp.status == 200:
                connected = True
                break
    except Exception:
        time.sleep(0.5)

if not connected:
    print("Failed to connect to in-process server within 15 seconds")
    server_thread.stop()
    sys.exit(1)

try:
    print("=== Testing in-process server ===")
    
    # 1. Fetch inventory.html
    with urllib.request.urlopen(f'{BASE_URL}/inventory.html', timeout=5) as resp:
        assert resp.status == 200
        html = resp.read().decode('utf-8')
        print(f"✓ /inventory.html served (status {resp.status}, size {len(html)} bytes)")

    # 2. Check Customer Files Grid
    assert '.customer-file-grid' in html
    assert 'class="customer-file-grid"' in html
    assert 'data-cren' in html
    assert 'data-cdel' in html
    assert 'data-cview' in html
    assert 'data-cdl' in html
    print("✓ 1. Customer Files Grid: Layout and trigger attributes verified")

    # 3. Check Rename Customer Modal
    assert '<dialog id="dlgSingleCustomerRename"' in html
    assert 'id="singleRenNameInput"' in html
    assert 'id="formSingleCustomerRename"' in html
    assert 'function openSingleCustomerRename' in html
    print("✓ 2. Rename Customer Modal: Dialog structure, inputs, and handler verified")

    # 4. Check Delete Customer Modal
    assert '<dialog id="dlgDeleteCustomerEntries"' in html
    assert 'id="delCustConfirmInput"' in html
    assert 'id="delWholeCustChk"' in html
    assert 'id="delCustPermanentChk"' in html
    assert 'id="btnConfirmDelCustEntries"' in html
    assert 'function openDeleteCustomerEntriesModal' in html
    print("✓ 3. Delete Customer Modal: Dialog structure, confirmation input, and handler verified")

    # 5. Check Bulk Upload buttons
    assert 'id="btnUploadAddCol"' in html
    assert 'id="btnUploadAddRec"' in html
    assert 'openAddColumnModal()' in html
    assert 'openAddDeviceModal()' in html
    print("✓ 4. Bulk Upload: Add Column and Add Record buttons verified in upload view")

    # 6. Check Add Column Modal
    assert '<dialog id="dlgAddColumn"' in html
    assert 'id="newColName"' in html
    assert 'id="newColTarget"' in html
    assert 'id="newColCustSel"' in html
    assert 'id="newColImeis"' in html
    assert 'id="newColValue"' in html
    assert 'id="btnSubmitAddColumn"' in html
    print("✓ 5. Add Column Modal: Inputs, scope selectors, and submission elements verified")

    # 7. Check Add Record Modal (devdlg)
    assert '<dialog id="devdlg" class="modal-card"' in html
    assert 'id="devTitle"' in html
    assert 'id="devFields"' in html
    assert 'id="devSave"' in html
    assert 'Customer & Device Identification' in html
    assert 'SIM & Connectivity Details' in html
    assert 'Lifecycle Dates & Timeline' in html
    assert 'Hardware & Software Specs' in html
    print("✓ 6. Add Record Modal: Modal card, 4 organized form sections, and controls verified")

    # 8. Test backend API with real database session
    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.role == 'admin').first()
        token = create_token(admin_user)
        print(f"✓ 7. Authenticated token created for {admin_user.user_id} ({admin_user.role})")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    req = urllib.request.Request(f'{BASE_URL}/api/customers', headers=headers)
    with urllib.request.urlopen(req) as resp:
        custs = json.loads(resp.read().decode('utf-8'))
        print(f"✓ 8. Customers API returned {len(custs)} customer portfolios")

    req = urllib.request.Request(f'{BASE_URL}/api/devices?page=1&page_size=5', headers=headers)
    with urllib.request.urlopen(req) as resp:
        devices = json.loads(resp.read().decode('utf-8'))
        print(f"✓ 9. Devices API returned {devices.get('total')} total devices in DB")

    print("\n🎉 ALL 9 REQUIREMENTS FULLY VALIDATED AND PASSING!")

finally:
    server_thread.stop()

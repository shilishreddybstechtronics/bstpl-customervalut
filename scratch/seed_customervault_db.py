import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, 'backend')
import sqlite3
from auth import hash_password

db_path = os.path.abspath('backend/customervault.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Ensure all tables exist
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    user_id VARCHAR(30) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plain_password VARCHAR(255),
    is_admin BOOLEAN DEFAULT 0,
    role VARCHAR(10) DEFAULT 'limited',
    permissions JSON,
    token_version INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

c.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) UNIQUE NOT NULL,
    avatar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    deleted_by VARCHAR(30)
)""")

c.execute("""
CREATE TABLE IF NOT EXISTS sim_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    device_sr_no VARCHAR(50),
    imei VARCHAR(20) UNIQUE NOT NULL,
    iccid VARCHAR(30),
    msisdn1 VARCHAR(20),
    msisdn2 VARCHAR(20),
    act_date DATE,
    expiry_date DATE,
    dispatched_date DATE,
    model VARCHAR(100),
    sim_provider VARCHAR(100),
    activation_plan VARCHAR(100),
    firmware VARCHAR(100),
    flash VARCHAR(100),
    sim_type VARCHAR(20),
    added_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    deleted_by VARCHAR(30),
    delete_reason VARCHAR(200),
    extra JSON
)""")

c.execute("""
CREATE TABLE IF NOT EXISTS sim_column_registry (
    name VARCHAR(100) PRIMARY KEY
)""")

c.execute("""
CREATE TABLE IF NOT EXISTS sim_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_login VARCHAR(30) DEFAULT '',
    user_name VARCHAR(100) DEFAULT '',
    action VARCHAR(30) NOT NULL,
    detail VARCHAR(500) DEFAULT '',
    ip VARCHAR(45) DEFAULT '',
    created_at DATETIME NOT NULL
)""")

c.execute("""
CREATE TABLE IF NOT EXISTS sim_errored_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(150),
    imei VARCHAR(100),
    device_sr_no VARCHAR(100),
    iccid VARCHAR(100),
    msisdn1 VARCHAR(100),
    msisdn2 VARCHAR(100),
    act_date DATE,
    expiry_date DATE,
    dispatched_date DATE,
    model VARCHAR(150),
    sim_provider VARCHAR(150),
    activation_plan VARCHAR(150),
    firmware VARCHAR(150),
    flash VARCHAR(150),
    sim_type VARCHAR(100),
    extra JSON,
    error_reason VARCHAR(500) DEFAULT 'Invalid entry',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

# 2. Seed Users if not present
users = c.execute("SELECT count(*) FROM users").fetchone()[0]
if users == 0:
    c.execute("""
    INSERT INTO users (name, user_id, password_hash, plain_password, is_admin, role)
    VALUES ('Shilish Reddy', '0001', ?, 'Admin@123', 1, 'admin')
    """, (hash_password('Admin@123'),))

# 3. Seed Customers if not present
cust_count = c.execute("SELECT count(*) FROM customers").fetchone()[0]
if cust_count == 0:
    customers_data = [
        ("Alpha Logistics Ltd", "🚚"),
        ("Apex Fleet Solutions", "🚛"),
        ("Swift Telematics Corp", "🛰️"),
        ("TransIndia Freight Lines", "📦"),
        ("BlueDart Global Cargo", "✈️"),
        ("OmniTrack Fleet Systems", "🌐"),
        ("Metro Fleet Services", "🚖"),
        ("Zenith Transport Hub", "🏢"),
        ("Pioneer Cargo Movers", "⚓"),
        ("Prime Logistics India", "⚡")
    ]
    for name, icon in customers_data:
        c.execute("INSERT OR IGNORE INTO customers (name, avatar) VALUES (?, ?)", (name, icon))

# 4. Seed Devices if not present
dev_count = c.execute("SELECT count(*) FROM sim_devices").fetchone()[0]
today = date.today()
if dev_count == 0:
    sample_devices = [
        (1, "SR-1001", "863481029384712", "8991001234567890123", "9845012345", "9845012346", today - timedelta(days=200), today + timedelta(days=165), today - timedelta(days=190), "TK103", "Airtel", "Annual Fleet 4G", "v2.1.0", "16MB", "E-SIM"),
        (1, "SR-1002", "863481029384713", "8991001234567890124", "9845012347", "", today - timedelta(days=180), today + timedelta(days=185), today - timedelta(days=175), "GT06N", "Vodafone", "Enterprise Connect", "v1.4.2", "8MB", "Plastic SIM"),
        (2, "SR-2001", "863481029384714", "8991001234567890125", "9845023456", "9845023457", today - timedelta(days=380), today - timedelta(days=15), today - timedelta(days=370), "Concox GT06", "Jio", "Standard GPS", "v3.0.1", "32MB", "E-SIM"),
        (2, "SR-2002", "863481029384715", "8991001234567890126", "9845023458", "", today - timedelta(days=350), today + timedelta(days=15), today - timedelta(days=340), "Teltonika FMB920", "Airtel", "Fleet Pro 10GB", "v4.0.0", "16MB", "Plastic SIM"),
        (3, "SR-3001", "863481029384716", "8991001234567890127", "9845034567", "9845034568", today - timedelta(days=120), today + timedelta(days=245), today - timedelta(days=110), "TK103B", "BSNL", "National M2M", "v2.2.0", "16MB", "E-SIM"),
        (3, "SR-3002", "863481029384717", "8991001234567890128", "9845034569", "", today - timedelta(days=365), today - timedelta(days=5), today - timedelta(days=355), "GT06", "Vodafone", "Basic Tracking", "v1.3.0", "8MB", "Plastic SIM"),
        (4, "SR-4001", "863481029384718", "8991001234567890129", "9845045678", "9845045679", today - timedelta(days=345), today + timedelta(days=20), today - timedelta(days=335), "Teltonika FMB120", "Airtel", "Heavy Fleet 4G", "v4.2.1", "32MB", "E-SIM"),
        (5, "SR-5001", "863481029384719", "8991001234567890130", "9845056789", "", today - timedelta(days=90), today + timedelta(days=275), today - timedelta(days=80), "Concox AT4", "Jio", "Asset Tracker 2Y", "v1.1.0", "16MB", "Plastic SIM"),
        (6, "SR-6001", "863481029384720", "8991001234567890131", "9845067890", "9845067891", today - timedelta(days=400), today - timedelta(days=35), today - timedelta(days=390), "TK103", "Airtel", "Legacy Track", "v2.0.0", "8MB", "E-SIM"),
        (7, "SR-7001", "863481029384721", "8991001234567890132", "9845078901", "", today - timedelta(days=360), today + timedelta(days=5), today - timedelta(days=350), "GT06N", "Vodafone", "Express Courier", "v1.5.0", "16MB", "Plastic SIM")
    ]
    for d in sample_devices:
        c.execute("""
        INSERT INTO sim_devices (
            customer_id, device_sr_no, imei, iccid, msisdn1, msisdn2,
            act_date, expiry_date, dispatched_date, model, sim_provider,
            activation_plan, firmware, flash, sim_type, added_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, d)

# 5. Seed Activity Logs if not present
act_count = c.execute("SELECT count(*) FROM sim_activity_log").fetchone()[0]
if act_count == 0:
    sample_activities = [
        (1, "0001", "Shilish Reddy", "login", "Signed into Admin Console", "127.0.0.1", datetime.now() - timedelta(minutes=10)),
        (1, "0001", "Shilish Reddy", "device_add", "Registered IMEI 863481029384712 (Alpha Logistics)", "127.0.0.1", datetime.now() - timedelta(minutes=8)),
        (1, "0001", "Shilish Reddy", "device_upload", "Uploaded batch of 10 device telemetry records", "127.0.0.1", datetime.now() - timedelta(minutes=5)),
        (1, "0001", "Shilish Reddy", "customer_add", "Created customer account 'Alpha Logistics Ltd'", "127.0.0.1", datetime.now() - timedelta(minutes=3))
    ]
    for a in sample_activities:
        c.execute("""
        INSERT INTO sim_activity_log (user_id, user_login, user_name, action, detail, ip, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, a)

# 6. Seed Errored Records if not present
err_count = c.execute("SELECT count(*) FROM sim_errored_records").fetchone()[0]
if err_count == 0:
    sample_errors = [
        ("Alpha Logistics", "8634810293", "SR-ERR-01", "89910012345", "9845099991", "", today, today + timedelta(days=365), today, "TK103", "Airtel", "Standard", "v1.0", "8MB", "E-SIM", "Invalid IMEI Length (10 digits, expected 15)"),
        ("Swift Telematics", "863481029384712", "SR-ERR-02", "89910012346", "9845099992", "", today, today + timedelta(days=365), today, "GT06N", "Vodafone", "Fleet 4G", "v1.2", "16MB", "Plastic SIM", "Duplicate IMEI already exists in database"),
        ("Apex Fleet", "863481029384799", "SR-ERR-03", "89910012347", "", "", today, today - timedelta(days=10), today, "Teltonika", "Jio", "Basic", "v2.0", "16MB", "E-SIM", "Expiry date occurs before activation date")
    ]
    for e in sample_errors:
        c.execute("""
        INSERT INTO sim_errored_records (
            customer_name, imei, device_sr_no, iccid, msisdn1, msisdn2,
            act_date, expiry_date, dispatched_date, model, sim_provider,
            activation_plan, firmware, flash, sim_type, error_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, e)

conn.commit()
conn.close()

print("customervault.db seeded and verified successfully!")


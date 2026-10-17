"""config.py - settings for CustomerVault.

The MySQL password does NOT belong in this file. Put it in ONE of these places:
  1. environment variables  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
  2. a file named config_local.py next to this one (never share or commit it)
Values in config_local.py override the defaults below; environment variables override both.
"""
import os

# Safe defaults only - NO password here. Your real login goes in config_local.py (see above).
MYSQL = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    # The database YOU created. Must match the name in MySQL exactly
    # (if it really contains a space, write "customer database").
    "database": "customer_database",
}

# False = use the existing database only (a wrong name gives an error that lists the real names,
#         instead of silently creating a new empty database).
AUTO_CREATE_DATABASE = False

# SYSTEM TABLES - created automatically by the app when it starts (you never list them below):
#   customers  - customer list (id <-> table name)      employees - employee logins
#   sessions   - logged-in sessions                      devices   - old combined records (kept, no longer read)
#   column_registry, app_state, activity_log - the column list, internal settings, the Login Inventory

# CUSTOMER TABLES - one MySQL table per customer; the table name IS the customer name.
#   * Any name in this list that has NO table in MySQL gets its table created when the app starts
#     (create only - nothing is ever renamed or deleted from here).
#   * The list is rewritten automatically from MySQL after every add / rename / delete / import, so a customer
#     deleted on the website does not come back.
#   * Set CREATE_MISSING_CUSTOMER_TABLES = False to stop tables being created from this list
#     (needed if you drop a table directly in MySQL while the app is stopped and want it to stay gone).
CREATE_MISSING_CUSTOMER_TABLES = True

DEFAULT_CUSTOMERS = [
    "simple track",
    "way4track(sharon)",
    "lambda",
    "sridhar reddy (karnataka)",
    "sridhar reddy(locker)",
    "track wheels",
    "vahan point",
    "rarthvik",
    "bujji",
    "smart wheel",
    "glorious technologies",
    "glovision",
    "algomatrix",
    "sumit electronics",
    "lets track",
    "vamo",
    "balkhi",
    "chandrapur",
    "shri ram tyres",
    "karnataka",
    "purview technical pvt ltd",
    "hm_tech",
    "sridhar reddy chennai",
    "hi-tech robotics",
    "cosmica",
    "vinay mule",
    "global logistics",
    "secure things",
    "dsm soft",
    "fuel track",
    "famous enterprises",
    "ts auto solutions",
    "masstrans",
    "tgg",
    "tgg vltd",
    "abhishek reddy",
    "delhi testing",
    "vikas sharma(jammu)",
    "via plus",
    "eubix technologies",
    "gemeni enterprises",
    "vk tracking",
    "royal computers",
    "rk services",
    "boston",
    "bay iot",
    "aargee",
    "amk khohli",
    "gujarat",
    "vishnu honda",
    "trak 24",
    "ma mahankhali motors",
    "olectra",
    "prime badge",
    "gamyam",
    "demo",
    "lead max",
    "spark minda",
    "prasad",
    "gandhi",
    "shaurya",
    "v group",
    "anil -shakthi",
    "royal _gas",
    "samad ali",
    "theaauto",
    "vasanth",
    "ashok reddy",
    "vv lakshman rao",
    "prime edge solutions",
    "ashok reddy(dhone)",
    "cn enterprises",
    "jairam",
    "tecdatum",
    "sushil",
    "fleet-x",
    "iteration tech",
    "babji",
    "maruti",
    "apsac",
    "vltd",
    "mh-mining",
    "rto-chennai",
    "goa",
    "chennai",
    "maharashtra",
    "leadmax(acs)",
    "iobot",
    "machine max",
    "rede technologies",
    "ind track(sysnet)",
    "j-technologies",
    "calon",
    "pixcell",
    "hey ev-delovita",
    "jio",
    "jsipl",
    "others",
    "mining",
    "gps-gujarath",
    "sv-enterprises",
    "led geo",
    "itg",
    "autoguard",
    "ccr technology",
    "gps wala",
    "water boards",
]

# ACCESS LEVELS - decided ONLY by Employee ID (a name can never grant a role).
#   "admin"    : everything - Cart, Login Inventory, deleting customers, Manage Users (add / remove members).
#   "standard" : everything EXCEPT Login Inventory, Cart and deleting customers (no Manage Users either).
#   "limited"  : only view / fetch / search / download customer data, insert (add) records and edit a record's details.
#                No renaming, no deleting, no Cart, no Login Inventory, no new columns, no SIM Data Upload.
# A member ADDED BY AN ADMIN (Manage Users > Add Member) is always an admin - that is stored in MySQL and wins over this list.
# Every other ID (people who register themselves later) gets DEFAULT_ROLE = "limited".
# Admin IDs can NOT be self-registered on the website (anyone could grab them) - create them with:  python add_user.py
ROLES = {
    "0001": "admin", "0002": "admin", "0003": "admin", "1234": "admin",
    "0004": "standard", "0005": "standard", "0006": "standard",
    "0007": "standard", "0008": "standard", "0009": "standard",
    "0010": "limited",      # fetch / insert / edit data only (no customer rename, no delete, no Cart, no Login Inventory)
}
DEFAULT_ROLE = "limited"

# Empty columns (no value in any customer table) are dropped automatically; Device Sr No, IMEI and ICCID and any column with data are kept.
#   "once" = on the first start only   |   "always" = on every start   |   "off" = never
PRUNE_EMPTY_COLUMNS = "once"


# ---------------------------------------------------------------- local overrides + environment (keep at the bottom)
try:
    import config_local
    MYSQL.update(getattr(config_local, "MYSQL", {}))
except ImportError:
    pass

for _key, _env in (("host", "MYSQL_HOST"), ("port", "MYSQL_PORT"), ("user", "MYSQL_USER"),
                   ("password", "MYSQL_PASSWORD"), ("database", "MYSQL_DATABASE")):
    if os.environ.get(_env, "").strip():
        MYSQL[_key] = os.environ[_env].strip()
# One-line alternative: set MYSQL_URL (or DATABASE_URL) = mysql://user:password@host:port/database
# Most cloud MySQL providers show exactly this "connection string" - paste it as one Render variable.
_url = (os.environ.get("MYSQL_URL") or os.environ.get("DATABASE_URL") or "").strip()
if _url.startswith(("mysql://", "mysql+pymysql://", "mariadb://")):
    from urllib.parse import unquote, urlparse
    _u = urlparse(_url)
    for _k, _v in (("host", _u.hostname), ("port", _u.port), ("user", unquote(_u.username or "")),
                   ("password", unquote(_u.password or "")), ("database", (_u.path or "").lstrip("/"))):
        if _v:
            MYSQL[_k] = _v
MYSQL["port"] = int(MYSQL["port"])

# On Render, set MYSQL_AUTO_CREATE=true to create the database if it does not exist yet.
if os.environ.get("MYSQL_AUTO_CREATE", "").lower() in ("1", "true", "yes"):
    AUTO_CREATE_DATABASE = True

"""config_local.py - YOUR secrets. Keep this file private (do not share it, do not commit it to git).
Only list what differs from config.py. Environment variables (MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_SSL) override this file."""

MYSQL = {
    "host": "mysql-28f91b17-shilish-0a63.g.aivencloud.com",
    "port": 24605,
    "user": "avnadmin",
    "password": "AVNS_a4tE3QJm5FRj6E2_Qw0",
    "database": "defaultdb",   # or "defaultdb" if your tables are there
    "ssl": True,
}

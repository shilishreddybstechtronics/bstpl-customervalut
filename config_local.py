"""config_local.py - YOUR secrets. Keep this file private (do not share it, do not commit it to git).
Only list what differs from config.py. Environment variables (MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
MYSQL_PASSWORD, MYSQL_DATABASE) override this file."""

MYSQL = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "customer_database",   # exact name as shown in MySQL Workbench
}

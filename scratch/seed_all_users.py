import sys
sys.path.insert(0, 'backend')
import sqlite3
from auth import hash_password, role_for_id

conn = sqlite3.connect('backend/customervault.db')
c = conn.cursor()

# Ensure table exists
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80) NOT NULL,
    user_id VARCHAR(30) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    plain_password VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'limited',
    token_version INTEGER DEFAULT 0,
    permissions JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

seed_users = [
    ("0001", "Shilish Reddy", "Admin@123", "admin"),
    ("0007", "Super Admin 0007", "Admin@0007", "admin"),
    ("0002", "Master Admin 0002", "Admin@0002", "admin"),
    ("0003", "Master Admin 0003", "Admin@0003", "admin"),
    ("0004", "Master Admin 0004", "Admin@0004", "admin"),
    ("0005", "Admin User 0005", "Admin@0005", "admin"),
    ("0006", "Admin User 0006", "Admin@0006", "admin"),
    ("0008", "Admin User 0008", "Admin@0008", "admin"),
    ("0009", "Admin User 0009", "Admin@0009", "admin"),
    ("0010", "Admin User 0010", "Admin@0010", "admin"),
    ("0011", "Regular User 0011", "User@0011", "limited"),
    ("0012", "Regular User 0012", "User@0012", "limited")
]

for uid, name, pwd, default_role in seed_users:
    role = role_for_id(uid)
    is_admin = 1 if role == 'admin' else 0
    h = hash_password(pwd)
    row = c.execute("SELECT id FROM users WHERE user_id = ?", (uid,)).fetchone()
    if not row:
        c.execute("""
            INSERT INTO users (name, user_id, password_hash, plain_password, is_admin, role, token_version)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (name, uid, h, pwd, is_admin, role))
        print(f"Seeded user {uid} ({name}) with role {role} and password {pwd}")
    else:
        c.execute("""
            UPDATE users SET password_hash = ?, plain_password = ?, is_admin = ?, role = ?
            WHERE user_id = ?
        """, (h, pwd, is_admin, role, uid))
        print(f"Updated user {uid} ({name}) with role {role} and password {pwd}")

conn.commit()
print("All users seeded/updated successfully in backend/customervault.db!")


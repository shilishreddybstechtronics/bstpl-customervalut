-- Run once in the TiDB Cloud SQL Editor (USE customer_database; first).
-- If a line says "Duplicate column name", that column already exists: skip that line.

ALTER TABLE users   ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE devices ADD COLUMN extra JSON NULL;

CREATE TABLE IF NOT EXISTS column_registry (name VARCHAR(100) PRIMARY KEY);

-- Make yourself the admin (replace with YOUR login ID):
UPDATE users SET is_admin = TRUE WHERE user_id = 'your_login_id';

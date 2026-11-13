-- WARNING: this file deletes the users table (DROP TABLE below). Do NOT run it again on a live database.
-- To add the new features, run migration_features.sql instead.

-- Run in the TiDB Cloud SQL Editor (or MySQL Workbench).
CREATE DATABASE IF NOT EXISTS customer_database;
USE customer_database;

-- The login now uses an ID instead of an email, so the old table must be replaced:
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    user_id VARCHAR(30) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

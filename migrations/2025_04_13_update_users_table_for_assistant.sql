-- Migration: Allow 'Assistant' role in users table

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

-- Rename the old users table
ALTER TABLE users RENAME TO users_old;

-- Create the new users table with the updated CHECK constraint
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Doctor', 'Receptionist', 'Assistant'))
);

-- Copy data from the old table to the new table
INSERT INTO users (user_id, username, password_hash, role)
SELECT user_id, username, password_hash, role FROM users_old;

-- Drop the old table
DROP TABLE users_old;

COMMIT;

PRAGMA foreign_keys=on;
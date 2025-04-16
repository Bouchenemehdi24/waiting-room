-- Migration: Update user roles to Admin, Doctor, Assistant and migrate Receptionist to Admin

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

-- Step 1: Rename the existing users table
ALTER TABLE users RENAME TO users_old_roles;

-- Step 2: Create the new users table with the updated CHECK constraint
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Admin', 'Doctor', 'Assistant')) -- Updated roles
);

-- Step 3: Copy data, mapping 'Receptionist' to 'Admin'
INSERT INTO users (user_id, username, password_hash, role)
SELECT
    user_id,
    username,
    password_hash,
    CASE
        WHEN role = 'Receptionist' THEN 'Admin' -- Map Receptionist to Admin
        ELSE role
    END
FROM users_old_roles;

-- Step 4: Drop the old table
DROP TABLE users_old_roles;

COMMIT;

PRAGMA foreign_keys=on;

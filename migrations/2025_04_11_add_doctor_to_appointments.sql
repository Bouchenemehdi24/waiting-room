-- Migration: Add doctor_id and notification fields to appointments table

ALTER TABLE appointments
ADD COLUMN doctor_id INTEGER REFERENCES users(user_id);

-- Optionally, add notification_sent and appointment_type fields
ALTER TABLE appointments
ADD COLUMN notification_sent INTEGER DEFAULT 0;

ALTER TABLE appointments
ADD COLUMN appointment_type TEXT;

-- If you want to add duration (in minutes)
ALTER TABLE appointments
ADD COLUMN duration INTEGER;

-- Update existing rows as needed (optional)
-- UPDATE appointments SET doctor_id = (SELECT user_id FROM users WHERE role='Doctor' LIMIT 1) WHERE doctor_id IS NULL;
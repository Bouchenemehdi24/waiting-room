import sqlite3

def migrate():
    conn = sqlite3.connect("medical_office.db")
    cursor = conn.cursor()
    # Add doctor_id column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN doctor_id INTEGER REFERENCES users(user_id);")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print("Error adding doctor_id:", e)
    # Add notification_sent column
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN notification_sent INTEGER DEFAULT 0;")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print("Error adding notification_sent:", e)
    # Add appointment_type column
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN appointment_type TEXT;")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print("Error adding appointment_type:", e)
    # Add duration column
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN duration INTEGER;")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print("Error adding duration:", e)
    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
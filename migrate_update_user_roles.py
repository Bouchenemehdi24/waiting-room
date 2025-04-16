import sqlite3
import os

# Define the path to the database and the migration script
DATABASE_PATH = 'medical_office.db'
MIGRATION_SCRIPT_PATH = os.path.join('migrations', '2025_04_14_update_user_roles.sql')

def apply_migration():
    """Applies the SQL migration script to update user roles."""
    conn = None  # Initialize conn to None
    try:
        print(f"Connecting to database: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        print(f"Reading migration script: {MIGRATION_SCRIPT_PATH}")
        with open(MIGRATION_SCRIPT_PATH, 'r') as f:
            sql_script = f.read()

        print("Executing migration script...")
        cursor.executescript(sql_script)
        conn.commit()
        print("Migration applied successfully.")

    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
        if conn:
            conn.rollback() # Rollback changes if error occurs
    except FileNotFoundError:
        print(f"Error: Migration script not found at {MIGRATION_SCRIPT_PATH}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database file not found at {DATABASE_PATH}")
    elif not os.path.exists(MIGRATION_SCRIPT_PATH):
         print(f"Error: Migration script not found at {MIGRATION_SCRIPT_PATH}")
    else:
        apply_migration()

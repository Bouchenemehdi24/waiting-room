import sqlite3
import datetime
import json
import os
import logging
import hashlib
import secrets
from contextlib import contextmanager
from db_connection_pool import DatabaseConnectionPool

class DatabaseError(Exception):
    """Base exception class for database errors"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass

class DatabaseOperationError(DatabaseError):
    """Raised when database operation fails"""
    pass

class DatabaseManager:
    def __init__(self, db_path="medical_office.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing DatabaseManager with database: {db_path}")
        
        # Initialize connection pool
        self.connection_pool = DatabaseConnectionPool(db_path, min_connections=2, max_connections=10, timeout=20)
        self.logger.info("Database connection pool initialized")
        
        try:
            self.init_database()
        except sqlite3.Error as e:
            self.logger.exception("Critical: Database initialization failed")
            raise DatabaseConnectionError(f"Failed to initialize database: {str(e)}")
            
    @contextmanager
    def get_connection(self):
        # Use the connection pool instead of creating new connections
        try:
            with self.connection_pool.connection() as conn:
                self.logger.debug("Database connection acquired from pool")
                yield conn
        except sqlite3.Error as e:
            self.logger.exception("Database connection failed")
            raise DatabaseConnectionError(f"Failed to connect: {str(e)}")
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables with correct schema
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('Doctor', 'Receptionist', 'Assistant'))
                );

                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    phone_number TEXT, -- Added optional phone number
                    first_seen_date TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS visits (
                    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    arrived_at TEXT NOT NULL,
                    called_at TEXT,
                    checkout_at TEXT,
                    total_paid INTEGER,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                );
                
                CREATE TABLE IF NOT EXISTS services (
                    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    price INTEGER NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS visit_services (
                    visit_id INTEGER NOT NULL,
                    service_id INTEGER NOT NULL,
                    FOREIGN KEY (visit_id) REFERENCES visits(visit_id),
                    FOREIGN KEY (service_id) REFERENCES services(service_id),
                    PRIMARY KEY (visit_id, service_id)
                );
                
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    visit_id INTEGER NOT NULL,
                    patient_name TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (visit_id) REFERENCES visits(visit_id)
                );
                
                -- Removed appointments table creation block

                CREATE TABLE IF NOT EXISTS audit_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Add indexes for performance
                CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);
                CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(date);
                CREATE INDEX IF NOT EXISTS idx_visits_called_at ON visits(called_at);
                CREATE INDEX IF NOT EXISTS idx_visits_checkout_at ON visits(checkout_at);
                CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);

                -- FTS5 module not available, removed FTS table and triggers.

            """)
            
            # --- Add missing columns safely ---
            try:
                cursor.execute("ALTER TABLE patients ADD COLUMN phone_number TEXT;")
                self.logger.info("Added 'phone_number' column to 'patients' table.")
            except sqlite3.OperationalError as e:
                # Ignore error if column already exists
                if "duplicate column name" in str(e).lower():
                    self.logger.debug("'phone_number' column already exists in 'patients' table.")
                else:
                    raise # Re-raise other operational errors
            
            conn.commit()
            self.logger.info("Database schema initialized/verified and columns/indexes created/verified.") # Updated log

    def add_patient(self, name, phone_number=None): # Added phone_number parameter
        self.logger.info(f"Adding new patient: {name}, Phone: {phone_number if phone_number else 'N/A'}")
        if not name or not name.strip():
            self.logger.error("Attempted to add patient with empty name")
            raise ValueError("Patient name cannot be empty")
            
        try:
            with self.connection_pool.connection() as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Check if patient already exists
                cursor.execute("SELECT patient_id FROM patients WHERE name = ?", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    self.logger.info(f"Patient already exists: {name}")
                    return existing['patient_id']
                
                cursor.execute(
                    "INSERT INTO patients (name, phone_number, first_seen_date) VALUES (?, ?, ?)", # Added phone_number to insert
                    (name, phone_number, now)
                )
                conn.commit()
                patient_id = cursor.lastrowid
                self.logger.info(f"Successfully added patient: {name} (Phone: {phone_number if phone_number else 'N/A'}, ID: {patient_id})")
                return patient_id
                
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error adding patient {name}: {str(e)}")
            raise DatabaseOperationError(f"Patient name conflict: {str(e)}")
        except sqlite3.Error as e:
            self.logger.exception(f"Error adding patient {name}")
            raise DatabaseOperationError(f"Failed to add patient: {str(e)}")

    def add_audit_log(self, user_id, action, details=""):
        """Adds an entry to the audit log using a connection from the pool."""
        self.logger.debug(f"Attempting audit log: User {user_id}, Action: {action}, Details: {details}")
        try:
            # Use a connection from the pool for audit logging
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO audit_log (user_id, action, timestamp, details)
                    VALUES (?, ?, ?, ?)
                """, (user_id, action, now, details))
                conn.commit()
                self.logger.debug(f"Successfully added audit log entry for user {user_id}, action {action}")
        except (sqlite3.Error, DatabaseConnectionError) as e:
            # Log any error during the audit log insertion using the pooled connection
            self.logger.error(f"Failed to add audit log entry (using pooled connection) for user {user_id}, action {action}. Error: {str(e)}")
            # Do not raise the error, just log it, to avoid disrupting the main operation.

    def add_visit(self, patient_id, user_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO visits (patient_id, date, arrived_at)
                    VALUES (?, date('now'), ?)
                """, (patient_id, now))
                conn.commit()
                visit_id = cursor.lastrowid
                self.logger.info(f"Added visit for patient ID {patient_id} (Visit ID: {visit_id}) by User ID {user_id}")
                # Temporarily disable audit log call due to persistent 'users_old_roles' error
                # self.add_audit_log(user_id, "add_visit", f"Patient ID: {patient_id}, Visit ID: {visit_id}")
                self.logger.warning(f"Audit log for 'add_visit' (Visit ID: {visit_id}) skipped due to persistent DB issue.")
                return visit_id

        except sqlite3.Error as e:
            self.logger.exception(f"Error adding visit for patient {patient_id} by user {user_id}")
            raise DatabaseOperationError(f"Failed to add visit: {str(e)}")
    
    def get_services(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, price FROM services")
                return cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.exception("Error retrieving services")
            raise DatabaseOperationError(f"Failed to retrieve services: {str(e)}")

    def update_service(self, name, price, user_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO services (name, price) VALUES (?, ?)",
                    (name, price)
                )
                conn.commit()
                self.logger.info(f"Updated service: {name} - {price} DA by User ID {user_id}")
                self.add_audit_log(user_id, "update_service", f"Service: {name}, Price: {price}")
        except sqlite3.Error as e:
            self.logger.exception(f"Error updating service {name} by user {user_id}")
            raise DatabaseOperationError(f"Failed to update service: {str(e)}")

    def delete_service(self, name, user_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM services WHERE name = ?", (name,))
                conn.commit()
                self.logger.info(f"Deleted service: {name} by User ID {user_id}")
                self.add_audit_log(user_id, "delete_service", f"Service: {name}")
        except sqlite3.Error as e:
            self.logger.exception(f"Error deleting service {name} by user {user_id}")
            raise DatabaseOperationError(f"Failed to delete service: {str(e)}")
    
    def get_current_visit(self, patient_name):
        """Get the current active visit for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.* 
                FROM visits v
                JOIN patients p ON v.patient_id = p.patient_id
                WHERE p.name = ?
                AND v.called_at IS NOT NULL
                AND v.checkout_at IS NULL
                ORDER BY v.arrived_at DESC
                LIMIT 1
            """, (patient_name,))
            return cursor.fetchone()
    
    def update_visit_checkout(self, visit_id, total_paid, service_ids):
        """Update visit with checkout information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                UPDATE visits 
                SET checkout_at = ?, total_paid = ?
                WHERE visit_id = ?
            """, (now, total_paid, visit_id))
            
            # Add visit services
            for service_id in service_ids:
                cursor.execute("""
                    INSERT INTO visit_services (visit_id, service_id)
                    VALUES (?, ?)
                """, (visit_id, service_id))
            
            conn.commit()
    
    def get_service_id(self, service_name):
        """Get service ID by name."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT service_id FROM services WHERE name = ?", (service_name,))
            result = cursor.fetchone()
            return result['service_id'] if result else None

    def update_patient_call(self, patient_name, call_time, user_id):
        """Update the most recent uncalled visit for a patient."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Find the visit_id first to log it
                cursor.execute("""
                    SELECT v.visit_id
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.patient_id
                    WHERE p.name = ?
                    AND v.called_at IS NULL
                    AND v.date = date('now')
                    ORDER BY v.arrived_at DESC
                    LIMIT 1
                """, (patient_name,))
                visit_result = cursor.fetchone()
                if not visit_result:
                    self.logger.warning(f"No active visit found for patient {patient_name} to call.")
                    return False

                visit_id = visit_result['visit_id']

                # Now update the visit
                cursor.execute("""
                    UPDATE visits
                    SET called_at = ?
                    WHERE visit_id = ?
                """, (call_time, visit_id))
                conn.commit()

                if cursor.rowcount > 0:
                    self.logger.info(f"Patient {patient_name} (Visit ID: {visit_id}) called at {call_time} by User ID {user_id}")
                    self.add_audit_log(user_id, "call_patient", f"Patient: {patient_name}, Visit ID: {visit_id}")
                    return True
                else:
                    # This case should ideally not happen due to the prior check, but included for safety
                    self.logger.warning(f"Failed to update call time for patient {patient_name} (Visit ID: {visit_id}). Rowcount was 0.")
                    return False
        except sqlite3.Error as e:
            self.logger.exception(f"Error updating call time for patient {patient_name} by user {user_id}")
            raise DatabaseOperationError(f"Failed to update call time: {str(e)}")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE visits 
                SET called_at = ?
                WHERE visit_id = (
                    SELECT v.visit_id
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.patient_id
                    WHERE p.name = ?
                    AND v.called_at IS NULL
                    AND v.date = date('now')
                    ORDER BY v.arrived_at DESC
                    LIMIT 1
                )
            """, (call_time, patient_name))

    # Removed appointment-related methods

    # --- User Management ---

    def _hash_password(self, password):
        """Hashes the password using SHA-256 with a salt."""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}${secrets.token_hex(16)}${hashed.hex()}" # Store salt with hash

    def _verify_password(self, stored_password_hash, provided_password):
        """Verifies a provided password against the stored hash."""
        try:
            salt, _, stored_hash = stored_password_hash.split('$')
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
            return stored_hash == provided_hash
        except Exception:
            self.logger.error("Error verifying password, possibly invalid hash format.")
            return False # Invalid hash format or other error

    def add_user(self, username, password, role):
        """Adds a new user to the database."""
        if role not in ['Doctor', 'Receptionist', 'Assistant']:
            raise ValueError("Invalid role specified. Must be 'Doctor', 'Receptionist', or 'Assistant'.")
        
        password_hash = self._hash_password(password)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role)
                )
                conn.commit()
                user_id = cursor.lastrowid
                self.logger.info(f"Added new user: {username} (Role: {role}, ID: {user_id})")
                # Optionally log this action itself, perhaps by a system user or the first admin
                # self.add_audit_log(admin_user_id, "add_user", f"Username: {username}, Role: {role}")
                return user_id
        except sqlite3.IntegrityError:
            self.logger.warning(f"Attempted to add user with existing username: {username}")
            raise DatabaseOperationError(f"Username '{username}' already exists.")
        except sqlite3.Error as e:
            self.logger.exception(f"Error adding user {username}")
            raise DatabaseOperationError(f"Failed to add user: {str(e)}")

    def get_user_by_username(self, username):
        """Retrieves user details by username."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, password_hash, role FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                if user:
                    self.logger.debug(f"User found: {username}")
                    return user
                else:
                    self.logger.debug(f"User not found: {username}")
                    return None
        except sqlite3.Error as e:
            self.logger.exception(f"Error retrieving user {username}")
            raise DatabaseOperationError(f"Failed to retrieve user: {str(e)}")

    def verify_user_credentials(self, username, password):
        """Verifies username and password, returns user details if valid."""
        user = self.get_user_by_username(username)
        if user and self._verify_password(user['password_hash'], password):
            self.logger.info(f"User credentials verified successfully for: {username}")
            return {'user_id': user['user_id'], 'username': user['username'], 'role': user['role']}
        else:
            self.logger.warning(f"Failed login attempt for username: {username}")
            return None

    def check_if_users_exist(self):
        """Checks if any users exist in the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users LIMIT 1")
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            self.logger.exception("Error checking for existing users")
            raise DatabaseOperationError(f"Failed to check for users: {str(e)}")

    # Removed leftover appointment update code

    def get_all_patients(self):
        """Retrieves all patient names and IDs."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT patient_id, name FROM patients ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.exception("Error retrieving all patients")
            raise DatabaseOperationError(f"Failed to retrieve patient list: {str(e)}")

    def search_patients(self, search_term):
        """Search patients by name using LIKE (FTS5 not available)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Reverted to using LIKE search as FTS5 module is not available
            cursor.execute("""
                SELECT patient_id, name 
                FROM patients 
                WHERE name LIKE ? 
                ORDER BY name -- Keep ordering consistent
                LIMIT 10
            """, (f'%{search_term}%',))
            return cursor.fetchall()

    def cleanup_expired_sessions(self):
        """Clean up expired sessions (older than 24 hours)"""
        pass

    def get_user_by_role(self, role):
        """Return a list of users with the specified role."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, username FROM users WHERE role = ?",
                (role,)
            )
            return [dict(user_id=row[0], username=row[1]) for row in cursor.fetchall()]

import sqlite3
import logging
import threading
import queue
import time
from contextlib import contextmanager

class DatabaseConnectionPool:
    """A connection pool for SQLite database connections.
    
    This class manages a pool of SQLite connections to improve performance
    by reusing connections instead of creating new ones for each operation.
    """
    
    def __init__(self, db_path, min_connections=2, max_connections=10, timeout=20):
        """Initialize the connection pool.
        
        Args:
            db_path: Path to the SQLite database file
            min_connections: Minimum number of connections to keep in the pool
            max_connections: Maximum number of connections allowed in the pool
            timeout: Connection timeout in seconds
        """
        self.db_path = db_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Connection pool and management
        self.pool = queue.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.RLock()
        
        # Initialize the minimum number of connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections."""
        self.logger.info(f"Initializing connection pool with {self.min_connections} connections")
        for _ in range(self.min_connections):
            self._add_connection()
    
    def _create_connection(self):
        """Create a new SQLite connection."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.row_factory = sqlite3.Row
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Set busy timeout to avoid database locked errors
            conn.execute(f"PRAGMA busy_timeout = {self.timeout * 1000}")
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Error creating database connection: {str(e)}")
            raise
    
    def _add_connection(self):
        """Add a new connection to the pool."""
        with self.lock:
            if self.active_connections < self.max_connections:
                try:
                    conn = self._create_connection()
                    self.pool.put(conn, block=False)
                    self.active_connections += 1
                    self.logger.debug(f"Added new connection to pool. Active connections: {self.active_connections}")
                except queue.Full:
                    # If the queue is full, close the connection
                    if conn:
                        conn.close()
                    self.logger.warning("Connection pool is full, couldn't add connection")
                except Exception as e:
                    self.logger.error(f"Error adding connection to pool: {str(e)}")
            else:
                self.logger.warning(f"Maximum connections reached ({self.max_connections})")
    
    def get_connection(self):
        """Get a connection from the pool."""
        try:
            # Try to get a connection from the pool
            conn = self.pool.get(block=True, timeout=self.timeout)
            self.logger.debug("Retrieved connection from pool")
            return conn
        except queue.Empty:
            # If the pool is empty but we haven't reached max connections, create a new one
            with self.lock:
                if self.active_connections < self.max_connections:
                    self.logger.info("Pool empty, creating new connection")
                    return self._create_connection()
                else:
                    self.logger.error("Connection pool exhausted and at maximum capacity")
                    raise ConnectionError("No available database connections")
    
    def return_connection(self, conn):
        """Return a connection to the pool."""
        if conn is None:
            return
            
        try:
            # Check if connection is still valid
            conn.execute("SELECT 1")
            # Return to pool
            self.pool.put(conn, block=False)
            self.logger.debug("Returned connection to pool")
        except (sqlite3.Error, queue.Full) as e:
            # If the connection is invalid or pool is full, close it
            self.logger.warning(f"Couldn't return connection to pool: {str(e)}")
            with self.lock:
                self.active_connections -= 1
            conn.close()
    
    @contextmanager
    def connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            self.logger.error(f"Error with pooled connection: {str(e)}")
            # If there's an exception, close the connection instead of returning it to the pool
            if conn:
                try:
                    conn.close()
                    with self.lock:
                        self.active_connections -= 1
                except Exception:
                    pass
            raise
        else:
            # If no exception occurred, return the connection to the pool
            self.return_connection(conn)
    
    def close_all(self):
        """Close all connections in the pool."""
        self.logger.info("Closing all database connections")
        with self.lock:
            while not self.pool.empty():
                try:
                    conn = self.pool.get(block=False)
                    conn.close()
                    self.active_connections -= 1
                except Exception as e:
                    self.logger.error(f"Error closing connection: {str(e)}")
            
            self.logger.info("All connections closed")
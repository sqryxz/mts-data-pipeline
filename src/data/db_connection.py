"""
Database connection manager for SQLite operations.
Provides context manager for safe database connections with proper cleanup.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator


class DatabaseConnection:
    """Manages SQLite database connections with proper cleanup."""
    
    def __init__(self, db_path: str = "data/crypto_data.db"):
        """
        Initialize database connection manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection with row factory enabled
            
        Raises:
            sqlite3.Error: If database connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Enable row factory for column access by name
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close() 
"""
Database initialization module.
Reads and executes the SQL schema file to create database tables.
"""

import os
import logging
from typing import Optional

from .db_connection import DatabaseConnection


def initialize_database(db_path: Optional[str] = None) -> bool:
    """
    Initialize the database by executing the schema.sql file.
    
    Args:
        db_path: Optional path to database file. Uses default if None.
        
    Returns:
        bool: True if initialization successful, False otherwise
        
    Raises:
        FileNotFoundError: If schema.sql file is not found
        sqlite3.Error: If database operations fail
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Get the schema file path (same directory as this module)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, "schema.sql")
        
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        # Read the schema file
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Initialize database connection
        db_conn = DatabaseConnection(db_path) if db_path else DatabaseConnection()
        
        # Execute the schema
        with db_conn.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        
        logger.info(f"Database initialized successfully at: {db_conn.db_path}")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Schema file error: {e}")
        raise
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    # Allow running this module directly for testing
    logging.basicConfig(level=logging.INFO)
    initialize_database() 
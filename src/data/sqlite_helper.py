"""
SQLite database helper class for crypto data operations.
Provides high-level interface for database operations with automatic initialization.
"""

import logging
import sqlite3
from typing import Optional, List, Dict, Tuple

import pandas as pd

from .db_connection import DatabaseConnection
from .db_init import initialize_database


class CryptoDatabase:
    """
    High-level database helper for crypto data operations.
    Automatically initializes database on instantiation.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the CryptoDatabase helper.
        
        Args:
            db_path: Optional path to SQLite database file. 
                    Uses default 'data/crypto_data.db' if None.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up database connection
        self.db_connection = DatabaseConnection(db_path) if db_path else DatabaseConnection()
        self.db_path = self.db_connection.db_path
        
        # Auto-initialize database on instantiation
        self._initialize_database()
        
        self.logger.info(f"CryptoDatabase initialized with database: {self.db_path}")
    
    def _initialize_database(self) -> None:
        """
        Initialize the database by creating tables if they don't exist.
        
        Raises:
            RuntimeError: If database initialization fails
        """
        try:
            success = initialize_database(self.db_path)
            if not success:
                raise RuntimeError("Database initialization returned False")
                
            self.logger.debug("Database tables initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise RuntimeError(f"Database initialization failed: {e}") from e
    
    def insert_crypto_data(self, crypto_data: List[Dict]) -> int:
        """
        Insert cryptocurrency OHLCV data into the database.
        
        Args:
            crypto_data: List of dictionaries containing crypto data.
                        Each dict should have keys: cryptocurrency, timestamp, 
                        date_str, open, high, low, close, volume
        
        Returns:
            int: Number of records successfully inserted (excludes duplicates)
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        if not crypto_data:
            self.logger.debug("No crypto data provided for insertion")
            return 0
        
        insert_sql = """
            INSERT OR IGNORE INTO crypto_ohlcv 
            (cryptocurrency, timestamp, date_str, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get initial row count
                cursor.execute("SELECT COUNT(*) FROM crypto_ohlcv")
                initial_count = cursor.fetchone()[0]
                
                # Insert data
                for record in crypto_data:
                    cursor.execute(insert_sql, (
                        record['cryptocurrency'],
                        record['timestamp'],
                        record['date_str'],
                        record['open'],
                        record['high'],
                        record['low'],
                        record['close'],
                        record['volume']
                    ))
                
                # Get final row count
                cursor.execute("SELECT COUNT(*) FROM crypto_ohlcv")
                final_count = cursor.fetchone()[0]
                
                conn.commit()
                
                inserted_count = final_count - initial_count
                self.logger.debug(f"Inserted {inserted_count} crypto records out of {len(crypto_data)} provided")
                
                return inserted_count
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to insert crypto data: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Missing required field in crypto data: {e}")
            raise ValueError(f"Missing required field: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error inserting crypto data: {e}")
            raise
    
    def insert_macro_data(self, macro_data: List[Dict]) -> int:
        """
        Insert macro economic indicators data into the database.
        
        Args:
            macro_data: List of dictionaries containing macro data.
                       Each dict should have keys: indicator, date, value
                       Optional keys: is_interpolated, is_forward_filled
        
        Returns:
            int: Number of records successfully inserted (excludes duplicates)
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        if not macro_data:
            self.logger.debug("No macro data provided for insertion")
            return 0
        
        insert_sql = """
            INSERT OR IGNORE INTO macro_indicators 
            (indicator, date, value, is_interpolated, is_forward_filled)
            VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get initial row count
                cursor.execute("SELECT COUNT(*) FROM macro_indicators")
                initial_count = cursor.fetchone()[0]
                
                # Insert data
                for record in macro_data:
                    cursor.execute(insert_sql, (
                        record['indicator'],
                        record['date'],
                        record['value'],
                        record.get('is_interpolated', False),
                        record.get('is_forward_filled', False)
                    ))
                
                # Get final row count
                cursor.execute("SELECT COUNT(*) FROM macro_indicators")
                final_count = cursor.fetchone()[0]
                
                conn.commit()
                
                inserted_count = final_count - initial_count
                self.logger.debug(f"Inserted {inserted_count} macro records out of {len(macro_data)} provided")
                
                return inserted_count
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to insert macro data: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Missing required field in macro data: {e}")
            raise ValueError(f"Missing required field: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error inserting macro data: {e}")
            raise
    
    def get_latest_crypto_timestamp(self, cryptocurrency: str) -> Optional[int]:
        """
        Get the latest timestamp for a specific cryptocurrency.
        Used for incremental data collection.
        
        Args:
            cryptocurrency: Name of the cryptocurrency (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            Optional[int]: Latest timestamp if data exists, None otherwise
            
        Raises:
            sqlite3.Error: If database query fails
        """
        query_sql = """
            SELECT MAX(timestamp) FROM crypto_ohlcv 
            WHERE cryptocurrency = ?
        """
        
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query_sql, (cryptocurrency,))
                result = cursor.fetchone()
                
                # Handle case where no data exists or result is None
                latest_timestamp = result[0] if result and result[0] is not None else None
                
                self.logger.debug(f"Latest timestamp for {cryptocurrency}: {latest_timestamp}")
                return latest_timestamp
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get latest crypto timestamp for {cryptocurrency}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting latest crypto timestamp: {e}")
            raise
    
    def get_latest_macro_date(self, indicator: str) -> Optional[str]:
        """
        Get the latest date for a specific macro indicator.
        Used for incremental data collection.
        
        Args:
            indicator: Name of the macro indicator (e.g., 'VIX', 'DXY', 'DGS10', 'DFF')
            
        Returns:
            Optional[str]: Latest date if data exists, None otherwise
            
        Raises:
            sqlite3.Error: If database query fails
        """
        query_sql = """
            SELECT MAX(date) FROM macro_indicators 
            WHERE indicator = ?
        """
        
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query_sql, (indicator,))
                result = cursor.fetchone()
                
                # Handle case where no data exists or result is None
                latest_date = result[0] if result and result[0] is not None else None
                
                self.logger.debug(f"Latest date for {indicator}: {latest_date}")
                return latest_date
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get latest macro date for {indicator}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting latest macro date: {e}")
            raise
    
    def query_to_dataframe(self, sql: str, params: Tuple = ()) -> pd.DataFrame:
        """
        Execute a SQL query and return the results as a pandas DataFrame.
        Generic method for converting SQL query results to DataFrame format.
        
        Args:
            sql: SQL query string
            params: Tuple of parameters for parameterized queries
            
        Returns:
            pd.DataFrame: Query results as DataFrame, empty DataFrame if no results
            
        Raises:
            sqlite3.Error: If database query fails
        """
        try:
            with self.db_connection.get_connection() as conn:
                # Use pandas.read_sql_query for efficient SQL-to-DataFrame conversion
                df = pd.read_sql_query(sql, conn, params=params)
                
                self.logger.debug(f"Query returned {len(df)} rows")
                return df
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to execute query: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in query_to_dataframe: {e}")
            raise
    
    def get_crypto_data(self, cryptocurrency: str, days: int = 30) -> pd.DataFrame:
        """
        Retrieve cryptocurrency OHLCV data for analysis.
        Returns recent data for the specified cryptocurrency within the date range.
        
        Args:
            cryptocurrency: Name of the cryptocurrency (e.g., 'bitcoin', 'ethereum')
            days: Number of recent days to retrieve (default: 30)
            
        Returns:
            pd.DataFrame: OHLCV data with all columns, ordered by timestamp ascending
            
        Raises:
            sqlite3.Error: If database query fails
        """
        # Calculate the cutoff timestamp for the date range
        # Database stores timestamps in milliseconds, so convert accordingly
        import time
        current_timestamp = int(time.time())
        cutoff_timestamp = (current_timestamp - (days * 24 * 60 * 60)) * 1000
        
        query_sql = """
            SELECT 
                id,
                cryptocurrency,
                timestamp,
                date_str,
                open,
                high,
                low,
                close,
                volume,
                created_at
            FROM crypto_ohlcv 
            WHERE cryptocurrency = ? 
            AND timestamp >= ?
            ORDER BY timestamp ASC
        """
        
        try:
            df = self.query_to_dataframe(query_sql, (cryptocurrency, cutoff_timestamp))
            
            self.logger.debug(f"Retrieved {len(df)} records for {cryptocurrency} over {days} days")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get crypto data for {cryptocurrency}: {e}")
            raise
    
    def get_health_status(self) -> Dict:
        """
        Get database health status and metrics for operational visibility.
        
        Returns:
            Dict: Health status containing crypto_data and macro_data arrays
                 with latest_date, total_records for each symbol/indicator,
                 plus database_path and database_size_mb
        """
        import os
        
        try:
            health_status = {
                'database_path': self.db_path,
                'database_size_mb': 0.0,
                'crypto_data': [],
                'macro_data': []
            }
            
            # Get database file size
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                health_status['database_size_mb'] = round(size_bytes / (1024 * 1024), 2)
            
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get crypto data health status
                crypto_query = """
                    SELECT 
                        cryptocurrency,
                        COUNT(*) as total_records,
                        MAX(date_str) as latest_date
                    FROM crypto_ohlcv 
                    GROUP BY cryptocurrency
                    ORDER BY cryptocurrency
                """
                cursor.execute(crypto_query)
                crypto_results = cursor.fetchall()
                
                for row in crypto_results:
                    health_status['crypto_data'].append({
                        'symbol': row[0],
                        'total_records': row[1],
                        'latest_date': row[2]
                    })
                
                # Get macro data health status  
                macro_query = """
                    SELECT 
                        indicator,
                        COUNT(*) as total_records,
                        MAX(date) as latest_date
                    FROM macro_indicators 
                    GROUP BY indicator
                    ORDER BY indicator
                """
                cursor.execute(macro_query)
                macro_results = cursor.fetchall()
                
                for row in macro_results:
                    health_status['macro_data'].append({
                        'indicator': row[0],
                        'total_records': row[1],
                        'latest_date': row[2]
                    })
            
            self.logger.debug(f"Health status retrieved: {len(health_status['crypto_data'])} cryptos, {len(health_status['macro_data'])} indicators")
            return health_status
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            # Return basic status even if detailed queries fail
            return {
                'database_path': self.db_path,
                'database_size_mb': 0.0,
                'crypto_data': [],
                'macro_data': [],
                'error': str(e)
            }

    def get_combined_analysis_data(self, cryptocurrency: str, days: int = 30) -> pd.DataFrame:
        """
        Get cryptocurrency data with macro indicators joined for comprehensive analysis.
        
        This method performs LEFT JOINs to combine crypto OHLCV data with all 4 macro indicators
        (VIX, Fed Funds Rate, 10-Year Treasury, Dollar Index) by date. Missing macro data
        will appear as NULL values in the DataFrame.
        
        Args:
            cryptocurrency: Name of the cryptocurrency (e.g., 'bitcoin', 'ethereum')
            days: Number of recent days to retrieve (default: 30)
            
        Returns:
            pd.DataFrame: Combined dataset with crypto price/volume and macro values
                         Columns: [date_str, timestamp, open, high, low, close, volume,
                                  vix_value, fed_funds_rate, treasury_10y_rate, dollar_index]
                         
        Raises:
            sqlite3.Error: If database query fails
        """
        # Calculate the cutoff timestamp for the date range
        import time
        current_timestamp = int(time.time())
        cutoff_timestamp = (current_timestamp - (days * 24 * 60 * 60)) * 1000
        
        # Complex SQL query to join crypto data with all macro indicators
        combined_query = """
            SELECT 
                c.date_str,
                c.timestamp,
                c.open,
                c.high,
                c.low,
                c.close,
                c.volume,
                vix.value AS vix_value,
                fed.value AS fed_funds_rate,
                treasury.value AS treasury_10y_rate,
                dxy.value AS dollar_index
            FROM crypto_ohlcv c
            LEFT JOIN macro_indicators vix 
                ON c.date_str = vix.date AND vix.indicator = 'VIXCLS'
            LEFT JOIN macro_indicators fed 
                ON c.date_str = fed.date AND fed.indicator = 'DFF'  
            LEFT JOIN macro_indicators treasury 
                ON c.date_str = treasury.date AND treasury.indicator = 'DGS10'
            LEFT JOIN macro_indicators dxy 
                ON c.date_str = dxy.date AND dxy.indicator = 'DTWEXBGS'
            WHERE c.cryptocurrency = ?
            AND c.timestamp >= ?
            ORDER BY c.timestamp ASC
        """
        
        try:
            df = self.query_to_dataframe(combined_query, (cryptocurrency, cutoff_timestamp))
            
            # Add derived analysis columns for convenience
            if not df.empty:
                # Convert timestamp to datetime for easier analysis
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Calculate daily returns
                df['daily_return'] = df['close'].pct_change()
                
                # Calculate price volatility (rolling standard deviation of returns)
                df['price_volatility'] = df['daily_return'].rolling(window=7, min_periods=1).std()
                
                # Calculate macro data availability ratio
                macro_columns = ['vix_value', 'fed_funds_rate', 'treasury_10y_rate', 'dollar_index']
                df['macro_data_availability'] = df[macro_columns].notna().sum(axis=1) / len(macro_columns)
            
            self.logger.info(f"Retrieved combined analysis data: {len(df)} records for {cryptocurrency} over {days} days")
            self.logger.debug(f"Macro data coverage: VIX={df['vix_value'].notna().sum()}, Fed={df['fed_funds_rate'].notna().sum()}, Treasury={df['treasury_10y_rate'].notna().sum()}, DXY={df['dollar_index'].notna().sum()}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get combined analysis data for {cryptocurrency}: {e}")
            raise 
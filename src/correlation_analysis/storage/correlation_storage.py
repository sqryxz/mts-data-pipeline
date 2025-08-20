"""
Correlation storage module for correlation analysis.
Handles storing and retrieving correlation history in SQLite database.
"""

import sqlite3
import logging
import time
import queue
import threading
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

import pandas as pd
import numpy as np


class CorrelationStorage:
    """
    Handles storage and retrieval of correlation data in SQLite database.
    Production-ready with connection pooling, transaction management, and concurrent access protection.
    """
    
    def __init__(self, db_path: Optional[str] = None, pool_size: int = 10, config: Optional[Dict] = None):
        """
        Initialize the correlation storage.
        
        Args:
            db_path: Path to SQLite database file (defaults to existing MTS database)
            pool_size: Size of connection pool
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        
        # Use existing MTS database if no path specified
        if db_path is None:
            self.db_path = Path("data/crypto_data.db")
        else:
            self.db_path = Path(db_path)
        
        # Configuration with defaults
        self.config = {
            'pool_size': pool_size,
            'connection_timeout': 30.0,
            'max_retries': 3,
            'retry_delay': 1.0,
            'batch_size': 1000,
            'enable_wal': True,
            'enable_file_locking': True,
            'validate_inputs': True
        }
        if config:
            self.config.update(config)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection pool
        self.connection_pool = queue.Queue(maxsize=self.config['pool_size'])
        self.pool_lock = threading.Lock()
        self.write_lock = threading.RLock()
        self.db_lock_file = self.db_path.with_suffix('.lock')
        
        # Pre-populate connection pool
        self._initialize_connection_pool()
        
        # Initialize database tables
        self._initialize_tables()
        
        self.logger.info(f"Correlation storage initialized with database: {self.db_path}, pool_size: {self.config['pool_size']}")
    
    def _initialize_connection_pool(self) -> None:
        """Initialize the connection pool with pre-created connections."""
        try:
            for _ in range(self.config['pool_size']):
                conn = sqlite3.connect(
                    str(self.db_path), 
                    timeout=self.config['connection_timeout'],
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrency
                if self.config.get('enable_wal', True):
                    conn.execute("PRAGMA journal_mode = WAL")
                    conn.execute("PRAGMA synchronous = NORMAL")
                    conn.execute("PRAGMA cache_size = 10000")
                    conn.execute("PRAGMA temp_store = MEMORY")
                
                self.connection_pool.put(conn)
                
            self.logger.debug(f"Connection pool initialized with {self.config['pool_size']} connections")
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def _initialize_tables(self) -> None:
        """
        Initialize correlation-related tables in the database.
        """
        try:
            with self._get_connection() as conn:
                # Create correlation_history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS correlation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        correlation REAL NOT NULL CHECK (correlation >= -1.0 AND correlation <= 1.0),
                        window_days INTEGER NOT NULL CHECK (window_days > 0),
                        sample_size INTEGER NOT NULL CHECK (sample_size > 0),
                        p_value REAL CHECK (p_value >= 0.0 AND p_value <= 1.0),
                        confidence_interval_lower REAL CHECK (confidence_interval_lower >= -1.0 AND confidence_interval_lower <= 1.0),
                        confidence_interval_upper REAL CHECK (confidence_interval_upper >= -1.0 AND confidence_interval_upper <= 1.0),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(pair, timestamp, window_days)
                    )
                """)
                
                # Create correlation_breakouts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS correlation_breakouts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        z_score REAL NOT NULL,
                        severity TEXT NOT NULL CHECK (severity IN ('low', 'moderate', 'high', 'extreme')),
                        direction TEXT NOT NULL CHECK (direction IN ('positive', 'negative')),
                        confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
                        threshold REAL NOT NULL,
                        current_correlation REAL NOT NULL CHECK (current_correlation >= -1.0 AND current_correlation <= 1.0),
                        historical_mean REAL NOT NULL,
                        historical_std REAL NOT NULL CHECK (historical_std >= 0.0),
                        sample_size INTEGER NOT NULL CHECK (sample_size > 0),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create correlation_pairs table for pair metadata
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS correlation_pairs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT UNIQUE NOT NULL,
                        primary_asset TEXT NOT NULL,
                        secondary_asset TEXT NOT NULL,
                        correlation_windows TEXT NOT NULL,  -- JSON array of windows
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_correlation_history_pair_timestamp ON correlation_history(pair, timestamp DESC)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_correlation_history_window ON correlation_history(window_days)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_correlation_breakouts_pair_timestamp ON correlation_breakouts(pair, timestamp DESC)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_correlation_breakouts_severity ON correlation_breakouts(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_correlation_pairs_active ON correlation_pairs(is_active)")
                
                conn.commit()
                self.logger.debug("Correlation tables initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to initialize correlation tables: {e}")
            raise
    
    @contextmanager
    def _get_connection(self, write_mode: bool = False):
        """
        Context manager for database connections with connection pooling and locking.
        
        Args:
            write_mode: If True, use write lock for concurrent access protection
            
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        lock_file = None
        
        try:
            if write_mode and self.config.get('enable_file_locking', True):
                # Use file-based locking for multi-process safety
                with self.write_lock:
                    lock_file = open(self.db_lock_file, 'w')
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                    
                    # Get connection from pool
                    conn = self.connection_pool.get(timeout=30.0)
            else:
                # Get connection from pool for read operations
                conn = self.connection_pool.get(timeout=30.0)
            
            yield conn
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise
        except queue.Empty:
            self.logger.error("Connection pool timeout - all connections in use")
            raise
        finally:
            if conn:
                # Return connection to pool
                try:
                    self.connection_pool.put(conn, timeout=1.0)
                except queue.Full:
                    # Pool is full, close the connection
                    conn.close()
            
            if lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
    
    def _validate_correlation_data(self, pair: str, timestamp: int, correlation: float, 
                                 window_days: int, sample_size: int) -> bool:
        """
        Validate correlation data before storage.
        
        Args:
            pair: Asset pair name
            timestamp: Unix timestamp
            correlation: Correlation value
            window_days: Correlation window in days
            sample_size: Number of data points used
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.config.get('validate_inputs', True):
            return True
        
        try:
            # Validate correlation range
            if not -1.0 <= correlation <= 1.0:
                self.logger.error(f"Correlation out of range [-1,1]: {correlation}")
                return False
            
            # Validate timestamp (not too far in future)
            current_time = int(datetime.now().timestamp() * 1000)
            if timestamp > current_time + (24 * 3600 * 1000):  # 1 day future max
                self.logger.error(f"Timestamp too far in future: {timestamp}")
                return False
            
            # Validate window and sample size
            if window_days <= 0 or sample_size <= 0:
                self.logger.error(f"Invalid window_days ({window_days}) or sample_size ({sample_size})")
                return False
            
            # Validate pair format
            if not pair or not isinstance(pair, str) or len(pair.strip()) == 0:
                self.logger.error(f"Invalid pair: {pair}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False
    
    def store_correlation_history(self, pair: str, timestamp: int, correlation: float, 
                                window_days: int, sample_size: int, p_value: Optional[float] = None,
                                confidence_interval_lower: Optional[float] = None,
                                confidence_interval_upper: Optional[float] = None) -> bool:
        """
        Store correlation history data in the database with validation and retry logic.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            timestamp: Unix timestamp
            correlation: Correlation value
            window_days: Correlation window in days
            sample_size: Number of data points used
            p_value: P-value for statistical significance
            confidence_interval_lower: Lower bound of confidence interval
            confidence_interval_upper: Upper bound of confidence interval
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.store_correlation_history_with_retry(
            pair, timestamp, correlation, window_days, sample_size, 
            p_value, confidence_interval_lower, confidence_interval_upper
        )
    
    def store_correlation_history_with_retry(self, pair: str, timestamp: int, correlation: float, 
                                           window_days: int, sample_size: int, p_value: Optional[float] = None,
                                           confidence_interval_lower: Optional[float] = None,
                                           confidence_interval_upper: Optional[float] = None) -> bool:
        """
        Store correlation history with retry logic and fallback.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            timestamp: Unix timestamp
            correlation: Correlation value
            window_days: Correlation window in days
            sample_size: Number of data points used
            p_value: P-value for statistical significance
            confidence_interval_lower: Lower bound of confidence interval
            confidence_interval_upper: Upper bound of confidence interval
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate inputs
        if not self._validate_correlation_data(pair, timestamp, correlation, window_days, sample_size):
            return False
        
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                with self._get_connection(write_mode=True) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO correlation_history 
                        (pair, timestamp, correlation, window_days, sample_size, p_value, 
                         confidence_interval_lower, confidence_interval_upper)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (pair, timestamp, correlation, window_days, sample_size, 
                         p_value, confidence_interval_lower, confidence_interval_upper))
                    
                    conn.commit()
                    self.logger.debug(f"Stored correlation history: {pair} at {timestamp}")
                    return True
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    self.logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    self.logger.error(f"Failed to store correlation history after {max_retries} attempts: {e}")
                    return self._store_to_fallback(pair, timestamp, correlation, window_days, sample_size, 
                                                 p_value, confidence_interval_lower, confidence_interval_upper)
            
            except sqlite3.Error as e:
                self.logger.error(f"Failed to store correlation history: {e}")
                return False
        
        return False
    
    def store_correlation_batch(self, correlation_data: List[Dict]) -> bool:
        """
        Store multiple correlations in a single transaction for better performance.
        
        Args:
            correlation_data: List of correlation data dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not correlation_data:
            return True
        
        try:
            with self._get_connection(write_mode=True) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                for data in correlation_data:
                    # Validate each record
                    if not self._validate_correlation_data(
                        data['pair'], data['timestamp'], data['correlation'], 
                        data['window_days'], data['sample_size']
                    ):
                        self.logger.warning(f"Skipping invalid correlation data: {data}")
                        continue
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO correlation_history 
                        (pair, timestamp, correlation, window_days, sample_size, p_value, 
                         confidence_interval_lower, confidence_interval_upper)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (data['pair'], data['timestamp'], data['correlation'], 
                         data['window_days'], data['sample_size'], data.get('p_value'),
                         data.get('confidence_interval_lower'), data.get('confidence_interval_upper')))
                
                conn.commit()
                self.logger.info(f"Stored {len(correlation_data)} correlation records in batch")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store correlation batch: {e}")
            return False
    
    def _store_to_fallback(self, pair: str, timestamp: int, correlation: float, 
                          window_days: int, sample_size: int, p_value: Optional[float] = None,
                          confidence_interval_lower: Optional[float] = None,
                          confidence_interval_upper: Optional[float] = None) -> bool:
        """
        Store correlation data to fallback storage (file-based) when database fails.
        
        Args:
            pair: Asset pair name
            timestamp: Unix timestamp
            correlation: Correlation value
            window_days: Correlation window in days
            sample_size: Number of data points used
            p_value: P-value for statistical significance
            confidence_interval_lower: Lower bound of confidence interval
            confidence_interval_upper: Upper bound of confidence interval
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create fallback directory
            fallback_dir = self.db_path.parent / "correlation_fallback"
            fallback_dir.mkdir(exist_ok=True)
            
            # Store in JSON file
            fallback_file = fallback_dir / f"correlation_fallback_{datetime.now().strftime('%Y%m%d')}.json"
            
            import json
            fallback_data = {
                'pair': pair,
                'timestamp': timestamp,
                'correlation': correlation,
                'window_days': window_days,
                'sample_size': sample_size,
                'p_value': p_value,
                'confidence_interval_lower': confidence_interval_lower,
                'confidence_interval_upper': confidence_interval_upper,
                'stored_at': datetime.now().isoformat()
            }
            
            # Append to file
            with open(fallback_file, 'a') as f:
                f.write(json.dumps(fallback_data) + '\n')
            
            self.logger.warning(f"Stored correlation data to fallback: {fallback_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store to fallback: {e}")
            return False
    
    def store_correlation_breakout(self, pair: str, timestamp: int, z_score: float,
                                 severity: str, direction: str, confidence: float,
                                 threshold: float, current_correlation: float,
                                 historical_mean: float, historical_std: float,
                                 sample_size: int) -> bool:
        """
        Store correlation breakout data in the database with validation.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            timestamp: Unix timestamp
            z_score: Z-score value
            severity: Breakout severity (low, moderate, high, extreme)
            direction: Breakout direction (positive, negative)
            confidence: Confidence level (0.0 to 1.0)
            threshold: Z-score threshold used
            current_correlation: Current correlation value
            historical_mean: Historical mean correlation
            historical_std: Historical standard deviation
            sample_size: Number of data points used
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate inputs
        if not self._validate_correlation_data(pair, timestamp, current_correlation, 1, sample_size):
            return False
        
        if severity not in ['low', 'moderate', 'high', 'extreme']:
            self.logger.error(f"Invalid severity: {severity}")
            return False
        
        if direction not in ['positive', 'negative']:
            self.logger.error(f"Invalid direction: {direction}")
            return False
        
        if not 0.0 <= confidence <= 1.0:
            self.logger.error(f"Invalid confidence: {confidence}")
            return False
        
        if historical_std < 0.0:
            self.logger.error(f"Invalid historical_std: {historical_std}")
            return False
        
        try:
            with self._get_connection(write_mode=True) as conn:
                conn.execute("""
                    INSERT INTO correlation_breakouts 
                    (pair, timestamp, z_score, severity, direction, confidence, threshold,
                     current_correlation, historical_mean, historical_std, sample_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pair, timestamp, z_score, severity, direction, confidence, threshold,
                     current_correlation, historical_mean, historical_std, sample_size))
                
                conn.commit()
                self.logger.debug(f"Stored correlation breakout: {pair} at {timestamp}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store correlation breakout: {e}")
            return False
    
    def get_correlation_history(self, pair: str, start_timestamp: Optional[int] = None,
                              end_timestamp: Optional[int] = None, 
                              window_days: Optional[int] = None,
                              limit: Optional[int] = None,
                              columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Retrieve correlation history for a pair with optimized queries.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            start_timestamp: Start timestamp (Unix)
            end_timestamp: End timestamp (Unix)
            window_days: Filter by window days
            limit: Maximum number of records to return
            columns: Specific columns to retrieve (None for all)
            
        Returns:
            pd.DataFrame: Correlation history data
        """
        try:
            # Select only needed columns for performance
            if columns:
                column_str = ', '.join(columns)
            else:
                column_str = 'timestamp, correlation, window_days, sample_size, p_value, confidence_interval_lower, confidence_interval_upper'
            
            query = f"SELECT {column_str} FROM correlation_history WHERE pair = ?"
            params = [pair]
            
            if start_timestamp is not None:
                query += " AND timestamp >= ?"
                params.append(start_timestamp)
            
            if end_timestamp is not None:
                query += " AND timestamp <= ?"
                params.append(end_timestamp)
            
            if window_days is not None:
                query += " AND window_days = ?"
                params.append(window_days)
            
            query += " ORDER BY timestamp DESC"
            
            if limit is not None:
                query += f" LIMIT {limit}"
            
            with self._get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                
            self.logger.debug(f"Retrieved {len(df)} correlation history records for {pair}")
            return df
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve correlation history: {e}")
            return pd.DataFrame()
    
    def get_correlation_breakouts(self, pair: Optional[str] = None,
                                start_timestamp: Optional[int] = None,
                                end_timestamp: Optional[int] = None,
                                severity: Optional[str] = None,
                                limit: Optional[int] = None) -> pd.DataFrame:
        """
        Retrieve correlation breakout data.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            start_timestamp: Start timestamp (Unix)
            end_timestamp: End timestamp (Unix)
            severity: Filter by severity level
            limit: Maximum number of records to return
            
        Returns:
            pd.DataFrame: Correlation breakout data
        """
        try:
            query = "SELECT * FROM correlation_breakouts WHERE 1=1"
            params = []
            
            if pair is not None:
                query += " AND pair = ?"
                params.append(pair)
            
            if start_timestamp is not None:
                query += " AND timestamp >= ?"
                params.append(start_timestamp)
            
            if end_timestamp is not None:
                query += " AND timestamp <= ?"
                params.append(end_timestamp)
            
            if severity is not None:
                query += " AND severity = ?"
                params.append(severity)
            
            query += " ORDER BY timestamp DESC"
            
            if limit is not None:
                query += f" LIMIT {limit}"
            
            with self._get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                
            self.logger.debug(f"Retrieved {len(df)} correlation breakout records")
            return df
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve correlation breakouts: {e}")
            return pd.DataFrame()
    
    def get_latest_correlation(self, pair: str, window_days: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get the latest correlation data for a pair.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            window_days: Filter by window days
            
        Returns:
            Optional[Dict[str, Any]]: Latest correlation data or None
        """
        try:
            query = "SELECT * FROM correlation_history WHERE pair = ?"
            params = [pair]
            
            if window_days is not None:
                query += " AND window_days = ?"
                params.append(window_days)
            
            query += " ORDER BY timestamp DESC LIMIT 1"
            
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                
            if row:
                return dict(row)
            else:
                return None
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get latest correlation: {e}")
            return None
    
    def get_correlation_statistics(self, pair: str, window_days: Optional[int] = None,
                                 days_back: int = 30) -> Dict[str, Any]:
        """
        Get correlation statistics for a pair.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            window_days: Filter by window days
            days_back: Number of days to look back
            
        Returns:
            Dict[str, Any]: Correlation statistics
        """
        try:
            # Calculate start timestamp
            start_timestamp = int((datetime.now().timestamp() - (days_back * 24 * 3600)) * 1000)
            
            query = """
                SELECT 
                    COUNT(*) as count,
                    AVG(correlation) as mean_correlation,
                    MIN(correlation) as min_correlation,
                    MAX(correlation) as max_correlation,
                    AVG(sample_size) as avg_sample_size
                FROM correlation_history 
                WHERE pair = ? AND timestamp >= ?
            """
            params = [pair, start_timestamp]
            
            if window_days is not None:
                query += " AND window_days = ?"
                params.append(window_days)
            
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                
                if row:
                    result = dict(row)
                    
                    # Calculate standard deviation using a separate query
                    std_query = """
                        SELECT correlation FROM correlation_history 
                        WHERE pair = ? AND timestamp >= ?
                    """
                    std_params = [pair, start_timestamp]
                    
                    if window_days is not None:
                        std_query += " AND window_days = ?"
                        std_params.append(window_days)
                    
                    cursor2 = conn.execute(std_query, std_params)
                    correlations = [row[0] for row in cursor2.fetchall()]
                    
                    if correlations:
                        import statistics
                        try:
                            result['std_correlation'] = statistics.stdev(correlations)
                        except statistics.StatisticsError:
                            result['std_correlation'] = 0.0
                    else:
                        result['std_correlation'] = 0.0
                    
                    return result
                else:
                    return {}
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get correlation statistics: {e}")
            return {}
    
    def get_active_pairs(self) -> List[str]:
        """
        Get list of active correlation pairs.
        
        Returns:
            List[str]: List of active pair names
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT pair FROM correlation_pairs WHERE is_active = 1")
                pairs = [row[0] for row in cursor.fetchall()]
                
            return pairs
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get active pairs: {e}")
            return []
    
    def add_correlation_pair(self, pair: str, primary_asset: str, secondary_asset: str,
                           correlation_windows: List[int]) -> bool:
        """
        Add a new correlation pair to the database.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            primary_asset: Primary asset name
            secondary_asset: Secondary asset name
            correlation_windows: List of correlation windows in days
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import json
            windows_json = json.dumps(correlation_windows)
            
            with self._get_connection(write_mode=True) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO correlation_pairs 
                    (pair, primary_asset, secondary_asset, correlation_windows, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (pair, primary_asset, secondary_asset, windows_json))
                
                conn.commit()
                self.logger.info(f"Added correlation pair: {pair}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to add correlation pair: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            Dict[str, Any]: Database information
        """
        try:
            with self._get_connection() as conn:
                # Get table counts
                cursor = conn.execute("SELECT COUNT(*) FROM correlation_history")
                history_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM correlation_breakouts")
                breakouts_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM correlation_pairs WHERE is_active = 1")
                active_pairs_count = cursor.fetchone()[0]
                
                # Get database size
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    'database_path': str(self.db_path),
                    'correlation_history_count': history_count,
                    'correlation_breakouts_count': breakouts_count,
                    'active_pairs_count': active_pairs_count,
                    'database_size_bytes': db_size,
                    'connection_pool_size': self.config['pool_size'],
                    'last_updated': datetime.now().isoformat()
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {}
    
    def close(self) -> None:
        """
        Close all connections in the pool.
        """
        try:
            while not self.connection_pool.empty():
                conn = self.connection_pool.get_nowait()
                conn.close()
            self.logger.info("Connection pool closed")
        except Exception as e:
            self.logger.error(f"Error closing connection pool: {e}")
    
    def __del__(self):
        """Cleanup on destruction."""
        self.close()

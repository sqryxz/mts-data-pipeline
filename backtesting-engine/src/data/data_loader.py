import sqlite3
import threading
from typing import Optional, List, Tuple, Any
from datetime import datetime
import pandas as pd

class DataLoader:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self.connect()

    def connect(self):
        with self._lock:
            if self.connection:
                self.connection.close()
            try:
                self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
                self.connection.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                print(f"Failed to connect to database {self.db_path}: {e}")
                self.connection = None

    def close(self):
        with self._lock:
            if self.connection:
                self.connection.close()
                self.connection = None

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def test_connection(self) -> bool:
        if self.connection is None:
            try:
                self.connect()
            except Exception:
                return False
        try:
            with self._lock:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True
        except sqlite3.Error as e:
            print(f"Database connection test failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during connection test: {e}")
            return False

    def execute_query(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            if not self.connection:
                self.connect()
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor

    def fetch_all(self, query: str, params: Tuple = ()) -> List[Any]:
        cursor = self.execute_query(query, params)
        try:
            return cursor.fetchall()
        finally:
            cursor.close()

    def load_market_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            raise ValueError("start_date and end_date must be datetime objects")
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")
        if not symbol.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Symbol contains invalid characters")

        # Convert to UTC and Unix timestamps
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=pd.Timestamp.utc.tz)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=pd.Timestamp.utc.tz)
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        query = (
            "SELECT timestamp, open, high, low, close, volume "
            "FROM crypto_ohlcv "
            "WHERE symbol = ? AND timestamp >= ? AND timestamp <= ? "
            "ORDER BY timestamp ASC"
        )
        params = (symbol, start_ts, end_ts)
        try:
            rows = self.fetch_all(query, params)
            if not rows:
                empty_df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
                empty_df["timestamp"] = pd.to_datetime(empty_df["timestamp"])
                empty_df.set_index("timestamp", inplace=True)
                return empty_df[["open", "high", "low", "close", "volume"]]
            df = pd.DataFrame(rows)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.set_index("timestamp", inplace=True)
            return df[numeric_columns]
        except Exception as e:
            raise RuntimeError(f"Failed to load market data for {symbol}: {e}") 
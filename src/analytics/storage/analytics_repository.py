import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from datetime import datetime
import pandas as pd
from src.analytics.models.analytics_models import MacroIndicatorMetrics

class AnalyticsRepository:
    """Repository for macro analytics data operations with proper connection management."""
    def __init__(self, db_path: str, enable_wal: bool = True):
        self.db_path = Path(db_path)
        self.enable_wal = enable_wal
        self.logger = logging.getLogger(__name__)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _initialize_database(self) -> None:
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.execute("PRAGMA foreign_keys = ON")
            if self.enable_wal:
                conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.commit()
            self.logger.info(f"Database initialized: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def health_check(self) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Database health check failed: {e}")
            return False

    def save_metrics(self, metrics: MacroIndicatorMetrics) -> bool:
        query = """
        INSERT OR REPLACE INTO macro_analytics_results 
        (indicator, timeframe, timestamp, current_value, rate_of_change, 
         z_score, percentile_rank, mean, std_dev, lookback_period, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                conn.execute(query, (
                    metrics.indicator,
                    metrics.timeframe,
                    metrics.timestamp,
                    metrics.current_value,
                    metrics.rate_of_change,
                    metrics.z_score,
                    metrics.percentile_rank,
                    metrics.mean,
                    metrics.std_dev,
                    metrics.lookback_period,
                    metrics.timestamp
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save metrics for {metrics.indicator}: {e}")
            return False

    def get_latest_metrics(self, indicator: str, timeframe: str) -> Optional[MacroIndicatorMetrics]:
        query = """
        SELECT indicator, timeframe, timestamp, current_value, rate_of_change,
               z_score, percentile_rank, mean, std_dev, lookback_period
        FROM macro_analytics_results 
        WHERE indicator = ? AND timeframe = ?
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (indicator, timeframe))
                row = cursor.fetchone()
                if row:
                    return MacroIndicatorMetrics(**dict(row))
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get latest metrics for {indicator}/{timeframe}: {e}")
            return None

    def _validate_date_format(self, date_str: str) -> bool:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def get_indicator_data(self, indicator: str, start_date: str, end_date: str, interpolate: bool = True) -> pd.DataFrame:
        if not self._validate_date_format(start_date):
            self.logger.error(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD")
            return pd.DataFrame()
        if not self._validate_date_format(end_date):
            self.logger.error(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD")
            return pd.DataFrame()
        query = """
        SELECT indicator, date, value
        FROM macro_indicators
        WHERE indicator = ? AND date >= ? AND date <= ?
        ORDER BY date ASC
        """
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=(indicator, start_date, end_date))
            if interpolate and not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()
                df['value'] = df['value'].interpolate(method='linear')
                df['value'] = df['value'].bfill()
                df['value'] = df['value'].ffill()
                df = df.reset_index()
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            self.logger.info(f"Retrieved {len(df)} records for {indicator} from {start_date} to {end_date}")
            return df
        except sqlite3.Error as e:
            self.logger.error(f"Database error fetching {indicator} data: {e}")
            return pd.DataFrame()
        except pd.errors.DatabaseError as e:
            self.logger.error(f"Pandas database error fetching {indicator} data: {e}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {indicator} data: {e}")
            return pd.DataFrame()

    def get_multiple_indicators_data(self, indicators: list[str], start_date: str, end_date: str, interpolate: bool = True) -> pd.DataFrame:
        if not indicators:
            return pd.DataFrame()
        all_data = []
        for indicator in indicators:
            df = self.get_indicator_data(indicator, start_date, end_date, interpolate)
            if not df.empty:
                df_pivot = df.set_index('date')[['value']].rename(columns={'value': indicator})
                all_data.append(df_pivot)
        if not all_data:
            return pd.DataFrame()
        combined_df = pd.concat(all_data, axis=1, sort=True)
        combined_df.index = pd.to_datetime(combined_df.index)
        combined_df = combined_df.sort_index()
        return combined_df

    def get_data_summary(self, indicator: str) -> dict:
        query = """
        SELECT 
            COUNT(*) as record_count,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            MIN(value) as min_value,
            MAX(value) as max_value,
            AVG(value) as avg_value
        FROM macro_indicators 
        WHERE indicator = ?
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (indicator,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return {}
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get data summary for {indicator}: {e}")
            return {} 
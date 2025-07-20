from src.analytics.storage.analytics_repository import AnalyticsRepository
from src.analytics.models.analytics_models import MacroIndicatorMetrics
from datetime import datetime
import os
import tempfile
import pandas as pd

def test_analytics_repository_connection_and_health():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    try:
        repo = AnalyticsRepository(db_path)
        # Create table for test
        with repo.get_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS macro_analytics_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                current_value REAL NOT NULL,
                rate_of_change REAL NOT NULL,
                z_score REAL NOT NULL,
                percentile_rank REAL NOT NULL CHECK(percentile_rank >= 0 AND percentile_rank <= 100),
                mean REAL NOT NULL,
                std_dev REAL NOT NULL CHECK(std_dev >= 0),
                lookback_period INTEGER NOT NULL CHECK(lookback_period > 0),
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(indicator, timeframe, timestamp)
            );''')
            conn.commit()
        assert repo.health_check()
    finally:
        os.remove(db_path)

def test_save_and_get_latest_metrics():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    try:
        repo = AnalyticsRepository(db_path)
        with repo.get_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS macro_analytics_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                current_value REAL NOT NULL,
                rate_of_change REAL NOT NULL,
                z_score REAL NOT NULL,
                percentile_rank REAL NOT NULL CHECK(percentile_rank >= 0 AND percentile_rank <= 100),
                mean REAL NOT NULL,
                std_dev REAL NOT NULL CHECK(std_dev >= 0),
                lookback_period INTEGER NOT NULL CHECK(lookback_period > 0),
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(indicator, timeframe, timestamp)
            );''')
            conn.commit()
        now = int(datetime(2024, 7, 10, 12, 0).timestamp())
        metrics = MacroIndicatorMetrics(
            indicator='VIX',
            timestamp=now,
            timeframe='1h',
            current_value=15.0,
            rate_of_change=0.05,
            z_score=1.2,
            percentile_rank=85.0,
            mean=14.5,
            std_dev=0.5,
            lookback_period=30
        )
        assert repo.save_metrics(metrics)
        fetched = repo.get_latest_metrics('VIX', '1h')
        assert fetched is not None
        assert fetched.indicator == 'VIX'
        assert fetched.timestamp == now
    finally:
        os.remove(db_path)

def test_get_indicator_data():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    try:
        repo = AnalyticsRepository(db_path)
        with repo.get_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS macro_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT NOT NULL,
                date TEXT NOT NULL,
                value REAL NOT NULL,
                is_interpolated BOOLEAN DEFAULT 0,
                is_forward_filled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(indicator, date)
            );''')
            # Insert sample data
            conn.execute("INSERT INTO macro_indicators (indicator, date, value) VALUES (?, ?, ?)", ('VIX', '2024-07-01', 12.0))
            conn.execute("INSERT INTO macro_indicators (indicator, date, value) VALUES (?, ?, ?)", ('VIX', '2024-07-02', 14.0))
            conn.execute("INSERT INTO macro_indicators (indicator, date, value) VALUES (?, ?, ?)", ('VIX', '2024-07-03', 16.0))
            conn.commit()
        df = repo.get_indicator_data('VIX', '2024-07-01', '2024-07-03')
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert set(df['value']) == {12.0, 14.0, 16.0}
    finally:
        os.remove(db_path) 
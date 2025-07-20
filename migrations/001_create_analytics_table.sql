-- Migration: Create macro_analytics_results table for macro analytics module

CREATE TABLE IF NOT EXISTS macro_analytics_results (
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
);

CREATE INDEX IF NOT EXISTS idx_analytics_indicator_timeframe 
ON macro_analytics_results(indicator, timeframe, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_timestamp 
ON macro_analytics_results(timestamp); 
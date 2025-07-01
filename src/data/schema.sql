-- SQLite Database Schema for Crypto Data Pipeline
-- This schema defines tables for storing cryptocurrency OHLCV data and macro economic indicators

-- Table for storing cryptocurrency OHLCV (Open, High, Low, Close, Volume) data
CREATE TABLE IF NOT EXISTS crypto_ohlcv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cryptocurrency TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    date_str TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate entries for same cryptocurrency at same timestamp
    UNIQUE(cryptocurrency, timestamp)
);

-- Table for storing macro economic indicators
CREATE TABLE IF NOT EXISTS macro_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL NOT NULL,
    is_interpolated BOOLEAN DEFAULT 0,
    is_forward_filled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate entries for same indicator on same date
    UNIQUE(indicator, date)
);

-- Indexes for better query performance

-- Indexes for crypto_ohlcv table
CREATE INDEX IF NOT EXISTS idx_crypto_ohlcv_cryptocurrency ON crypto_ohlcv(cryptocurrency);
CREATE INDEX IF NOT EXISTS idx_crypto_ohlcv_timestamp ON crypto_ohlcv(timestamp);
CREATE INDEX IF NOT EXISTS idx_crypto_ohlcv_date_str ON crypto_ohlcv(date_str);

-- Indexes for macro_indicators table
CREATE INDEX IF NOT EXISTS idx_macro_indicators_indicator ON macro_indicators(indicator);
CREATE INDEX IF NOT EXISTS idx_macro_indicators_date ON macro_indicators(date); 
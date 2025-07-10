-- Order book data table
CREATE TABLE IF NOT EXISTS order_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    side TEXT NOT NULL, -- 'bid' or 'ask'
    level INTEGER NOT NULL, -- 0-based level (0 = best bid/ask)
    price REAL NOT NULL,
    quantity REAL NOT NULL,
    UNIQUE(exchange, symbol, timestamp, side, level)
);

CREATE INDEX IF NOT EXISTS idx_order_book_lookup ON order_book(exchange, symbol, timestamp);

-- Bid-ask spread data table
CREATE TABLE IF NOT EXISTS bid_ask_spreads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    bid_price REAL NOT NULL,
    ask_price REAL NOT NULL,
    spread_absolute REAL NOT NULL,
    spread_percentage REAL NOT NULL,
    mid_price REAL NOT NULL,
    UNIQUE(exchange, symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_spreads_lookup ON bid_ask_spreads(exchange, symbol, timestamp);

-- Funding rate data table
CREATE TABLE IF NOT EXISTS funding_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    funding_rate REAL NOT NULL,
    predicted_rate REAL,
    funding_time INTEGER NOT NULL,
    UNIQUE(exchange, symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_funding_lookup ON funding_rates(exchange, symbol, timestamp); 
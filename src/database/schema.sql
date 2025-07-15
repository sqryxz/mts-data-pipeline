-- Enhanced Backtest Results Schema (Production-Ready)

-- Main backtest run records
CREATE TABLE IF NOT EXISTS backtest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) NOT NULL CHECK (initial_capital > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    config_json TEXT,
    status TEXT DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    error_message TEXT,
    -- Core metrics for fast queries
    total_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    trade_count INTEGER,
    CONSTRAINT chk_dates CHECK (start_date <= end_date)
);

-- Flexible performance metrics (name-value pairs)
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_run_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (backtest_run_id) REFERENCES backtest_runs (id) ON DELETE CASCADE
);

-- Trade executions (full trade log)
CREATE TABLE IF NOT EXISTS trade_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_run_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(15,8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(15,8) NOT NULL CHECK (price > 0),
    commission DECIMAL(10,4) NOT NULL DEFAULT 0,
    strategy TEXT,
    signal_strength REAL,
    order_id TEXT,
    FOREIGN KEY (backtest_run_id) REFERENCES backtest_runs (id) ON DELETE CASCADE
);

-- Portfolio value snapshots for analytics
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_run_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    cash_balance DECIMAL(15,2) NOT NULL,
    FOREIGN KEY (backtest_run_id) REFERENCES backtest_runs (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy ON backtest_runs(strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_dates ON backtest_runs(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_performance_backtest_id ON performance_metrics(backtest_run_id);
CREATE INDEX IF NOT EXISTS idx_trades_backtest_id ON trade_executions(backtest_run_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trade_executions(symbol, timestamp); 
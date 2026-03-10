# Work Plan: Multi-Factor Signal System

## Overview
Build a three-layer signal system that aggregates macro regime, cross-asset crypto momentum, and mean reversion signals into composite directional trade signals.

---

## Architecture

### Layer 1: Macro Regime Classification
- Classify macro environment into: Risk-On, Neutral, Risk-Off, Liquidity Squeeze
- 8 sub-signals scored -1 to +1 each
- Final Macro Score: range [-1, +1]

### Layer 2: Cross-Asset Crypto Momentum
Three buckets per asset:
- **Trend Bucket**: SMA cross, EMA cross, price vs 200d SMA, ROC
- **Mean Reversion Bucket**: RSI, MACD histogram, Bollinger %B
- **Volatility Bucket**: BB width, Squeeze, VIX-crypto correlation

### Layer 3: Composite Signal
- Weighted aggregation with dynamic weights based on VIX-crypto correlation
- Confirmation gate: 2-of-3 layers must agree
- Alert thresholds: Strong Long (>0.6), Lean Long (0.3-0.6), Neutral, Lean Short, Strong Short

---

## Files to Create

### 1. New Strategy File
`src/signals/strategies/multi_factor_strategy.py`
- Main strategy class implementing SignalStrategy interface
- Layer 1: Macro regime classifier
- Layer 2: Per-asset momentum/reversion/volatility calculators
- Layer 3: Composite aggregator with confirmation gate

### 2. Configuration File
`config/strategies/multi_factor.json`
```json
{
  "name": "Multi-Factor Strategy",
  "description": "Three-layer signal system combining macro regime, momentum, and mean reversion",
  "enabled": true,
  "layer_weights": {
    "macro": 0.30,
    "trend": 0.40,
    "reversion": 0.30
  },
  "high_corr_weights": {
    "macro": 0.45,
    "trend": 0.30,
    "reversion": 0.25
  },
  "alert_thresholds": {
    "strong_long": 0.6,
    "lean_long": 0.3,
    "lean_short": -0.3,
    "strong_short": -0.6
  },
  "asset_betas": {
    "bitcoin": 1.0,
    "ethereum": 1.1,
    "solana": 1.1,
    "sui": 1.1,
    "chainlink": 1.2,
    "uniswap": 1.2,
    "render-token": 1.2,
    "bittensor": 1.2,
    "fetch-ai": 1.3,
    "ocean-protocol": 1.3,
    "singularitynet": 1.3,
    "dogecoin": 1.2,
    "ripple": 0.9,
    "binancecoin": 0.9,
    "hyperliquid": 1.3,
    "ethena": 1.3
  },
  "indicator_windows": {
    "short_ma": 20,
    "long_ma": 50,
    "rsi": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bollinger_window": 20,
    "bollinger_std": 2,
    "roc_period": 14,
    "correlation_window": 30
  }
}
```

### 3. Database Schema Update
Add table for signal logging:
```sql
CREATE TABLE IF NOT EXISTS multi_factor_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    asset TEXT NOT NULL,
    macro_score REAL,
    trend_score REAL,
    reversion_score REAL,
    composite_score REAL,
    signal_direction TEXT,
    confirmation_gate_passed INTEGER,
    vix_level REAL,
    dxy_level REAL,
    hy_spread REAL,
    yield_curve_spread REAL,
    liquidity_score REAL,
    rsi_14 REAL,
    sma_20_50_cross TEXT,
    macd_direction TEXT,
    bb_position REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idxmf_asset_date ON multi_factor_signals(asset, timestamp);
```

---

## Implementation Tasks

### Task 1: Multi-Factor Strategy Class
**What to do**: Create `src/signals/strategies/multi_factor_strategy.py`
- Implement `SignalStrategy` interface
- Layer 1: `_calculate_macro_regime()` - classify macro environment
- Layer 2: `_calculate_trend_bucket()`, `_calculate_reversion_bucket()`, `_calculate_volatility_bucket()`
- Layer 3: `_aggregate_composite()`, `_check_confirmation_gate()`
- Per-asset loop excluding USDT
- Apply beta adjustments per asset

**QA Scenarios**:
- Run strategy on BTC - verify scores in range [-1, +1]
- Run on all 16 assets (exclude USDT)
- Check confirmation gate logic: 2-of-3 must agree

---

### Task 2: Configuration File
**What to do**: Create `config/strategies/multi_factor.json`
- Define all weights, thresholds, asset betas
- Indicator windows for MA, RSI, MACD, Bollinger

---

### Task 3: Database Schema
**What to do**: Add `multi_factor_signals` table
- Log all signal components for backtesting
- Create indexes for efficient queries

**QA Scenarios**:
- Verify table created
- Check indexes exist

---

### Task 4: Integration
**What to do**: Add to strategy registry and enable in config
- Register in `src/signals/strategies/__init__.py`
- Add to `ENABLED_STRATEGIES` in `.env`

---

### Task 5: Test Execution
**What to do**: Run strategy and verify output
- Execute signal generation
- Check alert JSON output
- Verify all 16 assets scored (USDT excluded)

---

## Technical Notes

### Data Sources
- **Macro**: Use existing `macro_indicators` table (VIXCLS, DGS*, DTWEXBGS, etc.)
- **Crypto Prices**: Use existing OHLCV data, calculate indicators on-the-fly
- **VIX-Crypto Correlation**: Calculate from daily returns rolling 30d

### Calculation Frequency
- Run every 4 hours (configurable)
- Use latest available data (forward-fill missing)

### Alert Output
- JSON format matching existing alert system
- Include full breakdown of all layer scores
- Include key drivers for each signal

---

## Success Criteria

- [ ] Strategy class implements all 3 layers
- [ ] All 16 crypto assets scored (USDT excluded)
- [ ] Composite scores in range [-1, +1]
- [ ] Confirmation gate working (2-of-3 agreement)
- [ ] Alert thresholds triggering correctly
- [ ] Signal data logged to database
- [ ] Strategy can be enabled/disabled via config

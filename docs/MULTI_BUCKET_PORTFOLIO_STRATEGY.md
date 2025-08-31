# Multi-Bucket Crypto Portfolio Strategy

## Overview

The Multi-Bucket Crypto Portfolio Strategy is a comprehensive systematic trading approach that exploits multiple market inefficiencies across different timeframes and market regimes. The strategy implements the mathematical framework outlined in the requirements with practical risk management and position sizing.

## Strategy Components

### 1. Cross-Sectional Momentum (7/14/30d)

**Implementation:**
- Calculates momentum returns for each horizon: `M_h = P_t / P_{t-h} - 1`
- Computes z-scores over rolling 180-day window: `Z_h = (M_h - μ_h) / σ_h`
- Composite momentum score: `CM = 0.5 * Z_7 + 0.3 * Z_14 + 0.2 * Z_30`
- Acceleration term: `ACC = M_7 - M_14`

**Entry Conditions:**
- `CM > 0.75` (configurable threshold)
- `M_7 > 0.04` (base momentum threshold)
- Trend alignment: `M_7 > 0`, `M_14 > 0`, `M_30 > 0`
- `ACC > 0` OR `Z_30 > 1.5` (established trend allowance)
- Momentum strength confirmation: `MS > 0`

### 2. Residual (Idiosyncratic) Momentum

**Implementation:**
- Linear regression: `R_i,t = α_i + β_i^BTC * R_BTC,t + ε_i,t`
- 60-day rolling OLS on daily returns
- Residual z-score: `Z^res = (ε_t - μ_ε) / σ_ε`
- Beta neutrality constraint: `|Σ w_i * β_i^BTC| < 0.05`

**Entry Conditions:**
- Long: `Z^res > 1.0`
- Short: `Z^res < -1.0`
- Position size boost: 25% if `Z^res > 1.5`

### 3. Mean-Reversion on Overextended Moves

**Implementation:**
- Overextension trigger: `Z_7 > 2.0` AND `MS < 0`
- Oversold trigger: `Z_7 < -2.0` AND `MS > 0.5`
- Reversion target: `Z_7 = 0.5`
- Only active in low correlation regime (`AvgCorr < 0.25`)

### 4. Pair/Spread Convergence

**Implementation:**
- Spread calculation: `S_t = P^ENA_t - (α + β * P^ETH_t)`
- Z-score of spread over 60 bars
- Entry conditions:
  - Long spread: `Z^S < -2` AND `Corr_30d > 0.65` AND `ΔCorr_7d ≥ 0.05`
  - Short spread: `Z^S > 2` under symmetric conditions
- Exit at `Z^S = 0` (mean reversion)

### 5. Dynamic Risk Modulation

**Implementation:**
- Leverage factor calculation:
  ```
  LeverageFactor = {
      1.0                    if AvgCorr ≤ 0.15
      1 - (AvgCorr - 0.15) / 0.35  if 0.15 < AvgCorr < 0.50
      0.4                    if AvgCorr ≥ 0.50
  }
  ```
- Risk-off triggers:
  - `ΔAvgCorr > 0.10` day-over-day AND `AvgCorr > 0.25`
  - Breadth collapse: >60% of universe with `|CM| < 0.25`

## Portfolio Structure

### Target Allocations (Normal Regime)
- **Momentum Long Bucket**: 40-55% gross
- **Residual Long/Short**: 15-25% gross
- **Pair/Convergence**: 10-15% gross
- **Mean-Reversion**: 5-10% gross
- **Cash/Stablecoin**: 15-25%

### Position Sizing

**Volatility Targeting:**
```
RiskPerPos = (TargetPortfolioVol × NAV) / √N_active × k
Notional_i = RiskPerPos / (σ_20,i × P_i)
```

**Position Caps:**
- Max single asset: 20% NAV
- ETH+ENA cluster: 1.2 × single-asset cap
- Mean-reversion shorts: ≤30% of gross

## Risk Management

### Hard Stops
- Momentum longs: `StopPrice = EntryPrice - 2 × ATR_14`
- Trailing stop: Shift up when price advances 1 ATR

### Time Stops
- Residual/pair trades: Close after 10 days if profit < 0.5 × target

### Drawdown Circuit
- Trigger: Peak-to-trough > 8%
- Action: Cut all positions by 50%
- Recovery: Resume at 4% from peak

## Configuration Parameters

### Momentum Parameters
```json
{
  "horizons": [7, 14, 30],
  "weights": [0.5, 0.3, 0.2],
  "zscore_window": 180,
  "composite_threshold": 0.75,
  "base_momentum_threshold": 0.04,
  "established_trend_threshold": 1.5
}
```

### Residual Parameters
```json
{
  "regression_window": 60,
  "residual_window": 20,
  "residual_threshold": 1.0,
  "beta_tolerance": 0.05
}
```

### Correlation Regime Parameters
```json
{
  "correlation_windows": [7, 14, 30, 60],
  "low_correlation_threshold": 0.15,
  "high_correlation_threshold": 0.50,
  "leverage_reduction_factor": 0.4,
  "regime_shift_threshold": 0.10
}
```

## Implementation Files

### Core Strategy
- `src/signals/strategies/multi_bucket_portfolio_strategy.py`
- Main strategy implementation with all analysis methods

### Configuration
- `config/strategies/multi_bucket_portfolio.json`
- Complete parameter configuration

### Testing
- `test_multi_bucket_strategy.py`
- Comprehensive test suite with sample data generation

## Usage Example

```python
from src.signals.strategies.multi_bucket_portfolio_strategy import MultiBucketPortfolioStrategy

# Initialize strategy
strategy = MultiBucketPortfolioStrategy('config/strategies/multi_bucket_portfolio.json')

# Analyze market data
analysis_results = strategy.analyze(market_data)

# Generate signals
signals = strategy.generate_signals(analysis_results)

# Get risk summary
risk_summary = analysis_results['risk_summary']
```

## Performance Attribution

### Daily Metrics
- Hit rate per bucket
- Average holding period per bucket
- Return per unit of ATR risk
- Residual alpha contribution
- Slippage vs mid

### Monthly Metrics
- Information ratio of CM-based ranking
- Turnover vs net alpha
- Regime shift detection accuracy

## Optimization Framework

### Parameter Grid
- Composite threshold: [0.5, 0.75, 1.0, 1.25]
- Momentum weights: Multiple combinations
- Walk-forward validation required

### Validation Criteria
- Sharpe ratio improvement > 0.2
- Residual IR > 0.3 after transaction costs
- Out-of-sample performance consistency

## Monitoring Checklist

### Daily Tasks
1. Recompute momentum metrics (M_7, M_14, M_30, Z-scores, CM, ACC, MS)
2. Update 60-day regressions for betas and residuals
3. Refresh correlations (7/30/60d) and compute AvgCorr
4. Generate candidate list meeting entry criteria
5. Validate cluster exposure constraints
6. Output risk summary (projected VAR, beta, gross/net)

### Risk Monitoring
- Portfolio beta neutrality
- Correlation regime shifts
- Breadth collapse detection
- Drawdown circuit triggers

## Failure Modes & Mitigation

### Regime Shift Lag
- **Risk**: CM exit lagging during correlation spikes
- **Mitigation**: ACC and MS deterioration rules, regime shift detection

### Overfitting
- **Risk**: Threshold optimization on in-sample data
- **Mitigation**: Walk-forward validation, round number thresholds

### Liquidity Issues
- **Risk**: Slippage on smaller caps
- **Mitigation**: Position size ≤ 5% of 30d ADV

### Correlation Compression
- **Risk**: Diversification loss during stress
- **Mitigation**: Leverage scaling, risk-off mode

## Integration with Existing System

The strategy integrates seamlessly with the existing MTS data pipeline:

1. **Data Sources**: Uses existing price data from SQLite database
2. **Signal Framework**: Implements standard TradingSignal interface
3. **Risk Management**: Leverages existing risk management infrastructure
4. **Monitoring**: Integrates with existing alerting and logging systems
5. **Backtesting**: Compatible with existing backtesting framework

## Next Steps

### Phase 1 (MVP)
- Momentum long bucket + basic volatility sizing + leverage factor
- Core signal generation and risk management

### Phase 2 (Enhanced)
- Add residual beta neutrality + pair trade ETH-ENA
- Advanced correlation regime detection

### Phase 3 (Advanced)
- Cross-sectional long/short and mean-reversion overlays
- Dynamic leverage and kill switch automation

### Phase 4 (Optimization)
- Parameter optimization framework
- Performance attribution and monitoring automation

## Summary

The Multi-Bucket Crypto Portfolio Strategy provides a comprehensive framework for systematic crypto trading that:

1. **Exploits Multiple Inefficiencies**: Momentum, residual, mean-reversion, and pair trading
2. **Adapts to Market Regimes**: Dynamic risk modulation based on correlation environment
3. **Manages Risk Systematically**: Position sizing, stops, and portfolio-level controls
4. **Integrates Seamlessly**: Works with existing infrastructure and data pipeline
5. **Scales Efficiently**: Modular design allows for phased implementation

The strategy represents a sophisticated approach to crypto portfolio management that balances alpha generation with risk control across multiple market conditions.

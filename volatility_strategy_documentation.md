# Volatility-Based Signal Generation Module

## Overview

The Volatility Strategy is a sophisticated signal generation module for the MTS Pipeline that identifies potential trading opportunities when 15-minute volatility exceeds historical thresholds for BTC or ETH. This strategy leverages statistical volatility analysis to capture breakout and reversal opportunities in cryptocurrency markets.

## Key Features

### 🎯 **Core Functionality**
- **15-minute rolling volatility calculation** using standard deviation of log returns
- **Historical threshold comparison** against 95th percentile of historical volatility
- **Dynamic position sizing** based on volatility magnitude and confidence
- **Risk management** with volatility-adjusted stop losses and take profits

### 📊 **Signal Types**
1. **LONG Signals**: Generated when volatility exceeds historical threshold but not extreme levels
   - Indicates potential breakout opportunities
   - Higher confidence when volatility is moderately elevated

2. **SHORT Signals**: Generated when volatility reaches extreme levels (98th percentile)
   - Indicates potential reversal opportunities
   - More conservative position sizing for risk management

### ⚙️ **Configurable Parameters**
- `volatility_window`: Time window for volatility calculation (default: 15 minutes)
- `historical_days`: Days of historical data for threshold calculation (default: 30)
- `volatility_threshold_percentile`: Percentile for normal breakout threshold (default: 95)
- `extreme_volatility_percentile`: Percentile for extreme volatility threshold (default: 98)
- `base_position_size`: Base position size as percentage of portfolio (default: 2%)
- `max_position_size`: Maximum position size (default: 5%)
- `min_confidence`: Minimum confidence threshold for signal generation (default: 60%)

## Implementation Details

### Architecture

```
VolatilityStrategy
├── analyze() - Market data analysis
│   ├── _calculate_volatility_metrics() - Volatility calculation
│   └── _identify_opportunities() - Signal identification
├── generate_signals() - Signal generation
│   ├── _calculate_position_size() - Position sizing
│   └── _calculate_risk_levels() - Risk management
└── get_parameters() - Strategy parameters
```

### Volatility Calculation

```python
# Calculate log returns for better statistical properties
df['returns'] = np.log(df['close'] / df['close'].shift(1))

# Calculate rolling volatility (annualized)
periods_per_window = max(1, volatility_window // 10)  # Assuming ~10-min intervals
df['volatility'] = df['returns'].rolling(window=periods_per_window).std() * np.sqrt(periods_per_window * 24 * 6)
```

### Signal Generation Logic

```python
# LONG signal: Volatility breakout
if current_volatility > historical_threshold and current_volatility <= extreme_threshold:
    # Generate LONG signal with confidence based on volatility magnitude

# SHORT signal: Extreme volatility
elif current_volatility > extreme_threshold:
    # Generate SHORT signal with conservative position sizing
```

## Usage Examples

### Basic Usage

```python
from src.signals.strategies.volatility_strategy import VolatilityStrategy

# Initialize strategy
strategy = VolatilityStrategy("config/strategies/volatility_strategy.json")

# Get market data
from src.data.sqlite_helper import CryptoDatabase
database = CryptoDatabase()
market_data = database.get_strategy_market_data(
    assets=['bitcoin', 'ethereum'], 
    days=30
)

# Run analysis
analysis_results = strategy.analyze(market_data)

# Generate signals
signals = strategy.generate_signals(analysis_results)
```

### Integration with Multi-Strategy Generator

```python
from src.services.multi_strategy_generator import MultiStrategyGenerator

# Configure strategy
strategy_configs = {
    'volatility_strategy': {
        'config_path': 'config/strategies/volatility_strategy.json'
    }
}

aggregator_config = {
    'strategy_weights': {'volatility_strategy': 1.0},
    'aggregation_config': {
        'max_position_size': 0.05,
        'conflict_resolution': 'weighted_average'
    }
}

# Initialize and run
generator = MultiStrategyGenerator(strategy_configs, aggregator_config)
signals = generator.generate_aggregated_signals(days=30)
```

## Configuration

### Strategy Configuration (`config/strategies/volatility_strategy.json`)

```json
{
    "assets": ["bitcoin", "ethereum"],
    "volatility_window": 15,
    "historical_days": 30,
    "volatility_threshold_percentile": 95,
    "extreme_volatility_percentile": 98,
    "base_position_size": 0.02,
    "max_position_size": 0.05,
    "min_confidence": 0.6,
    "description": "Volatility-based signal generation strategy",
    "strategy_type": "volatility_breakout",
    "risk_level": "moderate",
    "timeframe": "intraday"
}
```

## Risk Management

### Position Sizing
- **Base position size**: 2% of portfolio
- **Maximum position size**: 5% of portfolio
- **Dynamic adjustment**: Based on signal strength and confidence

### Stop Loss and Take Profit
- **Stop Loss**: 2% base stop, adjusted by volatility multiplier
- **Take Profit**: 4% base target, adjusted by volatility multiplier
- **Volatility scaling**: Higher volatility = wider stops

### Risk Controls
- **Minimum confidence**: 60% threshold for signal generation
- **Maximum risk per trade**: 2% of portfolio
- **Conservative shorts**: More conservative position sizing for SHORT signals

## Performance Considerations

### Data Requirements
- **Minimum data**: 10+ volatility observations for threshold calculation
- **Historical data**: 30 days recommended for robust thresholds
- **Data frequency**: Optimized for ~10-minute intervals

### Computational Efficiency
- **Rolling calculations**: Efficient pandas rolling operations
- **Vectorized operations**: NumPy-based calculations for speed
- **Memory management**: Minimal data copying and efficient DataFrame operations

## Testing

### Running Tests

```bash
# Test basic functionality
python3 test_volatility_strategy.py

# Test with specific configuration
python3 -c "
from src.signals.strategies.volatility_strategy import VolatilityStrategy
strategy = VolatilityStrategy('config/strategies/volatility_strategy.json')
print('Strategy initialized successfully')
"
```

### Expected Output

```
=== Volatility Strategy Test ===

Strategy initialized with parameters:
  assets: ['bitcoin', 'ethereum']
  volatility_window: 15
  historical_days: 30
  ...

Retrieved market data for 2 assets:
  bitcoin: 1529 records from 2024-01-01 to 2025-07-16
  ethereum: 1522 records from 2024-01-01 to 2025-07-16

Running volatility analysis...
Analysis complete. Found 2 opportunities

Volatility Metrics:
  bitcoin:
    Current Volatility: 45.23%
    Historical Threshold: 38.15%
    Extreme Threshold: 52.10%
    Volatility Percentile: 96.2%

Generated 2 trading signals:
  Signal 1:
    Asset: bitcoin
    Type: LONG
    Price: $107,232.89
    Strength: MODERATE
    Confidence: 0.723
    Position Size: 1.4%
    Volatility: 45.23%
    Reason: Volatility breakout: 45.23% > 38.15% threshold
```

## Integration with MTS Pipeline

### API Integration

The strategy integrates seamlessly with the existing MTS Pipeline API:

```python
# Via FastAPI endpoint
POST /signals/generate
{
    "strategies": ["volatility_strategy"],
    "assets": ["bitcoin", "ethereum"],
    "days": 30
}
```

### Database Integration

- **Data source**: Uses existing `CryptoDatabase` for market data
- **Signal storage**: Compatible with existing `TradingSignal` model
- **Historical tracking**: Integrates with backtesting framework

### Monitoring and Logging

- **Comprehensive logging**: Detailed analysis and signal generation logs
- **Performance metrics**: Volatility calculations and threshold comparisons
- **Error handling**: Robust exception handling with detailed error messages

## Best Practices

### Configuration Tuning
1. **Adjust thresholds** based on market conditions and risk tolerance
2. **Monitor performance** and adjust position sizes accordingly
3. **Test thoroughly** with historical data before live deployment

### Risk Management
1. **Start conservative** with lower position sizes
2. **Monitor volatility regimes** and adjust thresholds accordingly
3. **Use stop losses** to limit downside risk

### Performance Optimization
1. **Optimize data frequency** for your trading timeframe
2. **Monitor computational load** during high-frequency operation
3. **Cache results** when appropriate for repeated calculations

## Troubleshooting

### Common Issues

1. **Insufficient data**: Ensure at least 30 days of historical data
2. **Low signal frequency**: Adjust threshold percentiles for more/less sensitivity
3. **High false positives**: Increase confidence threshold or adjust volatility window

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger('src.signals.strategies.volatility_strategy').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Multi-timeframe analysis**: Combine multiple volatility timeframes
- **Volatility regime detection**: Identify different market volatility regimes
- **Machine learning integration**: Use ML models for threshold optimization
- **Real-time streaming**: Direct integration with WebSocket data streams

### Performance Improvements
- **GPU acceleration**: Use CUDA for large-scale volatility calculations
- **Distributed processing**: Parallel processing for multiple assets
- **Caching optimization**: Intelligent caching of volatility calculations 
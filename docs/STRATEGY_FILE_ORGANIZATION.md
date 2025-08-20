# Strategy File Organization

## Overview

This document outlines the proper organization of strategy-related files in the MTS data pipeline project.

## Directory Structure

### 1. Configuration Files (`config/strategies/`)

**Strategy Configuration JSON Files:**
- `ripple_signals.json` - Ripple (XRP) trading strategy configuration
- `eth_tops_bottoms.json` - ETH tops and bottoms detection strategy
- `volatility_strategy.json` - Volatility-based signal generation
- `mean_reversion.json` - Mean reversion strategy configuration
- `vix_correlation.json` - VIX correlation strategy configuration

**Strategy Demo Files:**
- `volatility_strategy_demo.py` - Volatility strategy demonstration script

### 2. Implementation Files (`src/signals/strategies/`)

**Core Strategy Classes:**
- `base_strategy.py` - Abstract base class for all strategies
- `strategy_registry.py` - Dynamic strategy loading and management
- `ripple_strategy.py` - Ripple (XRP) trading strategy implementation
- `eth_tops_bottoms_strategy.py` - ETH tops and bottoms strategy
- `volatility_strategy.py` - Volatility-based strategy implementation
- `mean_reversion_strategy.py` - Mean reversion strategy implementation
- `vix_correlation_strategy.py` - VIX correlation strategy implementation

### 3. Backtesting Strategy Files (`backtesting-engine/src/strategies/`)

**Backtesting-Specific Strategies:**
- `backtest_strategy_base.py` - Base class for backtesting strategies
- `buy_hold_strategy.py` - Simple buy and hold strategy for comparison
- `ripple_backtest_strategy.py` - Ripple strategy adapted for backtesting
- `eth_tops_bottoms_strategy.py` - ETH strategy adapted for backtesting

### 4. Documentation Files (`docs/`)

**Strategy Documentation:**
- `ripple_strategy_integration_summary.md` - Ripple strategy integration details
- `ripple_strategy_deployment_summary.md` - Ripple strategy deployment guide
- `eth_tops_bottoms_strategy_analysis.md` - ETH strategy analysis
- `volatility_strategy_documentation.md` - Volatility strategy documentation

### 5. Test Files

**Unit Tests:**
- `tests/test_strategy_registry.py` - Strategy registry tests
- `tests/test_multi_strategy_generator.py` - Multi-strategy generator tests
- `tests/test_mean_reversion_strategy.py` - Mean reversion strategy tests
- `tests/test_vix_correlation_strategy.py` - VIX correlation strategy tests
- `tests/test_strategy_market_data.py` - Strategy market data tests

**Backtesting Tests:**
- `backtesting-engine/tests/unit/test_backtest_strategy_base.py`
- `backtesting-engine/tests/unit/test_buy_hold_strategy.py`

## File Organization Rules

### Configuration Files
- **Location**: `config/strategies/`
- **Purpose**: JSON configuration files for strategy parameters
- **Naming**: `{strategy_name}.json`
- **Content**: Strategy parameters, thresholds, risk management settings

### Implementation Files
- **Location**: `src/signals/strategies/`
- **Purpose**: Python implementation of trading strategies
- **Naming**: `{strategy_name}_strategy.py`
- **Content**: Strategy logic, signal generation, analysis methods

### Backtesting Files
- **Location**: `backtesting-engine/src/strategies/`
- **Purpose**: Strategy implementations adapted for backtesting
- **Naming**: `{strategy_name}_backtest_strategy.py`
- **Content**: Backtesting-specific strategy logic

### Documentation Files
- **Location**: `docs/`
- **Purpose**: Strategy documentation and analysis
- **Naming**: `{strategy_name}_*.md`
- **Content**: Strategy guides, analysis reports, integration summaries

### Demo Files
- **Location**: `config/strategies/`
- **Purpose**: Demonstration scripts for strategy usage
- **Naming**: `{strategy_name}_demo.py`
- **Content**: Example usage and testing scripts

## Strategy Loading

The system uses the following pattern for loading strategies:

```python
# Configuration loading
config_path = f"config/strategies/{strategy_name}.json"

# Strategy instantiation
strategy = StrategyClass(config_path)

# Strategy registry
registry = StrategyRegistry()
registry.load_strategies_from_directory("src/signals/strategies")
```

## Migration Summary

The following files were moved during the reorganization:

### Moved to `config/strategies/`:
- `misc/volatility_strategy_demo.py` → `config/strategies/volatility_strategy_demo.py`

### Moved to `src/signals/strategies/`:
- `eth_tops_bottoms_strategy.py` → `src/signals/strategies/eth_tops_bottoms_strategy.py`

### Moved to `docs/`:
- `ripple_strategy_integration_summary.md` → `docs/ripple_strategy_integration_summary.md`
- `eth_tops_bottoms_strategy_analysis.md` → `docs/eth_tops_bottoms_strategy_analysis.md`
- `ripple_strategy_deployment_summary.md` → `docs/ripple_strategy_deployment_summary.md`
- `misc/volatility_strategy_documentation.md` → `docs/volatility_strategy_documentation.md`

## Best Practices

1. **Configuration Files**: Keep all strategy configuration JSON files in `config/strategies/`
2. **Implementation Files**: Keep all strategy Python implementations in `src/signals/strategies/`
3. **Documentation**: Keep all strategy documentation in `docs/`
4. **Tests**: Keep strategy tests in `tests/` or `backtesting-engine/tests/`
5. **Naming Convention**: Use consistent naming patterns across all file types
6. **Registry Pattern**: Use the strategy registry for dynamic loading and management

## Future Additions

When adding new strategies:

1. Create configuration file in `config/strategies/{strategy_name}.json`
2. Create implementation file in `src/signals/strategies/{strategy_name}_strategy.py`
3. Create documentation file in `docs/{strategy_name}_documentation.md`
4. Create test files in `tests/test_{strategy_name}_strategy.py`
5. Update the strategy registry if needed
6. Update this documentation 
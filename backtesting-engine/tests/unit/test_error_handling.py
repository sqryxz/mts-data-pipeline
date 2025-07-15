import pytest
from datetime import datetime
from backtesting_engine.src.core.backtest_engine import BacktestEngine
from backtesting_engine.config.backtest_settings import BacktestConfig
from backtesting_engine.src.utils.exceptions import (
    BacktestingError, DataError, StrategyError, ConfigurationError, ExecutionError
)

def test_configuration_error_no_strategies():
    """Test that ConfigurationError is raised when no strategies are provided."""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        initial_capital=100000.0,
        strategies=[],  # Empty strategies list
        symbols=["bitcoin"]
    )
    
    with pytest.raises(ConfigurationError, match="At least one strategy must be specified"):
        BacktestEngine(config)

def test_configuration_error_no_symbols():
    """Test that ConfigurationError is raised when no symbols are provided."""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        initial_capital=100000.0,
        strategies=["BuyHoldStrategy"],
        symbols=[]  # Empty symbols list
    )
    
    with pytest.raises(ConfigurationError, match="At least one symbol must be specified"):
        BacktestEngine(config)

def test_configuration_error_invalid_dates():
    """Test that ConfigurationError is raised when start date is after end date."""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 31),
        end_date=datetime(2023, 1, 1),  # End before start
        initial_capital=100000.0,
        strategies=["BuyHoldStrategy"],
        symbols=["bitcoin"]
    )
    
    with pytest.raises(ConfigurationError, match="Start date must be before end date"):
        BacktestEngine(config)

def test_configuration_error_negative_capital():
    """Test that ConfigurationError is raised when initial capital is negative."""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        initial_capital=-1000.0,  # Negative capital
        strategies=["BuyHoldStrategy"],
        symbols=["bitcoin"]
    )
    
    with pytest.raises(ConfigurationError, match="Initial capital must be positive"):
        BacktestEngine(config)

def test_strategy_error_invalid_strategy():
    """Test that StrategyError is raised for invalid strategy."""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        initial_capital=100000.0,
        strategies=["InvalidStrategy"],  # This will trigger the error in our mock
        symbols=["bitcoin"]
    )
    
    engine = BacktestEngine(config)
    with pytest.raises(StrategyError, match="Strategy 'InvalidStrategy' not found"):
        engine.run_backtest()

def test_data_error_no_symbols():
    """Test that DataError is raised when no symbols are available for data loading."""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        initial_capital=100000.0,
        strategies=["BuyHoldStrategy"],
        symbols=["bitcoin"]
    )
    
    engine = BacktestEngine(config)
    # Temporarily modify config to trigger data error
    engine.config.symbols = []
    
    with pytest.raises(DataError, match="No symbols specified for data loading"):
        engine.run_backtest()

def test_successful_backtest_with_valid_config():
    """Test that a valid configuration runs successfully."""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        initial_capital=100000.0,
        strategies=["BuyHoldStrategy"],
        symbols=["bitcoin"]
    )
    
    engine = BacktestEngine(config)
    result = engine.run_backtest()
    
    # Verify result structure
    assert result.total_return is not None
    assert result.sharpe_ratio is not None
    assert result.max_drawdown is not None
    assert result.trade_count >= 0 
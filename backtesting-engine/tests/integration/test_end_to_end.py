import pytest
from datetime import datetime, timedelta

# Import the main engine and config
from backtesting_engine.src.core.backtest_engine import BacktestEngine
from backtesting_engine.config.backtest_settings import BacktestConfig
from backtesting_engine.src.database.backtest_models import BacktestResult

@pytest.mark.integration
def test_end_to_end_backtest():
    """
    Integration test for complete backtesting pipeline.
    Tests data loading, strategy execution, and result generation.
    Dynamically selects available strategy and symbol.
    """
    # Use a 30-day period
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=29)

    # Create a temporary engine to check available resources
    temp_engine = BacktestEngine()
    # Check for available strategies
    available_strategies = getattr(temp_engine, 'get_available_strategies', lambda: [])()
    if not available_strategies:
        pytest.skip("No strategies available for testing")
    # Check for available symbols
    available_symbols = getattr(temp_engine, 'get_available_symbols', lambda s, e: [])(start_date, end_date)
    if not available_symbols:
        pytest.skip("No market data available for test period")

    # Use first available strategy and symbol
    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000.0,
        strategies=[available_strategies[0]],
        symbols=[available_symbols[0]]
    )

    # Create and run the engine
    engine = BacktestEngine(config)
    try:
        result = engine.run_backtest()
    except Exception as e:
        pytest.fail(f"Backtest failed with exception: {e}")
    finally:
        # Cleanup if needed
        if hasattr(engine, 'cleanup'):
            engine.cleanup()

    # Comprehensive result validation
    assert isinstance(result, BacktestResult), "Result should be BacktestResult instance"
    # Portfolio validation
    assert len(result.portfolio_values) >= 1, "Should have at least initial portfolio value"
    assert result.portfolio_values[0] == config.initial_capital, "Should start with initial capital"
    # Trade validation (should have at least 1 trade)
    assert result.trade_count >= 1, "Should have at least one trade"
    assert len(result.trade_history) >= 1, "Trade history should match trade count"
    assert len(result.trade_history) == result.trade_count, "Trade history length should match count"
    # Metrics validation
    assert isinstance(result.total_return, (int, float)), "Total return should be numeric"
    assert isinstance(result.sharpe_ratio, (int, float)), "Sharpe ratio should be numeric"
    assert isinstance(result.max_drawdown, (int, float)), "Max drawdown should be numeric"
    # Logical constraints
    assert -1.0 <= result.max_drawdown <= 0.0, "Max drawdown should be between -100% and 0%"
    # Trade data integrity
    for i, trade in enumerate(result.trade_history):
        assert 'symbol' in trade, f"Trade {i} missing symbol"
        assert 'action' in trade, f"Trade {i} missing action"
        assert 'quantity' in trade, f"Trade {i} missing quantity"
        assert 'price' in trade, f"Trade {i} missing price"
        assert trade['action'] in ['buy', 'sell', 'BUY', 'SELL'], f"Trade {i} has invalid action: {trade['action']}"
        assert trade['quantity'] > 0, f"Trade {i} has invalid quantity: {trade['quantity']}"
        assert trade['price'] > 0, f"Trade {i} has invalid price: {trade['price']}"

@pytest.mark.integration 
def test_backtest_with_invalid_config():
    """Test that engine properly handles invalid configurations."""
    # Test with future dates and invalid strategy/symbol
    config = BacktestConfig(
        start_date=datetime(2030, 1, 1),  # Future date
        end_date=datetime(2030, 1, 31),
        initial_capital=100000.0,
        strategies=["NonExistentStrategy"],
        symbols=["invalid_symbol"]
    )
    engine = BacktestEngine(config)
    with pytest.raises((ValueError, RuntimeError)):
        engine.run_backtest() 
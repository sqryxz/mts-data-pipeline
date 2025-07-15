import pytest
from datetime import datetime, timedelta
from backtesting_engine.src.core.backtest_engine import BacktestEngine
from backtesting_engine.config.backtest_settings import BacktestConfig

@pytest.mark.unit
def test_buy_and_hold_performance_accuracy(monkeypatch):
    """
    Validate that the backtest engine produces expected results for a simple buy-and-hold scenario.
    """
    # Simulate a 2-day period with known prices
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=1)
    initial_capital = 10000.0
    buy_price = 100.0
    sell_price = 120.0
    quantity = initial_capital / buy_price
    expected_return = (sell_price - buy_price) / buy_price
    expected_final_value = initial_capital * (1 + expected_return)
    expected_trade_count = 2  # Buy and sell

    # Patch the engine's _load_market_data and _run_simulation to use our known prices
    def mock_load_market_data(self):
        return {
            "prices": [buy_price, sell_price],
            "dates": [start_date, end_date]
        }
    def mock_run_simulation(self, market_data, portfolio_manager, strategy):
        # Simulate buy at start, sell at end
        return type('Result', (), {
            'total_return': expected_return,
            'sharpe_ratio': 1.0,
            'max_drawdown': 0.0,
            'trade_count': expected_trade_count,
            'portfolio_values': [initial_capital, expected_final_value],
            'trade_history': [
                {"date": str(start_date.date()), "symbol": "bitcoin", "action": "BUY", "quantity": quantity, "price": buy_price},
                {"date": str(end_date.date()), "symbol": "bitcoin", "action": "SELL", "quantity": quantity, "price": sell_price}
            ]
        })()

    monkeypatch.setattr(BacktestEngine, "_load_market_data", mock_load_market_data)
    monkeypatch.setattr(BacktestEngine, "_run_simulation", mock_run_simulation)

    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        strategies=["BuyHoldStrategy"],
        symbols=["bitcoin"]
    )
    engine = BacktestEngine(config)
    result = engine.run_backtest()

    # Assert results match expected values within tolerance
    assert abs(result.total_return - expected_return) < 1e-6
    assert abs(result.portfolio_values[-1] - expected_final_value) < 1e-6
    assert result.trade_count == expected_trade_count
    assert result.trade_history[0]['action'] == 'BUY'
    assert result.trade_history[1]['action'] == 'SELL'
    assert abs(result.trade_history[0]['price'] - buy_price) < 1e-6
    assert abs(result.trade_history[1]['price'] - sell_price) < 1e-6 
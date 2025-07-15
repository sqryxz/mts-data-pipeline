from datetime import datetime, timedelta
from backtesting_engine.src.core.backtest_engine import BacktestEngine
from backtesting_engine.config.backtest_settings import BacktestConfig
from backtesting_engine.src.database.backtest_models import BacktestResult

if __name__ == "__main__":
    # Example: 30-day backtest for bitcoin using BuyHoldStrategy
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=29)
    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000.0,
        strategies=["BuyHoldStrategy"],
        symbols=["bitcoin"]
    )
    engine = BacktestEngine(config)
    result = engine.run_backtest()
    print("\nSimple Backtest Example Results:")
    print(f"  Strategy: {config.strategies[0]}")
    print(f"  Symbol: {config.symbols[0]}")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Initial Capital: ${config.initial_capital:,.2f}")
    print(f"  Total Return: {result.total_return:.2%}")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
    print(f"  Max Drawdown: {result.max_drawdown:.2%}")
    print(f"  Trade Count: {result.trade_count}") 
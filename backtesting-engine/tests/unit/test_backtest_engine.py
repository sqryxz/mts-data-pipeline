import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.core.backtest_engine import BacktestEngine

class DummyPortfolioManager:
    def update_portfolio(self, event):
        pass
    def get_portfolio_value(self):
        return 100000.0

class DummyExecutionHandler:
    def execute_order(self, order):
        pass
    def get_fill_cost(self, order):
        return 0.0

def test_backtest_engine_init():
    pm = DummyPortfolioManager()
    eh = DummyExecutionHandler()
    engine = BacktestEngine(portfolio_manager=pm, execution_handler=eh)
    assert engine.event_manager is not None
    assert engine.state_manager is not None
    assert engine.portfolio_manager is pm
    assert engine.execution_handler is eh
    assert engine.is_ready() is True

def test_type_validation():
    class BadPortfolio:
        pass
    class BadExecution:
        pass
    with pytest.raises(TypeError):
        BacktestEngine(portfolio_manager=BadPortfolio(), execution_handler=DummyExecutionHandler())
    with pytest.raises(TypeError):
        BacktestEngine(portfolio_manager=DummyPortfolioManager(), execution_handler=BadExecution())

def test_run_backtest_param_validation():
    engine = BacktestEngine(portfolio_manager=DummyPortfolioManager(), execution_handler=DummyExecutionHandler())
    with pytest.raises(ValueError, match="data_source is required"):
        engine.run_backtest(None, "strategy")
    with pytest.raises(ValueError, match="strategy is required"):
        engine.run_backtest("data", None)
    with pytest.raises(ValueError, match="initial_capital must be positive"):
        engine.run_backtest("data", "strategy", initial_capital=0)

def test_run_backtest_success():
    engine = BacktestEngine(portfolio_manager=DummyPortfolioManager(), execution_handler=DummyExecutionHandler())
    result = engine.run_backtest("data", "strategy", initial_capital=100000.0)
    assert result["status"] == "completed"
    assert result["initial_capital"] == 100000.0
    assert result["final_value"] == 100000.0
    assert result["total_return"] == 0.0
    assert isinstance(result["trades"], list)
    assert isinstance(result["performance_metrics"], dict) 
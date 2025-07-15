from datetime import datetime, timedelta
from src.analytics.performance_calculator import PerformanceCalculator
import numpy as np

def test_add_portfolio_value_and_returns():
    calc = PerformanceCalculator()
    base = datetime(2024, 1, 1)
    calc.add_portfolio_value(base, 100.0)
    calc.add_portfolio_value(base + timedelta(days=1), 110.0)
    calc.add_portfolio_value(base + timedelta(days=2), 121.0)
    assert len(calc.portfolio_values) == 3
    assert len(calc.returns) == 2
    # First return: (110-100)/100 = 0.1
    assert abs(calc.returns[0] - 0.1) < 1e-8
    # Second return: (121-110)/110 = 0.1
    assert abs(calc.returns[1] - 0.1) < 1e-8

def test_total_return():
    calc = PerformanceCalculator()
    base = datetime(2024, 1, 1)
    calc.add_portfolio_value(base, 100.0)
    calc.add_portfolio_value(base + timedelta(days=1), 110.0)
    calc.add_portfolio_value(base + timedelta(days=2), 121.0)
    total_ret = calc.calculate_total_return()
    # (121-100)/100 = 0.21
    assert abs(total_ret - 0.21) < 1e-8

def test_total_return_not_enough_data():
    calc = PerformanceCalculator()
    assert calc.calculate_total_return() is None
    calc.add_portfolio_value(datetime(2024, 1, 1), 100.0)
    assert calc.calculate_total_return() is None

def test_sharpe_ratio():
    calc = PerformanceCalculator()
    # Use non-constant returns to ensure std != 0
    calc.returns = [0.01, 0.02, 0.015, 0.005, 0.012]
    sharpe = calc.calculate_sharpe_ratio(risk_free_rate=0.0, periods_per_year=252)
    assert sharpe is not None
    # Should be positive
    assert sharpe > 0

def test_sharpe_ratio_not_enough_data():
    calc = PerformanceCalculator()
    assert calc.calculate_sharpe_ratio() is None
    calc.returns = [0.01]
    assert calc.calculate_sharpe_ratio() is None

def test_max_drawdown():
    calc = PerformanceCalculator()
    vals = [100, 120, 110, 90, 95, 130]
    calc.portfolio_values = vals
    mdd = calc.calculate_max_drawdown()
    # Max drawdown: from 120 to 90 = -25%
    assert mdd is not None
    assert abs(mdd['max_drawdown'] - 0.25) < 1e-8
    assert mdd['peak'] == 120
    assert mdd['trough'] == 90
    # Duration is trough_idx - peak_idx = 3-1 = 2
    assert mdd['duration'] == 2

def test_max_drawdown_not_enough_data():
    calc = PerformanceCalculator()
    assert calc.calculate_max_drawdown() is None
    calc.portfolio_values = [100]
    assert calc.calculate_max_drawdown() is None 
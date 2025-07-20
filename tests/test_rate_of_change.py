from src.analytics.macro.rate_of_change import RateOfChangeCalculator, ZeroHandlingStrategy
import pytest

def test_calculate_roc_normal():
    calc = RateOfChangeCalculator()
    assert calc.calculate_roc(110, 100) == 10.0
    assert calc.calculate_roc(90, 100) == -10.0

def test_calculate_roc_zero_none():
    calc = RateOfChangeCalculator(ZeroHandlingStrategy.RETURN_NONE)
    assert calc.calculate_roc(100, 0) is None

def test_calculate_roc_zero_raise():
    calc = RateOfChangeCalculator(ZeroHandlingStrategy.RAISE_ERROR)
    with pytest.raises(ZeroDivisionError):
        calc.calculate_roc(100, 0)

def test_calculate_roc_zero_inf():
    calc = RateOfChangeCalculator(ZeroHandlingStrategy.RETURN_INF)
    assert calc.calculate_roc(100, 0) == float('inf')
    assert calc.calculate_roc(-100, 0) == float('-inf')
    assert calc.calculate_roc(0, 0) == 0.0

def test_calculate_roc_zero_absolute():
    calc = RateOfChangeCalculator(ZeroHandlingStrategy.USE_ABSOLUTE)
    assert calc.calculate_roc(42, 0) == 42

def test_calculate_roc_invalid_inputs():
    calc = RateOfChangeCalculator()
    with pytest.raises(ValueError):
        calc.calculate_roc(None, 100)
    with pytest.raises(ValueError):
        calc.calculate_roc(100, None)
    with pytest.raises(ValueError):
        calc.calculate_roc(float('nan'), 100)
    with pytest.raises(ValueError):
        calc.calculate_roc(100, float('inf'))

def test_calculate_roc_series():
    calc = RateOfChangeCalculator()
    values = [100, 110, 105, 120, 115]
    expected = [None, 10.0, -4.55, 14.29, -4.17]
    result = calc.calculate_roc_series(values)
    for r, e in zip(result, expected):
        if r is None or e is None:
            assert r is e
        else:
            assert abs(r - e) < 0.01

def test_calculate_annualized_roc():
    calc = RateOfChangeCalculator()
    # 20% over 30 periods, annualized to 252 periods
    result = calc.calculate_annualized_roc(120, 100, 30, 252)
    assert isinstance(result, float)
    # Invalid periods
    with pytest.raises(ValueError):
        calc.calculate_annualized_roc(120, 100, 0)
    # Invalid values
    assert calc.calculate_annualized_roc(None, 100, 30) is None
    assert calc.calculate_annualized_roc(120, None, 30) is None
    assert calc.calculate_annualized_roc(120, 0, 30) is None

def test_get_roc_category():
    calc = RateOfChangeCalculator()
    assert calc.get_roc_category(None) == "Invalid"
    assert calc.get_roc_category(0) == "No Change"
    assert calc.get_roc_category(0.5) == "Minimal Increase"
    assert calc.get_roc_category(-0.5) == "Minimal Decrease"
    assert calc.get_roc_category(3) == "Small Increase"
    assert calc.get_roc_category(-3) == "Small Decrease"
    assert calc.get_roc_category(10) == "Moderate Increase"
    assert calc.get_roc_category(-10) == "Moderate Decrease"
    assert calc.get_roc_category(20) == "Large Increase"
    assert calc.get_roc_category(-20) == "Large Decrease"
    assert calc.get_roc_category(50) == "Extreme Increase"
    assert calc.get_roc_category(-50) == "Extreme Decrease" 
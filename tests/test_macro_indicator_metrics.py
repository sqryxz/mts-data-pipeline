from src.analytics.models.analytics_models import MacroIndicatorMetrics
from datetime import datetime
import pytest

def test_macro_indicator_metrics_instantiation():
    now = int(datetime(2024, 7, 10, 12, 0).timestamp())
    metrics = MacroIndicatorMetrics(
        indicator='VIX',
        timestamp=now,
        timeframe='1h',
        current_value=15.0,
        rate_of_change=0.05,
        z_score=1.2,
        percentile_rank=85.0,
        mean=14.5,
        std_dev=0.5,
        lookback_period=30
    )
    assert metrics.indicator == 'VIX'
    assert metrics.timeframe == '1h'
    assert metrics.timestamp == now
    assert metrics.to_datetime() == datetime(2024, 7, 10, 12, 0)
    assert not metrics.is_outlier()
    assert str(metrics).startswith('VIX (1h) at 2024-07-10 12:00')

def test_macro_indicator_metrics_validation():
    now = int(datetime.now().timestamp())
    with pytest.raises(ValueError):
        MacroIndicatorMetrics(
            indicator='VIX',
            timestamp=now,
            timeframe='1h',
            current_value=15.0,
            rate_of_change=0.05,
            z_score=1.2,
            percentile_rank=120.0,  # Invalid
            mean=14.5,
            std_dev=0.5,
            lookback_period=30
        )
    with pytest.raises(ValueError):
        MacroIndicatorMetrics(
            indicator='VIX',
            timestamp=now,
            timeframe='1h',
            current_value=15.0,
            rate_of_change=0.05,
            z_score=1.2,
            percentile_rank=85.0,
            mean=14.5,
            std_dev=-1.0,  # Invalid
            lookback_period=30
        )
    with pytest.raises(ValueError):
        MacroIndicatorMetrics(
            indicator='VIX',
            timestamp=now,
            timeframe='1h',
            current_value=15.0,
            rate_of_change=0.05,
            z_score=1.2,
            percentile_rank=85.0,
            mean=14.5,
            std_dev=0.5,
            lookback_period=0  # Invalid
        ) 
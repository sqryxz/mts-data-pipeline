# Signal generation module 

from .signal_aggregator import SignalAggregator
from .strategies.base_strategy import SignalStrategy
from .strategies.strategy_registry import StrategyRegistry
# BacktestInterface imports removed to avoid circular dependency
# Import directly when needed

__all__ = [
    'SignalAggregator',
    'SignalStrategy',
    'StrategyRegistry'
] 
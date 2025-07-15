import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.strategies.backtest_strategy_base import BacktestStrategy, MarketEvent, Portfolio, Signal
from src.events.signal_event import SignalEvent
from typing import List
from datetime import datetime

class DummyMarketEvent:
    def __init__(self, timestamp, symbol, price):
        self.timestamp = timestamp
        self.symbol = symbol
        self.price = price

class DummyPortfolio:
    def __init__(self, balance, positions):
        self.balance = balance
        self.positions = positions

class DummySignal:
    def __init__(self, symbol, action, quantity, strength=None):
        self.symbol = symbol
        self.action = action
        self.quantity = quantity
        self.strength = strength

class DummyStrategy(BacktestStrategy):
    def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
        return [DummySignal(market_event.symbol, "BUY", 1.0)]
    def get_name(self) -> str:
        return "Dummy"

def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        BacktestStrategy()

def test_concrete_strategy():
    portfolio = DummyPortfolio(balance=1000.0, positions={"BTC": 1})
    strat = DummyStrategy(portfolio=portfolio)
    assert strat.get_name() == "Dummy"
    assert strat.portfolio.balance == 1000.0
    event = DummyMarketEvent(timestamp=datetime(2024, 1, 1), symbol="BTC", price=50000.0)
    signals = strat.generate_signals(event)
    assert isinstance(signals, list)
    assert signals[0].symbol == "BTC"
    assert signals[0].action == "BUY"
    assert signals[0].quantity == 1.0

def test_process_market_data():
    strat = DummyStrategy()
    event = DummyMarketEvent(timestamp=datetime(2024, 1, 1), symbol="BTC", price=50000.0)
    signal_events = strat.process_market_data(event)
    assert isinstance(signal_events, list)
    assert len(signal_events) == 1
    sig = signal_events[0]
    assert isinstance(sig, SignalEvent)
    assert sig.symbol == "BTC"
    assert sig.signal_type == "BUY"
    assert sig.strength == 1.0
    assert sig.strategy == "Dummy"
    assert sig.timestamp == datetime(2024, 1, 1)

def test_process_market_data_custom_strength():
    class CustomStrengthStrategy(BacktestStrategy):
        def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
            return [DummySignal(market_event.symbol, "BUY", 1.0, strength=0.42)]
        def get_name(self) -> str:
            return "CustomStrength"
    strat = CustomStrengthStrategy()
    event = DummyMarketEvent(timestamp=datetime(2024, 1, 2), symbol="ETH", price=3000.0)
    signal_events = strat.process_market_data(event)
    assert len(signal_events) == 1
    sig = signal_events[0]
    assert sig.strength == 0.42
    assert sig.symbol == "ETH"
    assert sig.signal_type == "BUY"
    assert sig.strategy == "CustomStrength"
    assert sig.timestamp == datetime(2024, 1, 2)

def test_process_market_data_missing_symbol():
    class BadSignal:
        def __init__(self):
            self.action = "BUY"
            self.quantity = 1.0
    class BadStrategy(BacktestStrategy):
        def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
            return [BadSignal()]
        def get_name(self) -> str:
            return "Bad"
    strat = BadStrategy()
    event = DummyMarketEvent(timestamp=datetime(2024, 1, 1), symbol="BTC", price=50000.0)
    with pytest.raises(AttributeError, match="missing 'symbol'"):
        strat.process_market_data(event)

def test_process_market_data_missing_action():
    class BadSignal:
        def __init__(self):
            self.symbol = "BTC"
            self.quantity = 1.0
    class BadStrategy(BacktestStrategy):
        def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
            return [BadSignal()]
        def get_name(self) -> str:
            return "Bad"
    strat = BadStrategy()
    event = DummyMarketEvent(timestamp=datetime(2024, 1, 1), symbol="BTC", price=50000.0)
    with pytest.raises(AttributeError, match="missing 'action'"):
        strat.process_market_data(event)

def test_process_market_data_none_event():
    strat = DummyStrategy()
    with pytest.raises(ValueError, match="Market event cannot be None"):
        strat.process_market_data(None) 
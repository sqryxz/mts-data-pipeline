import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.strategies.buy_hold_strategy import BuyAndHoldStrategy, BuyAndHoldSignal
from datetime import datetime

class DummyMarketEvent:
    def __init__(self, timestamp, symbol, price):
        self.timestamp = timestamp
        self.symbol = symbol
        self.price = price

def test_buy_and_hold_signal_once():
    strat = BuyAndHoldStrategy(symbol="BTC", quantity=2.0)
    event1 = DummyMarketEvent(timestamp=datetime(2024, 1, 1), symbol="BTC", price=50000.0)
    event2 = DummyMarketEvent(timestamp=datetime(2024, 1, 2), symbol="BTC", price=51000.0)
    # First event: should generate BUY
    signals1 = strat.generate_signals(event1)
    assert len(signals1) == 1
    sig = signals1[0]
    assert isinstance(sig, BuyAndHoldSignal)
    assert sig.symbol == "BTC"
    assert sig.action == "BUY"
    assert sig.quantity == 2.0
    # Second event: should generate nothing
    signals2 = strat.generate_signals(event2)
    assert signals2 == []

def test_buy_and_hold_wrong_symbol():
    strat = BuyAndHoldStrategy(symbol="BTC", quantity=1.0)
    event = DummyMarketEvent(timestamp=datetime(2024, 1, 1), symbol="ETH", price=3000.0)
    signals = strat.generate_signals(event)
    assert signals == []

def test_get_name():
    strat = BuyAndHoldStrategy(symbol="BTC")
    assert strat.get_name() == "BuyAndHold(BTC)" 
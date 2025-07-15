import pytest
from datetime import datetime
import math
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.events.fill_event import FillEvent

class TestFillEvent:
    def test_valid_fill_event_buy(self):
        event = FillEvent(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSD",
            quantity=2.0,
            fill_price=30000.0,
            commission=10.0,
            direction="BUY"
        )
        assert event.symbol == "BTCUSD"
        assert event.quantity == 2.0
        assert event.fill_price == 30000.0
        assert event.commission == 10.0
        assert event.direction == "BUY"
        assert event.validate() is True
        assert event.total_cost() == 2.0 * 30000.0 + 10.0
        assert event.net_quantity() == 2.0

    def test_valid_fill_event_sell(self):
        event = FillEvent(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSD",
            quantity=2.0,
            fill_price=30000.0,
            commission=10.0,
            direction="SELL"
        )
        assert event.symbol == "BTCUSD"
        assert event.quantity == 2.0
        assert event.fill_price == 30000.0
        assert event.commission == 10.0
        assert event.direction == "SELL"
        assert event.validate() is True
        assert event.total_cost() == 2.0 * 30000.0 - 10.0
        assert event.net_quantity() == -2.0

    @pytest.mark.parametrize("quantity", [0, -1, -0.01, float('inf'), float('nan')])
    def test_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            FillEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                quantity=quantity,
                fill_price=30000.0,
                commission=10.0,
                direction="BUY"
            )

    @pytest.mark.parametrize("fill_price", [0, -1, -0.01, float('inf'), float('nan')])
    def test_invalid_fill_price(self, fill_price):
        with pytest.raises(ValueError):
            FillEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                quantity=1.0,
                fill_price=fill_price,
                commission=10.0,
                direction="SELL"
            )

    @pytest.mark.parametrize("commission", [-1, float('inf'), float('nan')])
    def test_invalid_commission(self, commission):
        with pytest.raises(ValueError):
            FillEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                quantity=1.0,
                fill_price=30000.0,
                commission=commission,
                direction="BUY"
            )

    @pytest.mark.parametrize("direction", ["", None, "HOLD", "buyy", 123])
    def test_invalid_direction(self, direction):
        with pytest.raises(ValueError):
            FillEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                quantity=1.0,
                fill_price=30000.0,
                commission=10.0,
                direction=direction
            ) 
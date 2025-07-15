import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.events.order_event import OrderEvent

class TestOrderEvent:
    def test_valid_order_event(self):
        event = OrderEvent(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSD",
            order_type="MARKET",
            quantity=1.5,
            direction="BUY"
        )
        assert event.symbol == "BTCUSD"
        assert event.order_type == "MARKET"
        assert event.quantity == 1.5
        assert event.direction == "BUY"
        assert event.validate() is True

    @pytest.mark.parametrize("order_type", ["LIMIT", "", None])
    def test_invalid_order_type(self, order_type):
        with pytest.raises(ValueError):
            OrderEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                order_type=order_type,
                quantity=1.0,
                direction="BUY"
            )

    @pytest.mark.parametrize("direction", ["LONG", "", None])
    def test_invalid_direction(self, direction):
        with pytest.raises(ValueError):
            OrderEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                order_type="MARKET",
                quantity=1.0,
                direction=direction
            )

    @pytest.mark.parametrize("quantity", [0, -1, -0.01])
    def test_non_positive_quantity(self, quantity):
        with pytest.raises(ValueError):
            OrderEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                order_type="MARKET",
                quantity=quantity,
                direction="SELL"
            ) 
import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.events.order_event import OrderEvent
from src.execution.execution_handler import ExecutionHandler

class TestExecutionHandler:
    def setup_method(self):
        self.handler = ExecutionHandler()
        self.market_price = 20000.0

    def test_execute_market_order_buy(self):
        order = OrderEvent(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSD",
            order_type="MARKET",
            quantity=2.0,
            direction="BUY"
        )
        fill = self.handler.execute_market_order(order, self.market_price)
        assert fill.symbol == "BTCUSD"
        assert fill.quantity == 2.0
        assert fill.fill_price == self.market_price
        assert fill.direction == "BUY"
        expected_commission = 2.0 * self.market_price * self.handler.FIXED_COMMISSION_RATE
        assert abs(fill.commission - expected_commission) < 1e-8
        assert fill.total_cost() == 2.0 * self.market_price + expected_commission
        assert fill.net_quantity() == 2.0

    def test_execute_market_order_sell(self):
        order = OrderEvent(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSD",
            order_type="MARKET",
            quantity=3.0,
            direction="SELL"
        )
        fill = self.handler.execute_market_order(order, self.market_price)
        assert fill.symbol == "BTCUSD"
        assert fill.quantity == 3.0
        assert fill.fill_price == self.market_price
        assert fill.direction == "SELL"
        expected_commission = 3.0 * self.market_price * self.handler.FIXED_COMMISSION_RATE
        assert abs(fill.commission - expected_commission) < 1e-8
        assert fill.total_cost() == 3.0 * self.market_price - expected_commission
        assert fill.net_quantity() == -3.0

    @pytest.mark.parametrize("bad_type", ["INVALID_TYPE", "STOP_LIMIT_IF_TOUCHED", "FOO"])
    def test_unsupported_order_types(self, bad_type):
        """Test that unsupported order types raise a ValueError at OrderEvent construction.
        TODO: Update to use enums if/when order_type uses Enum in the codebase.
        """
        with pytest.raises(ValueError, match="order_type must be one of"):
            OrderEvent(
                timestamp=datetime(2024, 1, 1, 12, 0),
                symbol="BTCUSD",
                order_type=bad_type,
                quantity=1.0,
                direction="BUY"
            )

    @pytest.mark.parametrize("bad_price", [0, -1, -0.01, "abc", None])
    def test_invalid_market_price(self, bad_price):
        order = OrderEvent(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSD",
            order_type="MARKET",
            quantity=1.0,
            direction="BUY"
        )
        with pytest.raises(ValueError):
            self.handler.execute_market_order(order, bad_price) 
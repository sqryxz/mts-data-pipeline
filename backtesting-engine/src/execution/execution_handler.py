from datetime import datetime
from ..events.order_event import OrderEvent
from ..events.fill_event import FillEvent

class ExecutionHandler:
    FIXED_COMMISSION_RATE = 0.001  # 0.1%

    def execute_market_order(self, order_event: OrderEvent, market_price: float) -> FillEvent:
        if order_event.order_type != "MARKET":
            raise ValueError(f"Unsupported order type: {order_event.order_type}")
        if not isinstance(market_price, (int, float)) or market_price <= 0:
            raise ValueError("market_price must be a positive number")
        commission = abs(order_event.quantity) * market_price * self.FIXED_COMMISSION_RATE
        fill_event = FillEvent(
            timestamp=datetime.now(),
            symbol=order_event.symbol,
            quantity=order_event.quantity,
            fill_price=market_price,
            commission=commission,
            direction=order_event.direction
        )
        return fill_event 
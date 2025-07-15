from datetime import datetime
from .base_event import BaseEvent

class OrderEvent(BaseEvent):
    VALID_ORDER_TYPES = {"MARKET"}
    VALID_DIRECTIONS = {"BUY", "SELL"}

    def __init__(self, timestamp: datetime, symbol: str, order_type: str, quantity: float, direction: str):
        self._validate_inputs(symbol, order_type, quantity, direction)
        super().__init__(timestamp, event_type="ORDER")
        self.symbol = symbol.strip().upper()
        self.order_type = order_type.upper().strip()
        self.quantity = float(quantity)
        self.direction = direction.upper().strip()

    def _validate_inputs(self, symbol, order_type, quantity, direction):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")
        if not isinstance(order_type, str) or not order_type.strip():
            raise ValueError("order_type must be a non-empty string")
        if order_type.upper().strip() not in self.VALID_ORDER_TYPES:
            raise ValueError(f"order_type must be one of {self.VALID_ORDER_TYPES}")
        if not isinstance(quantity, (int, float)) or float(quantity) <= 0:
            raise ValueError("quantity must be a positive number")
        if not isinstance(direction, str) or not direction.strip():
            raise ValueError("direction must be a non-empty string")
        if direction.upper().strip() not in self.VALID_DIRECTIONS:
            raise ValueError(f"direction must be one of {self.VALID_DIRECTIONS}")

    def validate(self) -> bool:
        try:
            self._validate_inputs(self.symbol, self.order_type, self.quantity, self.direction)
            return True
        except ValueError:
            return False 
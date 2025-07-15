from datetime import datetime
from math import isfinite
from .base_event import BaseEvent

class FillEvent(BaseEvent):
    VALID_DIRECTIONS = {"BUY", "SELL"}
    
    def __init__(self, timestamp: datetime, symbol: str, quantity: float, 
                 fill_price: float, commission: float, direction: str):
        self._validate_inputs(symbol, quantity, fill_price, commission, direction)
        super().__init__(timestamp, event_type="FILL")
        self.symbol = symbol.strip().upper()
        self.quantity = abs(float(quantity))  # Always positive
        self.fill_price = float(fill_price)
        self.commission = float(commission)
        self.direction = direction.upper().strip()

    def _validate_inputs(self, symbol, quantity, fill_price, commission, direction):
        # Symbol validation
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")
        
        # Quantity validation
        if not isinstance(quantity, (int, float)):
            raise ValueError("quantity must be numeric")
        qty_float = float(quantity)
        if not isfinite(qty_float) or qty_float <= 0:
            raise ValueError("quantity must be a positive finite number")
        
        # Fill price validation
        if not isinstance(fill_price, (int, float)):
            raise ValueError("fill_price must be numeric")
        price_float = float(fill_price)
        if not isfinite(price_float) or price_float <= 0:
            raise ValueError("fill_price must be a positive finite number")
        
        # Commission validation
        if not isinstance(commission, (int, float)):
            raise ValueError("commission must be numeric")
        comm_float = float(commission)
        if not isfinite(comm_float) or comm_float < 0:
            raise ValueError("commission must be a non-negative finite number")
        
        # Direction validation
        if not isinstance(direction, str) or not direction.strip():
            raise ValueError("direction must be a non-empty string")
        if direction.upper().strip() not in self.VALID_DIRECTIONS:
            raise ValueError(f"direction must be one of {self.VALID_DIRECTIONS}")

    def total_cost(self) -> float:
        """Return the total cost/proceeds of the fill including commission."""
        base_amount = self.quantity * self.fill_price
        if self.direction == "BUY":
            # Cost = amount paid + commission
            return base_amount + self.commission
        else:  # SELL
            # Proceeds = amount received - commission
            return base_amount - self.commission
    
    def net_quantity(self) -> float:
        """Return signed quantity based on direction."""
        return self.quantity if self.direction == "BUY" else -self.quantity

    def validate(self) -> bool:
        try:
            self._validate_inputs(self.symbol, self.quantity, self.fill_price, 
                                self.commission, self.direction)
            return True
        except ValueError:
            return False 
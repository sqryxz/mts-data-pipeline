import numbers
from datetime import datetime

class StateManager:
    def __init__(self):
        self.current_time = None
        self.portfolio_state = {}
        self.current_prices = {}

    def reset(self):
        """Reset the state manager to its initial state."""
        self.current_time = None
        self.portfolio_state.clear()
        self.current_prices.clear()

    def update_state(self, event):
        if event is None:
            raise ValueError("Event cannot be None")
        # Update current_time with validation
        timestamp = getattr(event, 'timestamp', None)
        if timestamp is not None:
            if isinstance(timestamp, (numbers.Number, datetime)):
                self.current_time = timestamp
            else:
                raise ValueError("Event timestamp must be numeric or datetime")
        # Handle market events
        event_type = getattr(event, 'event_type', '')
        if isinstance(event_type, str) and event_type.upper() == 'MARKET':
            symbol = getattr(event, 'symbol', None)
            price = getattr(event, 'close_price', None)
            # Validate symbol
            if symbol is not None and str(symbol).strip():
                # Validate price
                if price is not None and isinstance(price, numbers.Number) and price >= 0:
                    self.current_prices[str(symbol).strip()] = float(price)
                elif price is not None:
                    raise ValueError(f"Invalid price for {symbol}: {price}") 
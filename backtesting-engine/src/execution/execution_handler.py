from datetime import datetime
from ..events.order_event import OrderEvent
from ..events.fill_event import FillEvent

class ExecutionHandler:
    def __init__(self, commission_rate: float = 0.001, slippage: float = 0.0005):
        self.commission_rate = commission_rate
        self.slippage = slippage

    def execute_order(self, order: dict, market_price: float):
        """Execute an order and return a fill event."""
        try:
            symbol = order['symbol']
            side = order['side']
            quantity = order['quantity']
            
            # Apply slippage
            if side == 'BUY':
                fill_price = market_price * (1 + self.slippage)
            else:  # SELL
                fill_price = market_price * (1 - self.slippage)
            
            # Calculate commission
            commission = abs(quantity) * fill_price * self.commission_rate
            
            # Create fill event
            class FillEventImpl:
                def __init__(self, timestamp, symbol, quantity, price, commission):
                    self.timestamp = timestamp
                    self.symbol = symbol
                    self.quantity = quantity
                    self.price = price
                    self.commission = commission
            
            return FillEventImpl(
                timestamp=datetime.now(),
                symbol=symbol,
                quantity=quantity,
                price=fill_price,
                commission=commission
            )
            
        except Exception as e:
            print(f"Error executing order: {e}")
            return None 
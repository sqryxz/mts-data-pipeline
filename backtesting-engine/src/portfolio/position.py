class Position:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.quantity = 0.0
        self.average_cost = 0.0
        self.unrealized_pnl = 0.0
        self._epsilon = 1e-8

    def update_position(self, quantity_change: float, price: float, current_price: float = None):
        # Input validation
        if quantity_change == 0:
            return
        if price <= 0:
            raise ValueError("Trade price must be positive")
        if current_price is not None and current_price <= 0:
            raise ValueError("Current price must be positive")

        prev_quantity = self.quantity
        new_quantity = self.quantity + quantity_change

        # Position flip logic
        if abs(new_quantity) < self._epsilon:
            # Position closed
            self.quantity = 0.0
            self.average_cost = 0.0
        elif prev_quantity == 0 or (prev_quantity > 0 and new_quantity < -self._epsilon) or (prev_quantity < 0 and new_quantity > self._epsilon):
            # New position or flip: set average cost to new entry price
            self.quantity = new_quantity
            self.average_cost = price
        elif (prev_quantity > 0 and quantity_change > 0) or (prev_quantity < 0 and quantity_change < 0):
            # Adding to existing position (same direction)
            total_cost = self.average_cost * abs(prev_quantity) + price * abs(quantity_change)
            self.quantity = new_quantity
            if abs(self.quantity) < self._epsilon:
                self.average_cost = 0.0
            else:
                self.average_cost = total_cost / abs(self.quantity)
        else:
            # Reducing position (not flipping)
            self.quantity = new_quantity
            # average_cost unchanged

        # Update unrealized PnL if current price provided
        if current_price is not None and abs(self.quantity) > self._epsilon:
            if self.quantity > 0:
                self.unrealized_pnl = (current_price - self.average_cost) * self.quantity
            else:
                self.unrealized_pnl = (self.average_cost - current_price) * abs(self.quantity)
        else:
            self.unrealized_pnl = 0.0 
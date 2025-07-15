from .position import Position

class PortfolioManager:
    def __init__(self, initial_capital: float):
        if not isinstance(initial_capital, (int, float)) or initial_capital <= 0:
            raise ValueError("initial_capital must be a positive number")
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.positions = {}  # symbol -> Position
        self._epsilon = 1e-10

    def get_portfolio_value(self, current_prices: dict) -> float:
        if not isinstance(current_prices, dict):
            raise ValueError("current_prices must be a dictionary")
        total = self.cash_balance
        missing_prices = []
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol)
            if price is None:
                missing_prices.append(symbol)
                continue
            if not isinstance(price, (int, float)) or price < 0:
                raise ValueError(f"Invalid price for {symbol}: {price}")
            total += position.quantity * price
        if missing_prices:
            print(f"[PortfolioManager] Warning: Missing prices for {missing_prices}")
        return total

    def process_fill(self, symbol: str, quantity: float, price: float, commission: float = 0.0):
        if not symbol or not isinstance(symbol, str):
            raise ValueError("symbol must be a non-empty string")
        if not isinstance(quantity, (int, float)) or abs(quantity) < self._epsilon:
            raise ValueError("quantity must be a nonzero number")
        if not isinstance(price, (int, float)) or price <= 0:
            raise ValueError("price must be a positive number")
        if not isinstance(commission, (int, float)) or commission < 0:
            raise ValueError("commission must be non-negative")
        total_cost = quantity * price + commission
        # Check sufficient funds for buys
        if quantity > 0 and self.cash_balance < total_cost:
            raise ValueError(f"Insufficient funds. Need {total_cost}, have {self.cash_balance}")
        # Check sufficient shares for sells
        if quantity < 0:
            if symbol not in self.positions:
                raise ValueError(f"Cannot sell {symbol}: no position exists")
            current_quantity = self.positions[symbol].quantity
            if current_quantity < abs(quantity) - self._epsilon:
                raise ValueError(f"Cannot sell {abs(quantity)} shares of {symbol}: only have {current_quantity}")
        # Process the trade
        self.cash_balance -= total_cost
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)
        try:
            self.positions[symbol].update_position(quantity, price)
            # Clean up zero positions
            if abs(self.positions[symbol].quantity) < self._epsilon:
                del self.positions[symbol]
        except Exception as e:
            self.cash_balance += total_cost
            raise ValueError(f"Failed to update position: {e}") 
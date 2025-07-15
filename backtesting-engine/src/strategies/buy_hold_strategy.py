from typing import List
from datetime import datetime
from .backtest_strategy_base import BacktestStrategy, MarketEvent, Signal

class BuyAndHoldSignal:
    def __init__(self, symbol: str, action: str, quantity: float):
        self.symbol = symbol
        self.action = action
        self.quantity = quantity

class BuyAndHoldStrategy(BacktestStrategy):
    """
    Simple buy-and-hold strategy: Buys a fixed quantity at the first event, then holds.
    """
    def __init__(self, symbol: str, quantity: float = 1.0, portfolio=None):
        super().__init__(portfolio)
        self.symbol = symbol
        self.quantity = quantity
        self.has_bought = False

    def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
        if not self.has_bought and market_event.symbol == self.symbol:
            self.has_bought = True
            return [BuyAndHoldSignal(self.symbol, "BUY", self.quantity)]
        return []

    def get_name(self) -> str:
        return f"BuyAndHold({self.symbol})" 
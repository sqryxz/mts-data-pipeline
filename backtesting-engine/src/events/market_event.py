from datetime import datetime
from typing import Dict
from .base_event import BaseEvent

class MarketEvent(BaseEvent):
    def __init__(self, timestamp: datetime, symbol: str, 
                 open_price: float, high_price: float, 
                 low_price: float, close_price: float, volume: float):
        self._validate_inputs(symbol, open_price, high_price, low_price, close_price, volume)
        super().__init__(timestamp, event_type=self.get_event_type())
        self.symbol = symbol.upper()
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price
        self.volume = volume

    @staticmethod
    def _validate_inputs(symbol: str, open_price: float, high_price: float, low_price: float, close_price: float, volume: float) -> None:
        epsilon = 1e-8
        if not symbol or not isinstance(symbol, str):
            raise ValueError("symbol must be a non-empty string")
        prices = {'open': open_price, 'high': high_price, 'low': low_price, 'close': close_price}
        for name, price in prices.items():
            if not isinstance(price, (int, float)) or price <= epsilon:
                raise ValueError(f"{name} must be a positive number")
        if not isinstance(volume, (int, float)) or volume < 0:
            raise ValueError("volume must be non-negative")
        if high_price < low_price:
            raise ValueError("high price must be >= low price")
        if not (low_price <= open_price <= high_price):
            raise ValueError("open price must be between low and high")
        if not (low_price <= close_price <= high_price):
            raise ValueError("close price must be between low and high")

    def validate(self) -> bool:
        self._validate_inputs(self.symbol, self.open, self.high, self.low, self.close, self.volume)
        return True

    @staticmethod
    def get_event_type() -> str:
        return "MARKET"

    def get_ohlc_dict(self) -> Dict[str, float]:
        return {
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close
        } 
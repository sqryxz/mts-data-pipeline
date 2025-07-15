from datetime import datetime
from .base_event import BaseEvent

class SignalEvent(BaseEvent):
    VALID_TYPES = {"BUY", "SELL", "HOLD"}

    def __init__(self, timestamp: datetime, symbol: str, signal_type: str, strength: float, strategy: str):
        self._validate_inputs(symbol, signal_type, strength, strategy)
        super().__init__(timestamp, event_type="SIGNAL")
        self.symbol = symbol.strip()
        self.signal_type = signal_type.upper().strip()
        self.strength = float(strength)
        self.strategy = strategy.strip()

    def _validate_inputs(self, symbol, signal_type, strength, strategy):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")
        if not isinstance(signal_type, str) or not signal_type.strip():
            raise ValueError("signal_type must be a non-empty string")
        if signal_type.upper().strip() not in self.VALID_TYPES:
            raise ValueError(f"signal_type must be one of {self.VALID_TYPES}")
        if not isinstance(strength, (int, float)):
            raise ValueError("strength must be numeric")
        if not (0 <= float(strength) <= 1):
            raise ValueError("strength must be between 0 and 1")
        if not isinstance(strategy, str) or not strategy.strip():
            raise ValueError("strategy must be a non-empty string")

    def validate(self) -> bool:
        try:
            self._validate_inputs(self.symbol, self.signal_type, self.strength, self.strategy)
            return True
        except ValueError:
            return False 
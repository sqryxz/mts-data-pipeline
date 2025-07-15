from abc import ABC, abstractmethod
from typing import Optional, List, Protocol, Union
from datetime import datetime
from ..events.signal_event import SignalEvent

class MarketEvent(Protocol):
    """Protocol defining market event interface."""
    timestamp: datetime
    symbol: str
    price: float

class Portfolio(Protocol):
    """Protocol defining portfolio interface."""
    balance: float
    positions: dict

class Signal(Protocol):
    """Protocol defining signal interface."""
    symbol: str
    action: str
    quantity: float
    strength: Optional[float]

class BacktestStrategy(ABC):
    """
    Abstract base class for backtesting trading strategies.

    This class defines the interface that all backtesting strategies
    must implement to work with the backtesting framework.
    """
    def __init__(self, portfolio: Optional[Portfolio] = None) -> None:
        """
        Initialize the strategy with optional portfolio reference.

        Args:
            portfolio: Portfolio instance for position tracking
        """
        self.portfolio = portfolio

    @abstractmethod
    def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
        """
        Generate trading signals based on the market event.

        Args:
            market_event: Market data event containing price/volume data
        Returns:
            List of trading signals to execute
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Return the name of the strategy.

        Returns:
            Human-readable strategy name
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    def process_market_data(self, market_event: MarketEvent) -> List[SignalEvent]:
        """
        Process market data and return a list of SignalEvent objects based on strategy logic.

        Args:
            market_event: Market data event to process
        Returns:
            List of SignalEvent objects
        Raises:
            ValueError: If market_event is None or invalid
            AttributeError: If required attributes are missing
        """
        if market_event is None:
            raise ValueError("Market event cannot be None")
        if not hasattr(market_event, 'timestamp'):
            raise AttributeError("Market event must have 'timestamp' attribute")
        signals = self.generate_signals(market_event)
        if not isinstance(signals, list):
            raise TypeError("generate_signals must return a list")
        signal_events = []
        for i, sig in enumerate(signals):
            if not hasattr(sig, 'symbol'):
                raise AttributeError(f"Signal {i} missing 'symbol' attribute")
            if not hasattr(sig, 'action'):
                raise AttributeError(f"Signal {i} missing 'action' attribute")
            # Safe strength extraction with validation
            strength = getattr(sig, 'strength', 1.0)
            if strength is None or not isinstance(strength, (int, float)) or not (0 <= float(strength) <= 1):
                strength = 1.0
            signal_events.append(
                SignalEvent(
                    timestamp=market_event.timestamp,
                    symbol=sig.symbol,
                    signal_type=sig.action,
                    strength=strength,
                    strategy=self.get_name()
                )
            )
        return signal_events 
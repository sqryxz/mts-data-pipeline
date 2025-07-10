from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class OrderBookLevel:
    price: float
    quantity: float
    level: int

@dataclass
class OrderBookSnapshot:
    exchange: str
    symbol: str
    timestamp: int
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    
    def get_best_bid(self) -> Optional[OrderBookLevel]:
        return self.bids[0] if self.bids else None
    
    def get_best_ask(self) -> Optional[OrderBookLevel]:
        return self.asks[0] if self.asks else None

@dataclass
class BidAskSpread:
    exchange: str
    symbol: str
    timestamp: int
    bid_price: float
    ask_price: float
    spread_absolute: float
    spread_percentage: float
    mid_price: float

@dataclass
class FundingRate:
    exchange: str
    symbol: str
    timestamp: int
    funding_rate: float
    predicted_rate: Optional[float]
    funding_time: int 
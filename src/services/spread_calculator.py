import logging
from typing import Optional
from src.data.realtime_models import OrderBookSnapshot, BidAskSpread
import time

logger = logging.getLogger(__name__)

class SpreadCalculator:
    def __init__(self):
        self.last_spreads = {}  # Cache for comparison
        
    def calculate_spread(self, orderbook: OrderBookSnapshot) -> Optional[BidAskSpread]:
        """Calculate bid-ask spread from order book"""
        try:
            best_bid = orderbook.get_best_bid()
            best_ask = orderbook.get_best_ask()
            
            if not best_bid or not best_ask:
                logger.warning(f"Missing best bid/ask for {orderbook.symbol}")
                return None
            
            # Calculate spread metrics
            spread_absolute = best_ask.price - best_bid.price
            mid_price = (best_bid.price + best_ask.price) / 2
            spread_percentage = (spread_absolute / mid_price) * 100
            
            spread = BidAskSpread(
                exchange=orderbook.exchange,
                symbol=orderbook.symbol,
                timestamp=orderbook.timestamp,
                bid_price=best_bid.price,
                ask_price=best_ask.price,
                spread_absolute=spread_absolute,
                spread_percentage=spread_percentage,
                mid_price=mid_price
            )
            
            # Cache for comparison
            cache_key = f"{orderbook.exchange}_{orderbook.symbol}"
            self.last_spreads[cache_key] = spread
            
            return spread
            
        except Exception as e:
            logger.error(f"Failed to calculate spread for {orderbook.symbol}: {e}")
            return None
    
    def get_spread_change(self, current_spread: BidAskSpread) -> Optional[float]:
        """Get spread change percentage from last calculation"""
        try:
            cache_key = f"{current_spread.exchange}_{current_spread.symbol}"
            last_spread = self.last_spreads.get(cache_key)
            
            if not last_spread:
                return None
            
            if last_spread.spread_percentage == 0:
                return None
            
            change = ((current_spread.spread_percentage - last_spread.spread_percentage) 
                     / last_spread.spread_percentage) * 100
            
            return change
            
        except Exception as e:
            logger.error(f"Failed to calculate spread change: {e}")
            return None
    
    def is_spread_anomaly(self, spread: BidAskSpread, threshold_percentage: float = 5.0) -> bool:
        """Check if spread is unusually wide"""
        try:
            return spread.spread_percentage > threshold_percentage
        except Exception as e:
            logger.error(f"Error checking spread anomaly: {e}")
            return False 
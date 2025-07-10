import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from src.data.realtime_models import OrderBookSnapshot, BidAskSpread
from src.services.spread_calculator import SpreadCalculator

logger = logging.getLogger(__name__)

class ArbitrageDirection(Enum):
    """Direction of arbitrage opportunity"""
    BUY_BINANCE_SELL_BYBIT = "buy_binance_sell_bybit"
    BUY_BYBIT_SELL_BINANCE = "buy_bybit_sell_binance"
    NO_ARBITRAGE = "no_arbitrage"

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity between exchanges"""
    symbol: str
    direction: ArbitrageDirection
    profit_percentage: float
    profit_absolute: float
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    max_volume: float  # Maximum tradeable volume
    timestamp: int
    duration_ms: int = 0  # How long this opportunity has existed
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time() * 1000)

@dataclass
class CrossExchangeSpread:
    """Spread comparison between exchanges"""
    symbol: str
    binance_bid: float
    binance_ask: float
    bybit_bid: float
    bybit_ask: float
    binance_spread: float
    bybit_spread: float
    spread_difference: float
    price_difference_percentage: float
    timestamp: int
    
    def get_mid_price_difference(self) -> float:
        """Calculate mid price difference between exchanges"""
        binance_mid = (self.binance_bid + self.binance_ask) / 2
        bybit_mid = (self.bybit_bid + self.bybit_ask) / 2
        return abs(binance_mid - bybit_mid)

class CrossExchangeAnalyzer:
    """Analyzes price differences and arbitrage opportunities between exchanges"""
    
    def __init__(self, min_profit_threshold: float = 0.001, min_volume_threshold: float = 100.0):
        """
        Initialize cross-exchange analyzer
        
        Args:
            min_profit_threshold: Minimum profit percentage for arbitrage (0.1% default)
            min_volume_threshold: Minimum volume in USD for opportunities
        """
        self.min_profit_threshold = min_profit_threshold
        self.min_volume_threshold = min_volume_threshold
        self.spread_calculator = SpreadCalculator()
        
        # Track historical opportunities
        self.active_opportunities: Dict[str, ArbitrageOpportunity] = {}
        self.opportunity_history: List[ArbitrageOpportunity] = []
        
        # Track price differences
        self.spread_history: Dict[str, List[CrossExchangeSpread]] = {}
        
        # Performance metrics
        self.total_opportunities_detected = 0
        self.profitable_opportunities = 0
        
    def analyze_orderbooks(self, binance_orderbook: OrderBookSnapshot, 
                          bybit_orderbook: OrderBookSnapshot) -> Tuple[Optional[ArbitrageOpportunity], CrossExchangeSpread]:
        """
        Analyze order books from both exchanges for arbitrage opportunities
        
        Returns:
            Tuple of (ArbitrageOpportunity or None, CrossExchangeSpread)
        """
        try:
            if binance_orderbook.symbol != bybit_orderbook.symbol:
                logger.error(f"Symbol mismatch: {binance_orderbook.symbol} vs {bybit_orderbook.symbol}")
                return None, None
            
            symbol = binance_orderbook.symbol
            
            # Get best prices
            binance_best_bid = binance_orderbook.get_best_bid()
            binance_best_ask = binance_orderbook.get_best_ask()
            bybit_best_bid = bybit_orderbook.get_best_bid()
            bybit_best_ask = bybit_orderbook.get_best_ask()
            
            if not all([binance_best_bid, binance_best_ask, bybit_best_bid, bybit_best_ask]):
                logger.warning(f"Missing price data for {symbol}")
                return None, None
            
            # Calculate spreads
            binance_spread = self.spread_calculator.calculate_spread(binance_orderbook)
            bybit_spread = self.spread_calculator.calculate_spread(bybit_orderbook)
            
            if not binance_spread or not bybit_spread:
                logger.warning(f"Failed to calculate spreads for {symbol}")
                return None, None
            
            # Create cross-exchange spread comparison
            cross_spread = CrossExchangeSpread(
                symbol=symbol,
                binance_bid=binance_best_bid.price,
                binance_ask=binance_best_ask.price,
                bybit_bid=bybit_best_bid.price,
                bybit_ask=bybit_best_ask.price,
                binance_spread=binance_spread.spread_percentage,
                bybit_spread=bybit_spread.spread_percentage,
                spread_difference=abs(binance_spread.spread_percentage - bybit_spread.spread_percentage),
                price_difference_percentage=self._calculate_price_difference_percentage(
                    binance_spread.mid_price, bybit_spread.mid_price
                ),
                timestamp=max(binance_orderbook.timestamp, bybit_orderbook.timestamp)
            )
            
            # Check for arbitrage opportunities
            arbitrage_opportunity = self._detect_arbitrage(
                symbol, binance_best_bid, binance_best_ask, 
                bybit_best_bid, bybit_best_ask, binance_orderbook, bybit_orderbook
            )
            
            # Update opportunity tracking
            if arbitrage_opportunity:
                self._update_opportunity_tracking(arbitrage_opportunity)
            
            # Store spread history
            if symbol not in self.spread_history:
                self.spread_history[symbol] = []
            self.spread_history[symbol].append(cross_spread)
            
            # Keep only last 1000 spreads per symbol to manage memory
            if len(self.spread_history[symbol]) > 1000:
                self.spread_history[symbol] = self.spread_history[symbol][-1000:]
            
            return arbitrage_opportunity, cross_spread
            
        except Exception as e:
            logger.error(f"Error analyzing orderbooks for {binance_orderbook.symbol}: {e}")
            return None, None
    
    def _detect_arbitrage(self, symbol: str, binance_bid, binance_ask, bybit_bid, bybit_ask,
                         binance_orderbook: OrderBookSnapshot, bybit_orderbook: OrderBookSnapshot) -> Optional[ArbitrageOpportunity]:
        """Detect arbitrage opportunities between exchanges"""
        
        # Scenario 1: Buy on Binance, sell on Bybit
        # (Bybit bid > Binance ask)
        if bybit_bid.price > binance_ask.price:
            profit_absolute = bybit_bid.price - binance_ask.price
            profit_percentage = (profit_absolute / binance_ask.price) * 100
            
            if profit_percentage >= self.min_profit_threshold * 100:
                max_volume = self._calculate_max_tradeable_volume(
                    binance_ask, bybit_bid, binance_orderbook, bybit_orderbook
                )
                
                if max_volume * binance_ask.price >= self.min_volume_threshold:
                    return ArbitrageOpportunity(
                        symbol=symbol,
                        direction=ArbitrageDirection.BUY_BINANCE_SELL_BYBIT,
                        profit_percentage=profit_percentage,
                        profit_absolute=profit_absolute,
                        buy_exchange="binance",
                        sell_exchange="bybit",
                        buy_price=binance_ask.price,
                        sell_price=bybit_bid.price,
                        max_volume=max_volume,
                        timestamp=int(time.time() * 1000)
                    )
        
        # Scenario 2: Buy on Bybit, sell on Binance
        # (Binance bid > Bybit ask)
        elif binance_bid.price > bybit_ask.price:
            profit_absolute = binance_bid.price - bybit_ask.price
            profit_percentage = (profit_absolute / bybit_ask.price) * 100
            
            if profit_percentage >= self.min_profit_threshold * 100:
                max_volume = self._calculate_max_tradeable_volume(
                    bybit_ask, binance_bid, bybit_orderbook, binance_orderbook
                )
                
                if max_volume * bybit_ask.price >= self.min_volume_threshold:
                    return ArbitrageOpportunity(
                        symbol=symbol,
                        direction=ArbitrageDirection.BUY_BYBIT_SELL_BINANCE,
                        profit_percentage=profit_percentage,
                        profit_absolute=profit_absolute,
                        buy_exchange="bybit",
                        sell_exchange="binance",
                        buy_price=bybit_ask.price,
                        sell_price=binance_bid.price,
                        max_volume=max_volume,
                        timestamp=int(time.time() * 1000)
                    )
        
        return None
    
    def _calculate_max_tradeable_volume(self, buy_level, sell_level, 
                                       buy_orderbook: OrderBookSnapshot, 
                                       sell_orderbook: OrderBookSnapshot) -> float:
        """Calculate maximum tradeable volume for arbitrage"""
        # For simplicity, use the minimum of best bid/ask quantities
        # In practice, you'd want to analyze multiple levels
        buy_quantity = buy_level.quantity
        sell_quantity = sell_level.quantity
        
        # Account for potential slippage by using 80% of available liquidity
        return min(buy_quantity, sell_quantity) * 0.8
    
    def _calculate_price_difference_percentage(self, price1: float, price2: float) -> float:
        """Calculate percentage difference between two prices"""
        avg_price = (price1 + price2) / 2
        return abs(price1 - price2) / avg_price * 100
    
    def _update_opportunity_tracking(self, opportunity: ArbitrageOpportunity) -> None:
        """Update tracking of arbitrage opportunities"""
        key = f"{opportunity.symbol}_{opportunity.direction.value}"
        
        if key in self.active_opportunities:
            # Update existing opportunity with duration
            existing = self.active_opportunities[key]
            opportunity.duration_ms = opportunity.timestamp - existing.timestamp
        
        self.active_opportunities[key] = opportunity
        self.opportunity_history.append(opportunity)
        self.total_opportunities_detected += 1
        
        if opportunity.profit_percentage > 0:
            self.profitable_opportunities += 1
    
    def get_active_opportunities(self, symbol: str = None) -> List[ArbitrageOpportunity]:
        """Get currently active arbitrage opportunities"""
        opportunities = list(self.active_opportunities.values())
        
        if symbol:
            opportunities = [opp for opp in opportunities if opp.symbol == symbol]
        
        return opportunities
    
    def get_opportunity_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected opportunities"""
        if not self.opportunity_history:
            return {
                "total_opportunities": 0,
                "profitable_opportunities": 0,
                "success_rate": 0.0,
                "average_profit_percentage": 0.0,
                "max_profit_percentage": 0.0
            }
        
        profits = [opp.profit_percentage for opp in self.opportunity_history]
        
        return {
            "total_opportunities": self.total_opportunities_detected,
            "profitable_opportunities": self.profitable_opportunities,
            "success_rate": (self.profitable_opportunities / self.total_opportunities_detected) * 100,
            "average_profit_percentage": sum(profits) / len(profits),
            "max_profit_percentage": max(profits),
            "min_profit_percentage": min(profits),
            "opportunities_by_symbol": self._get_opportunities_by_symbol(),
            "opportunities_by_direction": self._get_opportunities_by_direction()
        }
    
    def _get_opportunities_by_symbol(self) -> Dict[str, int]:
        """Count opportunities by symbol"""
        symbol_counts = {}
        for opp in self.opportunity_history:
            symbol_counts[opp.symbol] = symbol_counts.get(opp.symbol, 0) + 1
        return symbol_counts
    
    def _get_opportunities_by_direction(self) -> Dict[str, int]:
        """Count opportunities by direction"""
        direction_counts = {}
        for opp in self.opportunity_history:
            direction = opp.direction.value
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
        return direction_counts
    
    def clear_stale_opportunities(self, max_age_ms: int = 10000) -> int:
        """Clear arbitrage opportunities older than max_age_ms"""
        current_time = int(time.time() * 1000)
        stale_keys = []
        
        for key, opportunity in self.active_opportunities.items():
            if (current_time - opportunity.timestamp) > max_age_ms:
                stale_keys.append(key)
        
        for key in stale_keys:
            del self.active_opportunities[key]
        
        return len(stale_keys)
    
    def analyze_spread_trends(self, symbol: str, lookback_minutes: int = 60) -> Dict[str, Any]:
        """Analyze spread trends over time for a symbol"""
        current_time = int(time.time() * 1000)
        lookback_ms = lookback_minutes * 60 * 1000
        cutoff_time = current_time - lookback_ms
        
        # Filter recent spreads
        recent_spreads = [
            spread for spread in self.spread_history.get(symbol, [])
            if spread.timestamp >= cutoff_time
        ]
        
        if not recent_spreads:
            return {"symbol": symbol, "error": "No recent spread data"}
        
        # Calculate trends
        spread_diffs = [s.spread_difference for s in recent_spreads]
        price_diffs = [s.price_difference_percentage for s in recent_spreads]
        
        return {
            "symbol": symbol,
            "period_minutes": lookback_minutes,
            "data_points": len(recent_spreads),
            "average_spread_difference": sum(spread_diffs) / len(spread_diffs),
            "max_spread_difference": max(spread_diffs),
            "average_price_difference": sum(price_diffs) / len(price_diffs),
            "max_price_difference": max(price_diffs),
            "trend_direction": "increasing" if spread_diffs[-1] > spread_diffs[0] else "decreasing"
        } 
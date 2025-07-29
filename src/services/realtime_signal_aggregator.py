import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict

from src.data.realtime_models import OrderBookSnapshot, BidAskSpread
from src.services.cross_exchange_analyzer import CrossExchangeAnalyzer, ArbitrageOpportunity, ArbitrageDirection
from src.signals.signal_aggregator import SignalAggregator
from src.data.signal_models import TradingSignal, SignalType, SignalStrength
from src.api.binance_client import BinanceClient
from src.api.bybit_client import BybitClient
from src.realtime.orderbook_processor import OrderBookProcessor
from src.data.realtime_storage import RealtimeStorage

logger = logging.getLogger(__name__)

class RealTimeSignalType(Enum):
    """Real-time specific signal types"""
    ARBITRAGE = "arbitrage"
    FUNDING_RATE_DIVERGENCE = "funding_rate_divergence"
    VOLUME_SPIKE = "volume_spike"
    SPREAD_ANOMALY = "spread_anomaly"
    MOMENTUM_BREAKOUT = "momentum_breakout"

@dataclass
class RealTimeSignal:
    """Real-time trading signal"""
    signal_type: RealTimeSignalType
    symbol: str
    strength: SignalStrength
    confidence: float  # 0.0 to 1.0
    direction: str  # 'buy', 'sell', 'neutral'
    price: float
    volume: float
    timestamp: int
    metadata: Dict[str, Any]
    expires_at: Optional[int] = None  # Signal expiration timestamp
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time() * 1000)
        if self.expires_at is None:
            # Default expiration: 5 minutes
            self.expires_at = self.timestamp + (5 * 60 * 1000)
    
    def is_expired(self) -> bool:
        """Check if signal has expired"""
        return int(time.time() * 1000) > self.expires_at
    
    def to_traditional_signal(self) -> TradingSignal:
        """Convert to traditional TradingSignal format for compatibility"""
        # Map real-time signal types to traditional types
        signal_type_mapping = {
            RealTimeSignalType.ARBITRAGE: SignalType.LONG if self.direction == 'buy' else SignalType.SHORT,
            RealTimeSignalType.FUNDING_RATE_DIVERGENCE: SignalType.LONG if self.direction == 'buy' else SignalType.SHORT,
            RealTimeSignalType.VOLUME_SPIKE: SignalType.HOLD,
            RealTimeSignalType.SPREAD_ANOMALY: SignalType.HOLD,
            RealTimeSignalType.MOMENTUM_BREAKOUT: SignalType.LONG if self.direction == 'buy' else SignalType.SHORT
        }
        
        return TradingSignal(
            asset=self.symbol.replace('USDT', '').lower(),  # Convert BTCUSDT to bitcoin
            signal_type=signal_type_mapping.get(self.signal_type, SignalType.HOLD),
            timestamp=self.timestamp,
            price=self.price,
            strategy_name=f"realtime_{self.signal_type.value}",
            signal_strength=self.strength,
            confidence=self.confidence,
            position_size=min(self.volume / 10.0, 0.1),  # Conservative position sizing
            analysis_data=self.metadata
        )

class RealTimeSignalAggregator:
    """Aggregates and manages real-time trading signals from multiple sources"""
    
    def __init__(self, 
                 min_arbitrage_profit: float = 0.001,
                 min_signal_confidence: float = 0.5,  # Lowered from 0.7
                 max_active_signals: int = 50):
        """
        Initialize real-time signal aggregator
        
        Args:
            min_arbitrage_profit: Minimum profit threshold for arbitrage signals
            min_signal_confidence: Minimum confidence for signal generation
            max_active_signals: Maximum number of active signals to maintain
        """
        # Track different types of signals
        self.orderbook_signals: Dict[str, RealTimeSignal] = {}
        self.funding_signals: Dict[str, RealTimeSignal] = {}
        self.spread_signals: Dict[str, RealTimeSignal] = {}
        self.arbitrage_signals: Dict[str, RealTimeSignal] = {}
        
        # Configuration for signal generation
        self.min_arbitrage_profit = 0.001  # 0.1% minimum arbitrage profit
        self.spread_threshold = 0.0005  # 0.05% spread threshold
        self.volume_threshold = 1.0  # Minimum volume threshold
        
        # Symbol monitoring
        self.monitored_symbols: Set[str] = {'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'TAOUSDT', 'FETUSDT', 'AGIXUSDT', 'RNDRUSDT', 'OCEANUSDT'}
        
        # Performance tracking
        self.signals_generated = 0
        self.signals_by_type = defaultdict(int)
        self.last_signal_time = {}
        
        logger.info("RealTimeSignalAggregator initialized")
        
        # Components
        self.cross_exchange_analyzer = CrossExchangeAnalyzer(
            min_profit_threshold=min_arbitrage_profit,
            min_volume_threshold=100.0
        )
        self.orderbook_processor = OrderBookProcessor()
        self.binance_client = BinanceClient()
        self.bybit_client = BybitClient()
        self.realtime_storage = RealtimeStorage()
        
        # Signal management
        self.active_signals: Dict[str, RealTimeSignal] = {}
        self.signal_history: List[RealTimeSignal] = []
        self.signal_callbacks: List[Callable[[RealTimeSignal], None]] = []
        
        # Performance tracking
        self.total_signals_generated = 0
        self.successful_signals = 0
        self.last_cleanup_time = time.time()
        
        # Symbol tracking
        self.last_orderbook_data: Dict[str, Dict[str, OrderBookSnapshot]] = {}
        
    def add_signal_callback(self, callback: Callable[[RealTimeSignal], None]) -> None:
        """Add callback function to be called when new signals are generated"""
        self.signal_callbacks.append(callback)
    
    def remove_signal_callback(self, callback: Callable[[RealTimeSignal], None]) -> None:
        """Remove signal callback"""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)
    
    async def process_orderbook_data(self, binance_orderbook: OrderBookSnapshot, 
                                   bybit_orderbook: OrderBookSnapshot) -> List[RealTimeSignal]:
        """
        Process order book data from both exchanges and generate signals
        
        Returns:
            List of generated real-time signals
        """
        try:
            signals = []
            symbol = binance_orderbook.symbol
            
            # Store latest orderbook data
            if symbol not in self.last_orderbook_data:
                self.last_orderbook_data[symbol] = {}
            self.last_orderbook_data[symbol]['binance'] = binance_orderbook
            self.last_orderbook_data[symbol]['bybit'] = bybit_orderbook
            
            # 1. Check for arbitrage opportunities
            arbitrage_signals = await self._detect_arbitrage_signals(binance_orderbook, bybit_orderbook)
            signals.extend(arbitrage_signals)
            
            # 2. Check for spread anomalies
            spread_signals = await self._detect_spread_anomalies(binance_orderbook, bybit_orderbook)
            signals.extend(spread_signals)
            
            # 3. Check for volume spikes
            volume_signals = await self._detect_volume_signals(binance_orderbook, bybit_orderbook)
            signals.extend(volume_signals)
            
            # Process and store signals
            for signal in signals:
                await self._process_new_signal(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error processing orderbook data for {binance_orderbook.symbol}: {e}")
            return []
    
    async def _detect_arbitrage_signals(self, binance_orderbook: OrderBookSnapshot,
                                      bybit_orderbook: OrderBookSnapshot) -> List[RealTimeSignal]:
        """Detect arbitrage trading signals"""
        signals = []
        
        try:
            opportunity, cross_spread = self.cross_exchange_analyzer.analyze_orderbooks(
                binance_orderbook, bybit_orderbook
            )
            
            if opportunity and opportunity.profit_percentage >= self.min_arbitrage_profit * 100:
                # Calculate signal strength based on profit percentage
                if opportunity.profit_percentage >= 0.2:  # 0.2%+
                    strength = SignalStrength.STRONG
                elif opportunity.profit_percentage >= 0.1:  # 0.1%+
                    strength = SignalStrength.MODERATE
                else:
                    strength = SignalStrength.WEAK
                
                # Calculate confidence based on volume and profit consistency
                volume_factor = min(opportunity.max_volume / 2.0, 1.0)  # Normalize by 2 BTC
                profit_factor = min(opportunity.profit_percentage / 0.5, 1.0)  # Normalize by 0.5%
                confidence = (volume_factor + profit_factor) / 2
                
                if confidence >= self.min_signal_confidence:
                    signal = RealTimeSignal(
                        signal_type=RealTimeSignalType.ARBITRAGE,
                        symbol=opportunity.symbol,
                        strength=strength,
                        confidence=confidence,
                        direction='buy' if opportunity.direction != ArbitrageDirection.NO_ARBITRAGE else 'neutral',
                        price=opportunity.buy_price,
                        volume=opportunity.max_volume,
                        timestamp=opportunity.timestamp,
                        metadata={
                            'buy_exchange': opportunity.buy_exchange,
                            'sell_exchange': opportunity.sell_exchange,
                            'sell_price': opportunity.sell_price,
                            'profit_absolute': opportunity.profit_absolute,
                            'profit_percentage': opportunity.profit_percentage,
                            'arbitrage_direction': opportunity.direction.value
                        },
                        expires_at=opportunity.timestamp + (2 * 60 * 1000)  # 2 minute expiry for arbitrage
                    )
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error detecting arbitrage signals: {e}")
        
        return signals
    
    async def _detect_spread_anomalies(self, binance_orderbook: OrderBookSnapshot,
                                     bybit_orderbook: OrderBookSnapshot) -> List[RealTimeSignal]:
        """Detect unusual spread patterns"""
        signals = []
        
        try:
            # Calculate spreads for both exchanges
            binance_best_bid = binance_orderbook.get_best_bid()
            binance_best_ask = binance_orderbook.get_best_ask()
            bybit_best_bid = bybit_orderbook.get_best_bid()
            bybit_best_ask = bybit_orderbook.get_best_ask()
            
            if not all([binance_best_bid, binance_best_ask, bybit_best_bid, bybit_best_ask]):
                return signals
            
            # Calculate spread percentages
            binance_spread_pct = ((binance_best_ask.price - binance_best_bid.price) / 
                                 binance_best_bid.price) * 100
            bybit_spread_pct = ((bybit_best_ask.price - bybit_best_bid.price) / 
                               bybit_best_bid.price) * 100
            
            # Detect unusually wide spreads (> 0.1%)
            if binance_spread_pct > 0.1 or bybit_spread_pct > 0.1:
                wider_exchange = 'binance' if binance_spread_pct > bybit_spread_pct else 'bybit'
                max_spread = max(binance_spread_pct, bybit_spread_pct)
                
                signal = RealTimeSignal(
                    signal_type=RealTimeSignalType.SPREAD_ANOMALY,
                    symbol=binance_orderbook.symbol,
                    strength=SignalStrength.MODERATE if max_spread > 0.2 else SignalStrength.WEAK,
                    confidence=min(max_spread / 0.5, 1.0),  # Normalize by 0.5%
                    direction='neutral',
                    price=(binance_best_bid.price + binance_best_ask.price) / 2,
                    volume=min(binance_best_bid.quantity, binance_best_ask.quantity),
                    timestamp=max(binance_orderbook.timestamp, bybit_orderbook.timestamp),
                    metadata={
                        'binance_spread_pct': binance_spread_pct,
                        'bybit_spread_pct': bybit_spread_pct,
                        'wider_exchange': wider_exchange,
                        'spread_difference': abs(binance_spread_pct - bybit_spread_pct)
                    }
                )
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error detecting spread anomalies: {e}")
        
        return signals
    
    async def _detect_volume_signals(self, binance_orderbook: OrderBookSnapshot,
                                   bybit_orderbook: OrderBookSnapshot) -> List[RealTimeSignal]:
        """Detect unusual volume patterns"""
        signals = []
        
        try:
            symbol = binance_orderbook.symbol
            
            # Get previous orderbook data for comparison
            if symbol in self.last_orderbook_data:
                prev_binance = self.last_orderbook_data[symbol].get('binance')
                prev_bybit = self.last_orderbook_data[symbol].get('bybit')
                
                if prev_binance and prev_bybit:
                    # Calculate volume changes
                    binance_vol_change = self._calculate_volume_change(prev_binance, binance_orderbook)
                    bybit_vol_change = self._calculate_volume_change(prev_bybit, bybit_orderbook)
                    
                    # Detect significant volume spikes (> 50% increase)
                    max_vol_change = max(binance_vol_change, bybit_vol_change)
                    if max_vol_change > 0.5:  # 50% increase
                        exchange = 'binance' if binance_vol_change > bybit_vol_change else 'bybit'
                        
                        signal = RealTimeSignal(
                            signal_type=RealTimeSignalType.VOLUME_SPIKE,
                            symbol=symbol,
                            strength=SignalStrength.STRONG if max_vol_change > 1.0 else SignalStrength.MODERATE,
                            confidence=min(max_vol_change / 2.0, 1.0),
                            direction='neutral',
                            price=(binance_orderbook.get_best_bid().price + 
                                  binance_orderbook.get_best_ask().price) / 2,
                            volume=max_vol_change,
                            timestamp=max(binance_orderbook.timestamp, bybit_orderbook.timestamp),
                            metadata={
                                'exchange': exchange,
                                'volume_change_pct': max_vol_change * 100,
                                'binance_volume_change': binance_vol_change,
                                'bybit_volume_change': bybit_vol_change
                            }
                        )
                        signals.append(signal)
                        
        except Exception as e:
            logger.error(f"Error detecting volume signals: {e}")
        
        return signals
    
    def _calculate_volume_change(self, prev_orderbook: OrderBookSnapshot, 
                               current_orderbook: OrderBookSnapshot) -> float:
        """Calculate volume change percentage between orderbooks"""
        try:
            prev_volume = sum(level.quantity for level in prev_orderbook.bids[:5]) + \
                         sum(level.quantity for level in prev_orderbook.asks[:5])
            current_volume = sum(level.quantity for level in current_orderbook.bids[:5]) + \
                           sum(level.quantity for level in current_orderbook.asks[:5])
            
            if prev_volume == 0:
                return 0.0
            
            return (current_volume - prev_volume) / prev_volume
            
        except Exception:
            return 0.0
    
    async def _process_new_signal(self, signal: RealTimeSignal) -> None:
        """Process and store a new signal"""
        try:
            # Generate unique signal ID
            signal_id = f"{signal.signal_type.value}_{signal.symbol}_{signal.timestamp}"
            
            # Store signal
            self.active_signals[signal_id] = signal
            self.signal_history.append(signal)
            self.total_signals_generated += 1
            
            # Trigger callbacks
            for callback in self.signal_callbacks:
                try:
                    callback(signal)
                except Exception as e:
                    logger.error(f"Error in signal callback: {e}")
            
            # Store in database for persistence
            await self._store_signal_in_database(signal)
            
            logger.info(f"Generated {signal.signal_type.value} signal for {signal.symbol}: "
                       f"{signal.direction} @ {signal.price} (confidence: {signal.confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing new signal: {e}")
    
    async def _store_signal_in_database(self, signal: RealTimeSignal) -> None:
        """Store signal in database for historical analysis"""
        try:
            # Store in realtime storage
            signal_data = {
                'signal_type': signal.signal_type.value,
                'symbol': signal.symbol,
                'strength': signal.strength.value,
                'confidence': signal.confidence,
                'direction': signal.direction,
                'price': signal.price,
                'volume': signal.volume,
                'timestamp': signal.timestamp,
                'expires_at': signal.expires_at,
                'metadata': signal.metadata
            }
            
            # Note: In a real implementation, you'd store this in the realtime_storage
            # For now, we'll just log it
            logger.debug(f"Stored signal in database: {signal_data}")
            
        except Exception as e:
            logger.error(f"Error storing signal in database: {e}")
    
    def get_active_signals(self, symbol: str = None, 
                          signal_type: RealTimeSignalType = None) -> List[RealTimeSignal]:
        """Get currently active signals with optional filtering"""
        signals = list(self.active_signals.values())
        
        # Filter by symbol
        if symbol:
            signals = [s for s in signals if s.symbol == symbol]
        
        # Filter by signal type
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        
        return signals
    
    def cleanup_expired_signals(self) -> int:
        """Remove expired signals and return count of removed signals"""
        current_time = int(time.time() * 1000)
        expired_keys = []
        
        for signal_id, signal in self.active_signals.items():
            if signal.is_expired():
                expired_keys.append(signal_id)
        
        for key in expired_keys:
            del self.active_signals[key]
        
        self.last_cleanup_time = time.time()
        return len(expired_keys)
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get comprehensive signal statistics"""
        # Cleanup first
        expired_count = self.cleanup_expired_signals()
        
        return {
            'total_signals_generated': self.total_signals_generated,
            'active_signals_count': len(self.active_signals),
            'expired_signals_cleaned': expired_count,
            'signal_types_distribution': self._get_signal_type_distribution(),
            'symbols_distribution': self._get_symbol_distribution(),
            'average_confidence': self._get_average_confidence(),
            'last_cleanup_time': self.last_cleanup_time
        }
    
    def _get_signal_type_distribution(self) -> Dict[str, int]:
        """Get distribution of active signals by type"""
        distribution = {}
        for signal in self.active_signals.values():
            signal_type = signal.signal_type.value
            distribution[signal_type] = distribution.get(signal_type, 0) + 1
        return distribution
    
    def _get_symbol_distribution(self) -> Dict[str, int]:
        """Get distribution of active signals by symbol"""
        distribution = {}
        for signal in self.active_signals.values():
            symbol = signal.symbol
            distribution[symbol] = distribution.get(symbol, 0) + 1
        return distribution
    
    def _get_average_confidence(self) -> float:
        """Get average confidence of active signals"""
        if not self.active_signals:
            return 0.0
        
        total_confidence = sum(signal.confidence for signal in self.active_signals.values())
        return total_confidence / len(self.active_signals) 
"""
ETH Tops and Bottoms Strategy for Backtesting Engine

This strategy implements the ETH tops and bottoms detection logic
for use with the backtesting engine framework.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from .backtest_strategy_base import BacktestStrategy, MarketEvent, Signal
from ..events.signal_event import SignalEvent


class ETHTopBottomBacktestStrategy(BacktestStrategy):
    """
    Backtesting implementation of the ETH tops and bottoms strategy.
    
    This strategy identifies potential tops and bottoms using:
    - Technical indicators (RSI, MACD, volume analysis)
    - Pattern recognition (divergences, support/resistance)
    - Volatility analysis (multi-timeframe)
    """
    
    def __init__(self, portfolio=None, config: Dict = None):
        """
        Initialize the ETH tops and bottoms strategy.
        
        Args:
            portfolio: Portfolio instance for position tracking
            config: Strategy configuration parameters
        """
        super().__init__(portfolio)
        
        # Default configuration
        self.config = config or {
            'technical_indicators': {
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'stochastic_k': 14,
                'stochastic_d': 3,
                'williams_r_period': 14
            },
            'signal_thresholds': {
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'volume_threshold': 1.5,  # Volume ratio threshold
                'confidence_min': 0.6
            },
            'position_sizing': {
                'base_size': 0.02,  # 2% of portfolio
                'max_size': 0.05,   # 5% of portfolio
                'confidence_multiplier': 1.5
            },
            'risk_management': {
                'stop_loss_pct': 0.05,  # 5% stop loss
                'take_profit_pct': 0.15,  # 15% take profit
                'max_positions': 3
            }
        }
        
        # Strategy state
        self.price_history = []
        self.technical_indicators = {}
        self.signal_history = []
        self.current_positions = {}
        
        self.logger = logging.getLogger(__name__)
        
    def get_name(self) -> str:
        """Return the strategy name."""
        return "ETH_Tops_Bottoms_Strategy"
    
    def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
        """
        Generate trading signals based on market event.
        
        Args:
            market_event: Market data event containing price/volume data
            
        Returns:
            List of trading signals to execute
        """
        try:
            # Update price history
            self._update_price_history(market_event)
            
            # Calculate technical indicators if we have enough data
            if len(self.price_history) < 50:
                return []
            
            # Calculate technical indicators
            self._calculate_technical_indicators()
            
            # Generate signals based on strategy logic
            signals = []
            
            # Check for top signals
            top_signal = self._check_for_top_signal(market_event)
            if top_signal:
                signals.append(top_signal)
            
            # Check for bottom signals
            bottom_signal = self._check_for_bottom_signal(market_event)
            if bottom_signal:
                signals.append(bottom_signal)
            
            # Check for divergence signals
            divergence_signals = self._check_for_divergence_signals(market_event)
            signals.extend(divergence_signals)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return []
    
    def _update_price_history(self, market_event: MarketEvent):
        """Update price history with new market data."""
        try:
            # Create price data point
            price_data = {
                'timestamp': market_event.timestamp,
                'open': getattr(market_event, 'open', market_event.price),
                'high': getattr(market_event, 'high', market_event.price),
                'low': getattr(market_event, 'low', market_event.price),
                'close': market_event.price,
                'volume': getattr(market_event, 'volume', 0)
            }
            
            self.price_history.append(price_data)
            
            # Keep only last 1000 data points for memory efficiency
            if len(self.price_history) > 1000:
                self.price_history = self.price_history[-1000:]
                
        except Exception as e:
            self.logger.error(f"Error updating price history: {e}")
    
    def _calculate_technical_indicators(self):
        """Calculate technical indicators for the price history."""
        try:
            if len(self.price_history) < 50:
                return
            
            # Convert to DataFrame for easier calculations
            df = pd.DataFrame(self.price_history)
            df.set_index('timestamp', inplace=True)
            
            # Calculate RSI
            df['rsi'] = self._calculate_rsi(df['close'])
            
            # Calculate MACD
            macd_data = self._calculate_macd(df['close'])
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']
            
            # Calculate Stochastic
            stoch_data = self._calculate_stochastic(df)
            df['stoch_k'] = stoch_data['k']
            df['stoch_d'] = stoch_data['d']
            
            # Calculate Williams %R
            df['williams_r'] = self._calculate_williams_r(df)
            
            # Calculate Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # Calculate Bollinger Bands
            bb_data = self._calculate_bollinger_bands(df['close'])
            df['bb_upper'] = bb_data['upper']
            df['bb_middle'] = bb_data['middle']
            df['bb_lower'] = bb_data['lower']
            
            # Calculate volatility
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            df['volatility_20'] = df['log_returns'].rolling(window=20).std() * np.sqrt(20)
            
            # Store indicators
            self.technical_indicators = df.to_dict('index')
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
    
    def _check_for_top_signal(self, market_event: MarketEvent) -> Optional[Signal]:
        """Check for potential top signals."""
        try:
            if len(self.price_history) < 30:
                return None
            
            current_data = self._get_current_indicators()
            if not current_data:
                return None
            
            # Get recent data for analysis
            recent_data = self._get_recent_data(20)
            
            # Top signal criteria
            price_at_resistance = self._is_price_at_resistance(current_data, recent_data)
            rsi_overbought = current_data.get('rsi', 50) > self.config['signal_thresholds']['rsi_overbought']
            macd_bearish = self._is_macd_bearish(current_data)
            volume_declining = self._is_volume_declining(current_data, recent_data)
            
            # Check if we have a top signal
            if (price_at_resistance and rsi_overbought and 
                (macd_bearish or volume_declining)):
                
                confidence = self._calculate_top_confidence(current_data, recent_data)
                
                if confidence >= self.config['signal_thresholds']['confidence_min']:
                    return self._create_signal(
                        market_event.symbol, 
                        'SELL', 
                        confidence,
                        f"Top signal: RSI={current_data.get('rsi', 0):.1f}, "
                        f"Price at resistance, MACD bearish"
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for top signal: {e}")
            return None
    
    def _check_for_bottom_signal(self, market_event: MarketEvent) -> Optional[Signal]:
        """Check for potential bottom signals."""
        try:
            if len(self.price_history) < 30:
                return None
            
            current_data = self._get_current_indicators()
            if not current_data:
                return None
            
            # Get recent data for analysis
            recent_data = self._get_recent_data(20)
            
            # Bottom signal criteria
            price_at_support = self._is_price_at_support(current_data, recent_data)
            rsi_oversold = current_data.get('rsi', 50) < self.config['signal_thresholds']['rsi_oversold']
            macd_bullish = self._is_macd_bullish(current_data)
            volume_increasing = self._is_volume_increasing(current_data, recent_data)
            
            # Check if we have a bottom signal
            if (price_at_support and rsi_oversold and 
                (macd_bullish or volume_increasing)):
                
                confidence = self._calculate_bottom_confidence(current_data, recent_data)
                
                if confidence >= self.config['signal_thresholds']['confidence_min']:
                    return self._create_signal(
                        market_event.symbol, 
                        'BUY', 
                        confidence,
                        f"Bottom signal: RSI={current_data.get('rsi', 0):.1f}, "
                        f"Price at support, MACD bullish"
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for bottom signal: {e}")
            return None
    
    def _check_for_divergence_signals(self, market_event: MarketEvent) -> List[Signal]:
        """Check for divergence signals."""
        signals = []
        
        try:
            if len(self.price_history) < 30:
                return signals
            
            current_data = self._get_current_indicators()
            if not current_data:
                return signals
            
            # Check for RSI divergence
            rsi_divergence = self._check_rsi_divergence()
            if rsi_divergence:
                confidence = 0.7  # Divergence signals get moderate confidence
                action = 'SELL' if rsi_divergence['direction'] == 'bearish' else 'BUY'
                signals.append(self._create_signal(
                    market_event.symbol, 
                    action, 
                    confidence,
                    f"RSI divergence: {rsi_divergence['direction']}"
                ))
            
            # Check for MACD divergence
            macd_divergence = self._check_macd_divergence()
            if macd_divergence:
                confidence = 0.65  # MACD divergence gets slightly lower confidence
                action = 'SELL' if macd_divergence['direction'] == 'bearish' else 'BUY'
                signals.append(self._create_signal(
                    market_event.symbol, 
                    action, 
                    confidence,
                    f"MACD divergence: {macd_divergence['direction']}"
                ))
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error checking for divergence signals: {e}")
            return signals
    
    def _get_current_indicators(self) -> Optional[Dict]:
        """Get current technical indicators."""
        try:
            if not self.technical_indicators:
                return None
            
            # Get the most recent data
            latest_timestamp = max(self.technical_indicators.keys())
            return self.technical_indicators[latest_timestamp]
            
        except Exception as e:
            self.logger.error(f"Error getting current indicators: {e}")
            return None
    
    def _get_recent_data(self, periods: int) -> List[Dict]:
        """Get recent price and indicator data."""
        try:
            if len(self.price_history) < periods:
                return []
            
            return self.price_history[-periods:]
            
        except Exception as e:
            self.logger.error(f"Error getting recent data: {e}")
            return []
    
    def _is_price_at_resistance(self, current: Dict, recent: List[Dict]) -> bool:
        """Check if price is at resistance level."""
        try:
            if not recent:
                return False
            
            current_price = current.get('close', 0)
            recent_highs = [d.get('high', 0) for d in recent]
            max_recent_high = max(recent_highs) if recent_highs else 0
            
            # Price within 2% of recent high
            return current_price >= max_recent_high * 0.98
            
        except Exception as e:
            self.logger.error(f"Error checking resistance: {e}")
            return False
    
    def _is_price_at_support(self, current: Dict, recent: List[Dict]) -> bool:
        """Check if price is at support level."""
        try:
            if not recent:
                return False
            
            current_price = current.get('close', 0)
            recent_lows = [d.get('low', 0) for d in recent]
            min_recent_low = min(recent_lows) if recent_lows else 0
            
            # Price within 2% of recent low
            return current_price <= min_recent_low * 1.02
            
        except Exception as e:
            self.logger.error(f"Error checking support: {e}")
            return False
    
    def _is_macd_bearish(self, current: Dict) -> bool:
        """Check if MACD is bearish."""
        try:
            macd = current.get('macd', 0)
            macd_signal = current.get('macd_signal', 0)
            return macd < macd_signal
            
        except Exception as e:
            self.logger.error(f"Error checking MACD bearish: {e}")
            return False
    
    def _is_macd_bullish(self, current: Dict) -> bool:
        """Check if MACD is bullish."""
        try:
            macd = current.get('macd', 0)
            macd_signal = current.get('macd_signal', 0)
            return macd > macd_signal
            
        except Exception as e:
            self.logger.error(f"Error checking MACD bullish: {e}")
            return False
    
    def _is_volume_declining(self, current: Dict, recent: List[Dict]) -> bool:
        """Check if volume is declining."""
        try:
            if not recent:
                return False
            
            current_volume = current.get('volume', 0)
            recent_volumes = [d.get('volume', 0) for d in recent]
            avg_recent_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            
            return current_volume < avg_recent_volume
            
        except Exception as e:
            self.logger.error(f"Error checking volume declining: {e}")
            return False
    
    def _is_volume_increasing(self, current: Dict, recent: List[Dict]) -> bool:
        """Check if volume is increasing."""
        try:
            if not recent:
                return False
            
            current_volume = current.get('volume', 0)
            recent_volumes = [d.get('volume', 0) for d in recent]
            avg_recent_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            
            return current_volume > avg_recent_volume * self.config['signal_thresholds']['volume_threshold']
            
        except Exception as e:
            self.logger.error(f"Error checking volume increasing: {e}")
            return False
    
    def _calculate_top_confidence(self, current: Dict, recent: List[Dict]) -> float:
        """Calculate confidence score for top signal."""
        try:
            confidence = 0.0
            
            # RSI factor
            rsi = current.get('rsi', 50)
            if rsi > 75:
                confidence += 0.3
            elif rsi > 70:
                confidence += 0.2
            
            # MACD factor
            if self._is_macd_bearish(current):
                confidence += 0.2
            
            # Volume factor
            if self._is_volume_declining(current, recent):
                confidence += 0.15
            
            # Price at resistance
            if self._is_price_at_resistance(current, recent):
                confidence += 0.15
            
            # Volatility factor
            volatility = current.get('volatility_20', 0)
            if volatility > 0.05:  # High volatility
                confidence += 0.1
            
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"Error calculating top confidence: {e}")
            return 0.0
    
    def _calculate_bottom_confidence(self, current: Dict, recent: List[Dict]) -> float:
        """Calculate confidence score for bottom signal."""
        try:
            confidence = 0.0
            
            # RSI factor
            rsi = current.get('rsi', 50)
            if rsi < 25:
                confidence += 0.3
            elif rsi < 30:
                confidence += 0.2
            
            # MACD factor
            if self._is_macd_bullish(current):
                confidence += 0.2
            
            # Volume factor
            if self._is_volume_increasing(current, recent):
                confidence += 0.15
            
            # Price at support
            if self._is_price_at_support(current, recent):
                confidence += 0.15
            
            # Volatility factor
            volatility = current.get('volatility_20', 0)
            if volatility > 0.05:  # High volatility
                confidence += 0.1
            
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"Error calculating bottom confidence: {e}")
            return 0.0
    
    def _check_rsi_divergence(self) -> Optional[Dict]:
        """Check for RSI divergence."""
        try:
            if len(self.price_history) < 20:
                return None
            
            recent_data = self.price_history[-20:]
            recent_indicators = [self.technical_indicators.get(d['timestamp'], {}) for d in recent_data]
            
            if len(recent_indicators) < 10:
                return None
            
            # Check for bearish divergence (price higher, RSI lower)
            price_trend = recent_data[-1]['close'] > recent_data[-10]['close']
            rsi_trend = recent_indicators[-1].get('rsi', 50) < recent_indicators[-10].get('rsi', 50)
            
            if price_trend and rsi_trend:
                return {'direction': 'bearish', 'type': 'RSI'}
            
            # Check for bullish divergence (price lower, RSI higher)
            price_trend = recent_data[-1]['close'] < recent_data[-10]['close']
            rsi_trend = recent_indicators[-1].get('rsi', 50) > recent_indicators[-10].get('rsi', 50)
            
            if price_trend and rsi_trend:
                return {'direction': 'bullish', 'type': 'RSI'}
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking RSI divergence: {e}")
            return None
    
    def _check_macd_divergence(self) -> Optional[Dict]:
        """Check for MACD divergence."""
        try:
            if len(self.price_history) < 20:
                return None
            
            recent_data = self.price_history[-20:]
            recent_indicators = [self.technical_indicators.get(d['timestamp'], {}) for d in recent_data]
            
            if len(recent_indicators) < 10:
                return None
            
            # Check for bearish divergence (price higher, MACD lower)
            price_trend = recent_data[-1]['close'] > recent_data[-10]['close']
            macd_trend = recent_indicators[-1].get('macd', 0) < recent_indicators[-10].get('macd', 0)
            
            if price_trend and macd_trend:
                return {'direction': 'bearish', 'type': 'MACD'}
            
            # Check for bullish divergence (price lower, MACD higher)
            price_trend = recent_data[-1]['close'] < recent_data[-10]['close']
            macd_trend = recent_indicators[-1].get('macd', 0) > recent_indicators[-10].get('macd', 0)
            
            if price_trend and macd_trend:
                return {'direction': 'bullish', 'type': 'MACD'}
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking MACD divergence: {e}")
            return None
    
    def _create_signal(self, symbol: str, action: str, confidence: float, reason: str) -> Signal:
        """Create a trading signal."""
        class SignalImpl:
            def __init__(self, symbol, action, strength, reason):
                self.symbol = symbol
                self.action = action
                self.strength = strength
                self.reason = reason
        
        return SignalImpl(symbol, action, confidence, reason)
    
    # Technical indicator calculation methods
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        fast_ema = prices.ewm(span=self.config['technical_indicators']['macd_fast']).mean()
        slow_ema = prices.ewm(span=self.config['technical_indicators']['macd_slow']).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=self.config['technical_indicators']['macd_signal']).mean()
        histogram = macd - signal
        
        return {'macd': macd, 'signal': signal, 'histogram': histogram}
    
    def _calculate_stochastic(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator."""
        k_period = self.config['technical_indicators']['stochastic_k']
        d_period = self.config['technical_indicators']['stochastic_d']
        
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        
        k = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=d_period).mean()
        
        return {'k': k, 'd': d}
    
    def _calculate_williams_r(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Williams %R indicator."""
        period = self.config['technical_indicators']['williams_r_period']
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        return williams_r
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {'upper': upper, 'middle': middle, 'lower': lower} 
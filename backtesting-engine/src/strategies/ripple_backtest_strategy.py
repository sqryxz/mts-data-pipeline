"""
Ripple (XRP) Backtesting Strategy

This strategy implements the Ripple trading logic for the backtesting engine,
leveraging XRP's unique characteristics including whale detection, macro correlations,
and technical patterns optimized for XRP's volatility.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from .backtest_strategy_base import BacktestStrategy, MarketEvent, Signal
from ..events.signal_event import SignalEvent


class RippleBacktestStrategy(BacktestStrategy):
    """
    Backtesting implementation of the Ripple (XRP) trading strategy.
    
    This strategy leverages XRP's unique characteristics:
    - Whale detection and institutional volume patterns
    - BTC correlation analysis and decoupling detection
    - Macro environment impact (Dollar strength, VIX, rates)
    - Technical analysis optimized for XRP's volatility
    """
    
    def __init__(self, portfolio=None, config: Dict = None):
        """
        Initialize the Ripple backtesting strategy.
        
        Args:
            portfolio: Portfolio instance for position tracking
            config: Strategy configuration parameters
        """
        super().__init__(portfolio)
        
        # Default configuration
        self.config = config or {
            'technical_indicators': {
                'rsi_period': 14,
                'rsi_short_period': 7,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bollinger_period': 20,
                'bollinger_std': 2,
                'volume_ma_period': 20,
                'atr_period': 14
            },
            'ripple_specific': {
                'whale_volume_threshold': 2.0,
                'institutional_volume_threshold': 1.5,
                'correlation_with_btc_threshold': 0.7,
                'regulatory_sentiment_weight': 0.15,
                'bank_partnership_weight': 0.10
            },
            'signal_thresholds': {
                'rsi_overbought': 75,
                'rsi_oversold': 25,
                'rsi_extreme_overbought': 85,
                'rsi_extreme_oversold': 15,
                'volume_spike_threshold': 2.5,
                'price_momentum_threshold': 0.05,
                'volatility_spike_threshold': 3.0,
                'confidence_min': 0.65
            },
            'macro_correlations': {
                'dollar_strength_threshold': 115,
                'dollar_weakness_threshold': 105,
                'vix_fear_threshold': 25,
                'vix_complacency_threshold': 15,
                'treasury_yield_impact': 0.20,
                'credit_spread_impact': 0.25
            },
            'position_sizing': {
                'base_size': 0.025,
                'max_size': 0.06,
                'confidence_multiplier': 1.8,
                'volatility_adjustment': True,
                'correlation_adjustment': True
            },
            'risk_management': {
                'stop_loss_pct': 0.04,
                'take_profit_pct': 0.12,
                'trailing_stop_pct': 0.02,
                'max_positions': 2,
                'max_daily_trades': 3,
                'correlation_limit': 0.8
            },
            'time_filters': {
                'asian_hours_weight': 1.2,
                'european_hours_weight': 1.0,
                'us_hours_weight': 1.1,
                'weekend_discount': 0.8
            },
            'confidence_weights': {
                'technical': 0.35,
                'macro': 0.30,
                'volume': 0.20,
                'ripple_specific': 0.15
            }
        }
        
        # Strategy state
        self.price_history = []
        self.volume_history = []
        self.technical_indicators = {}
        self.signal_history = []
        self.current_positions = {}
        self.daily_trades = 0
        self.last_trade_date = None
        
        # XRP-specific state
        self.whale_activity_detected = False
        self.btc_correlation = 0.0
        self.macro_environment = 'neutral'
        self.volatility_regime = 'medium'
        
        self.logger = logging.getLogger(__name__)
        
    def get_name(self) -> str:
        """Return the strategy name."""
        return "Ripple_Strategy"
    
    def generate_signals(self, market_event: MarketEvent) -> List[Signal]:
        """
        Generate trading signals based on market event.
        
        Args:
            market_event: Market data event containing price/volume data
            
        Returns:
            List of trading signals to execute
        """
        try:
            # Update price and volume history
            self._update_market_history(market_event)
            
            # Calculate technical indicators if we have enough data
            if len(self.price_history) < 50:
                return []
            
            # Calculate technical indicators
            self._calculate_technical_indicators()
            
            # Update XRP-specific factors
            self._update_ripple_specific_factors(market_event)
            
            # Check daily trade limits
            if self._exceeded_daily_trade_limit(market_event.timestamp):
                return []
            
            # Generate signals based on strategy logic
            signals = []
            
            # Check for buy signals
            buy_signal = self._check_for_buy_signal(market_event)
            if buy_signal:
                signals.append(buy_signal)
                self._record_trade(market_event.timestamp)
            
            # Check for sell signals
            sell_signal = self._check_for_sell_signal(market_event)
            if sell_signal:
                signals.append(sell_signal)
                self._record_trade(market_event.timestamp)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return []
    
    def _update_market_history(self, market_event: MarketEvent):
        """Update price and volume history with new market data."""
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
            self.logger.error(f"Error updating market history: {e}")
    
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
            
            # Calculate Bollinger Bands
            bb_data = self._calculate_bollinger_bands(df['close'])
            df['bb_upper'] = bb_data['upper']
            df['bb_middle'] = bb_data['middle']
            df['bb_lower'] = bb_data['lower']
            
            # Calculate volume indicators
            df['volume_ma'] = df['volume'].rolling(window=self.config['technical_indicators']['volume_ma_period']).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            # Calculate momentum indicators
            df['price_momentum'] = df['close'].pct_change(periods=5)
            df['volatility'] = df['close'].pct_change().rolling(window=20).std()
            
            # Store the latest indicators
            latest = df.iloc[-1]
            self.technical_indicators = {
                'rsi': latest['rsi'],
                'macd': latest['macd'],
                'macd_signal': latest['macd_signal'],
                'macd_histogram': latest['macd_histogram'],
                'bb_upper': latest['bb_upper'],
                'bb_middle': latest['bb_middle'],
                'bb_lower': latest['bb_lower'],
                'volume_ratio': latest['volume_ratio'],
                'price_momentum': latest['price_momentum'],
                'volatility': latest['volatility']
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
    
    def _update_ripple_specific_factors(self, market_event: MarketEvent):
        """Update XRP-specific factors like whale activity and macro environment."""
        try:
            # Detect whale activity
            volume_ratio = self.technical_indicators.get('volume_ratio', 1.0)
            whale_threshold = self.config['ripple_specific']['whale_volume_threshold']
            institutional_threshold = self.config['ripple_specific']['institutional_volume_threshold']
            
            self.whale_activity_detected = volume_ratio >= whale_threshold
            
            # Update volatility regime
            volatility = self.technical_indicators.get('volatility', 0.02)
            if volatility > 0.05:  # High volatility
                self.volatility_regime = 'high'
            elif volatility < 0.02:  # Low volatility
                self.volatility_regime = 'low'
            else:
                self.volatility_regime = 'medium'
            
            # Update macro environment (simplified for backtesting)
            # In real implementation, this would use actual macro data
            self.macro_environment = 'neutral'  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Error updating Ripple-specific factors: {e}")
    
    def _check_for_buy_signal(self, market_event: MarketEvent) -> Optional[Signal]:
        """Check for buy signal conditions."""
        try:
            if not self.technical_indicators:
                return None
            
            confidence_factors = []
            reasoning = []
            
            # Technical factors
            rsi = self.technical_indicators.get('rsi', 50)
            macd = self.technical_indicators.get('macd', 0)
            macd_signal = self.technical_indicators.get('macd_signal', 0)
            bb_lower = self.technical_indicators.get('bb_lower', 0)
            volume_ratio = self.technical_indicators.get('volume_ratio', 1.0)
            
            # RSI oversold condition
            if rsi < self.config['signal_thresholds']['rsi_oversold']:
                confidence_factors.append(0.25)
                reasoning.append(f"RSI oversold ({rsi:.1f})")
            elif rsi < self.config['signal_thresholds']['rsi_oversold'] + 10:
                confidence_factors.append(0.15)
                reasoning.append(f"RSI approaching oversold ({rsi:.1f})")
            
            # MACD bullish signal
            if macd > macd_signal:
                confidence_factors.append(0.20)
                reasoning.append("MACD bullish crossover")
            
            # Bollinger band bounce
            if market_event.price <= bb_lower * 1.02:
                confidence_factors.append(0.15)
                reasoning.append("Bollinger band support bounce")
            
            # Volume confirmation
            if volume_ratio >= self.config['ripple_specific']['whale_volume_threshold']:
                confidence_factors.append(0.20)
                reasoning.append("Whale accumulation detected")
            elif volume_ratio >= self.config['ripple_specific']['institutional_volume_threshold']:
                confidence_factors.append(0.10)
                reasoning.append("Institutional volume spike")
            
            # XRP-specific factors
            if self.whale_activity_detected:
                confidence_factors.append(0.15)
                reasoning.append("Whale activity confirmed")
            
            # Time-based boost
            time_weight = self._get_time_weight(market_event.timestamp)
            if time_weight > 1.0:
                confidence_factors.append(0.05)
                reasoning.append("Favorable trading hours")
            
            # Calculate total confidence
            base_confidence = sum(confidence_factors)
            adjusted_confidence = base_confidence * time_weight
            
            # Apply confidence weights
            weights = self.config['confidence_weights']
            final_confidence = (
                adjusted_confidence * weights.get('technical', 0.35) +
                (0.2 if self.whale_activity_detected else 0.1) * weights.get('volume', 0.20) +
                (0.15 if self.macro_environment == 'positive' else 0) * weights.get('macro', 0.30) +
                (0.1 if self.whale_activity_detected else 0) * weights.get('ripple_specific', 0.15)
            )
            
            # Check minimum confidence threshold
            min_confidence = self.config['signal_thresholds']['confidence_min']
            if final_confidence >= min_confidence:
                position_size = self._calculate_position_size(final_confidence)
                
                return self._create_signal(
                    symbol=market_event.symbol,
                    action="BUY",
                    confidence=final_confidence,
                    reason=' | '.join(reasoning)
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking buy conditions: {e}")
            return None
    
    def _check_for_sell_signal(self, market_event: MarketEvent) -> Optional[Signal]:
        """Check for sell signal conditions."""
        try:
            if not self.technical_indicators:
                return None
            
            confidence_factors = []
            reasoning = []
            
            # Technical factors
            rsi = self.technical_indicators.get('rsi', 50)
            macd = self.technical_indicators.get('macd', 0)
            macd_signal = self.technical_indicators.get('macd_signal', 0)
            bb_upper = self.technical_indicators.get('bb_upper', 0)
            volume_ratio = self.technical_indicators.get('volume_ratio', 1.0)
            
            # RSI overbought condition
            if rsi > self.config['signal_thresholds']['rsi_overbought']:
                confidence_factors.append(0.25)
                reasoning.append(f"RSI overbought ({rsi:.1f})")
            elif rsi > self.config['signal_thresholds']['rsi_overbought'] - 10:
                confidence_factors.append(0.15)
                reasoning.append(f"RSI approaching overbought ({rsi:.1f})")
            
            # MACD bearish signal
            if macd < macd_signal:
                confidence_factors.append(0.20)
                reasoning.append("MACD bearish crossover")
            
            # Bollinger band rejection
            if market_event.price >= bb_upper * 0.98:
                confidence_factors.append(0.15)
                reasoning.append("Bollinger band resistance rejection")
            
            # Volume confirmation (selling pressure)
            if volume_ratio > self.config['signal_thresholds']['volume_spike_threshold']:
                confidence_factors.append(0.20)
                reasoning.append("High volume selling pressure")
            
            # Calculate confidence similar to buy conditions
            base_confidence = sum(confidence_factors)
            time_weight = self._get_time_weight(market_event.timestamp)
            
            weights = self.config['confidence_weights']
            final_confidence = base_confidence * (
                weights.get('technical', 0.35) + 
                weights.get('volume', 0.20) + 
                weights.get('macro', 0.30)
            )
            
            min_confidence = self.config['signal_thresholds']['confidence_min']
            if final_confidence >= min_confidence:
                position_size = self._calculate_position_size(final_confidence)
                
                return self._create_signal(
                    symbol=market_event.symbol,
                    action="SELL",
                    confidence=final_confidence,
                    reason=' | '.join(reasoning)
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking sell conditions: {e}")
            return None
    
    def _calculate_position_size(self, confidence: float) -> float:
        """Calculate position size based on confidence and risk factors."""
        base_size = self.config['position_sizing']['base_size']
        max_size = self.config['position_sizing']['max_size']
        confidence_mult = self.config['position_sizing']['confidence_multiplier']
        
        # Adjust for confidence
        size = base_size * (1 + (confidence - 0.5) * confidence_mult)
        
        # Adjust for volatility
        if self.volatility_regime == 'high':
            size *= 0.7
        elif self.volatility_regime == 'low':
            size *= 1.2
        
        return min(size, max_size)
    
    def _get_time_weight(self, timestamp: datetime) -> float:
        """Get time-based weight for signals."""
        hour = timestamp.hour
        
        # Asian hours (important for XRP)
        if 22 <= hour or hour <= 6:
            return self.config['time_filters']['asian_hours_weight']
        # European hours
        elif 7 <= hour <= 15:
            return self.config['time_filters']['european_hours_weight']
        # US hours
        elif 14 <= hour <= 21:
            return self.config['time_filters']['us_hours_weight']
        
        return 1.0
    
    def _exceeded_daily_trade_limit(self, timestamp: datetime) -> bool:
        """Check if daily trade limit has been exceeded."""
        current_date = timestamp.date()
        
        # Reset daily counter if it's a new day
        if self.last_trade_date != current_date:
            self.daily_trades = 0
            self.last_trade_date = current_date
        
        max_daily_trades = self.config['risk_management']['max_daily_trades']
        return self.daily_trades >= max_daily_trades
    
    def _record_trade(self, timestamp: datetime):
        """Record a trade for daily limit tracking."""
        self.daily_trades += 1
        self.last_trade_date = timestamp.date()
    
    def _create_signal(self, symbol: str, action: str, confidence: float, reason: str) -> Signal:
        """Create a trading signal."""
        class SignalImpl:
            def __init__(self, symbol, action, strength, reason):
                self.symbol = symbol
                self.action = action
                self.quantity = 1.0  # Will be calculated by portfolio manager
                self.strength = strength
                self.reason = reason
        
        return SignalImpl(symbol, action, confidence, reason)
    
    # Technical indicator calculation methods
    def _calculate_rsi(self, prices: pd.Series, period: int = None) -> pd.Series:
        """Calculate RSI indicator."""
        if period is None:
            period = self.config['technical_indicators']['rsi_period']
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        fast = self.config['technical_indicators']['macd_fast']
        slow = self.config['technical_indicators']['macd_slow']
        signal = self.config['technical_indicators']['macd_signal']
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        period = self.config['technical_indicators']['bollinger_period']
        std_mult = self.config['technical_indicators']['bollinger_std']
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_mult)
        lower = sma - (std * std_mult)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower
        } 
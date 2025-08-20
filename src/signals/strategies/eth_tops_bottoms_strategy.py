#!/usr/bin/env python3
"""
ETH Tops and Bottoms Strategy Implementation

This script implements a comprehensive strategy for capturing ETH tops and bottoms
using technical analysis, macro indicators, and volatility patterns.

Author: AI Assistant
Date: 2025
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

from src.data.sqlite_helper import CryptoDatabase
from .base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalDirection, SignalStrength

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETHTopBottomStrategy(SignalStrategy):
    """
    Comprehensive strategy for identifying ETH tops and bottoms using
    technical analysis, macro indicators, and volatility patterns.
    """
    
    def __init__(self, config_path: str):
        """Initialize the strategy with configuration file path."""
        super().__init__(config_path)
        
        # Load additional configuration if needed
        self.database = CryptoDatabase()
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market conditions and return analysis results."""
        try:
            # Extract ETH data from market_data
            eth_data = market_data.get('ethereum', pd.DataFrame())
            if eth_data.empty:
                return {'error': 'No ETH data available'}
            
            # Run the existing analysis
            analysis = self.analyze_market(days=30)  # Use 30 days for analysis
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in analyze method: {e}")
            return {'error': str(e)}
    
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """Generate trading signals from analysis results."""
        try:
            signals = []
            
            # Check if analysis was successful
            if 'error' in analysis_results:
                return signals
            
            # Extract signal information from analysis
            current_signal = analysis_results.get('current_signal', {})
            signal_type = current_signal.get('signal_type')
            confidence = current_signal.get('confidence', 0.0)
            price = current_signal.get('price', 0.0)
            
            if signal_type and confidence > 0.1:  # Only generate signals with confidence > 10%
                # Create TradingSignal
                signal = TradingSignal(
                    symbol='ETHUSDT',
                    signal_type=signal_type,
                    direction=SignalDirection.BUY if signal_type == SignalType.LONG else SignalDirection.SELL,
                    price=price,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    strategy_name='eth_tops_bottoms',
                    signal_strength=SignalStrength.MODERATE,
                    position_size=0.02,
                    metadata={
                        'strategy': 'ETHTopBottomStrategy',
                        'analysis_summary': analysis_results.get('summary', ''),
                        'technical_score': current_signal.get('technical_score', 0.0),
                        'macro_score': current_signal.get('macro_score', 0.0),
                        'volatility_score': current_signal.get('volatility_score', 0.0)
                    }
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return []
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters for logging/optimization."""
        return {
            'strategy_name': 'ETHTopBottomStrategy',
            'config': self.config,
            'technical_indicators': self.config.get('technical_indicators', {}),
            'macro_indicators': self.config.get('macro_indicators', []),
            'signal_thresholds': self.config.get('signal_thresholds', {}),
            'confidence_weights': self.config.get('confidence_weights', {})
        }
    
    def get_eth_data(self, days: int = 365) -> pd.DataFrame:
        """Retrieve ETH price data from database."""
        try:
            market_data = self.database.get_strategy_market_data(
                assets=['ethereum'], 
                days=days
            )
            
            if 'ethereum' in market_data and not market_data['ethereum'].empty:
                df = market_data['ethereum'].copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df
            else:
                raise ValueError("No ETH data found in database")
                
        except Exception as e:
            self.logger.error(f"Error retrieving ETH data: {e}")
            return pd.DataFrame()
    
    def get_macro_data(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Retrieve macro indicator data from database."""
        try:
            macro_data = {}
            
            for indicator in self.config['macro_indicators']:
                query = f"""
                SELECT date, value 
                FROM macro_indicators 
                WHERE indicator = '{indicator}' 
                AND date BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY date
                """
                
                df = pd.read_sql_query(query, self.database.conn)
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    macro_data[indicator] = df
                    
            return macro_data
            
        except Exception as e:
            self.logger.error(f"Error retrieving macro data: {e}")
            return {}
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for ETH price data."""
        try:
            # RSI
            df['rsi'] = self._calculate_rsi(df['close'], self.config['technical_indicators']['rsi_period'])
            
            # MACD
            macd_data = self._calculate_macd(df['close'])
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']
            
            # Stochastic Oscillator
            stoch_data = self._calculate_stochastic(df)
            df['stoch_k'] = stoch_data['k']
            df['stoch_d'] = stoch_data['d']
            
            # Williams %R
            df['williams_r'] = self._calculate_williams_r(df)
            
            # Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # Bollinger Bands
            bb_data = self._calculate_bollinger_bands(df['close'])
            df['bb_upper'] = bb_data['upper']
            df['bb_middle'] = bb_data['middle']
            df['bb_lower'] = bb_data['lower']
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def calculate_volatility_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility metrics for different time windows."""
        try:
            # Calculate log returns
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Rolling volatility for different windows
            for window in self.config['volatility_windows']:
                df[f'volatility_{window}m'] = df['log_returns'].rolling(window=window).std() * np.sqrt(window)
            
            # Historical volatility percentiles
            for window in self.config['volatility_windows']:
                vol_col = f'volatility_{window}m'
                if vol_col in df.columns:
                    df[f'{vol_col}_percentile'] = df[vol_col].rolling(window=252).rank(pct=True) * 100
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility metrics: {e}")
            return df
    
    def identify_patterns(self, df: pd.DataFrame) -> Dict[str, List]:
        """Identify potential top and bottom patterns."""
        patterns = {
            'tops': [],
            'bottoms': [],
            'divergences': []
        }
        
        try:
            # Identify potential tops
            for i in range(50, len(df) - 10):
                if self._is_potential_top(df, i):
                    patterns['tops'].append({
                        'index': i,
                        'timestamp': df.index[i],
                        'price': df['close'].iloc[i],
                        'confidence': self._calculate_top_confidence(df, i)
                    })
            
            # Identify potential bottoms
            for i in range(50, len(df) - 10):
                if self._is_potential_bottom(df, i):
                    patterns['bottoms'].append({
                        'index': i,
                        'timestamp': df.index[i],
                        'price': df['close'].iloc[i],
                        'confidence': self._calculate_bottom_confidence(df, i)
                    })
            
            # Identify divergences
            patterns['divergences'] = self._identify_divergences(df)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error identifying patterns: {e}")
            return patterns
    
    def _is_potential_top(self, df: pd.DataFrame, index: int) -> bool:
        """Check if current point is a potential top."""
        try:
            # Get recent data
            recent = df.iloc[index-20:index+10]
            current = df.iloc[index]
            
            # Price at resistance level
            price_at_resistance = current['close'] >= recent['high'].max() * 0.98
            
            # RSI overbought
            rsi_overbought = current['rsi'] > self.config['signal_thresholds']['rsi_overbought']
            
            # MACD bearish crossover
            macd_bearish = (current['macd'] < current['macd_signal'] and 
                           df.iloc[index-1]['macd'] > df.iloc[index-1]['macd_signal'])
            
            # Volume declining
            volume_declining = current['volume'] < recent['volume'].mean()
            
            # Price above moving averages but momentum weakening
            above_ma = (current['close'] > current['sma_20'] > current['sma_50'])
            momentum_weakening = current['rsi'] < df.iloc[index-5:index]['rsi'].max()
            
            return (price_at_resistance and rsi_overbought and 
                   (macd_bearish or volume_declining) and above_ma and momentum_weakening)
                   
        except Exception as e:
            self.logger.error(f"Error in _is_potential_top: {e}")
            return False
    
    def _is_potential_bottom(self, df: pd.DataFrame, index: int) -> bool:
        """Check if current point is a potential bottom."""
        try:
            # Get recent data
            recent = df.iloc[index-20:index+10]
            current = df.iloc[index]
            
            # Price at support level
            price_at_support = current['close'] <= recent['low'].min() * 1.02
            
            # RSI oversold
            rsi_oversold = current['rsi'] < self.config['signal_thresholds']['rsi_oversold']
            
            # MACD bullish crossover
            macd_bullish = (current['macd'] > current['macd_signal'] and 
                           df.iloc[index-1]['macd'] < df.iloc[index-1]['macd_signal'])
            
            # Volume increasing
            volume_increasing = current['volume'] > recent['volume'].mean()
            
            # Price below moving averages but momentum strengthening
            below_ma = (current['close'] < current['sma_20'] < current['sma_50'])
            momentum_strengthening = current['rsi'] > df.iloc[index-5:index]['rsi'].min()
            
            return (price_at_support and rsi_oversold and 
                   (macd_bullish or volume_increasing) and below_ma and momentum_strengthening)
                   
        except Exception as e:
            self.logger.error(f"Error in _is_potential_bottom: {e}")
            return False
    
    def _calculate_top_confidence(self, df: pd.DataFrame, index: int) -> float:
        """Calculate confidence score for potential top."""
        try:
            current = df.iloc[index]
            recent = df.iloc[index-20:index]
            
            confidence = 0.0
            
            # Technical factors
            if current['rsi'] > 75:
                confidence += 0.2
            elif current['rsi'] > 70:
                confidence += 0.15
                
            if current['macd'] < current['macd_signal']:
                confidence += 0.15
                
            if current['volume'] < recent['volume'].mean():
                confidence += 0.1
                
            if current['close'] > current['bb_upper']:
                confidence += 0.1
                
            # Volatility factors
            if 'volatility_60m' in current:
                if current['volatility_60m'] < recent['volatility_60m'].quantile(0.2):
                    confidence += 0.1
                    
            # Pattern factors
            if self._is_head_and_shoulders(df, index):
                confidence += 0.2
                
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"Error calculating top confidence: {e}")
            return 0.0
    
    def _calculate_bottom_confidence(self, df: pd.DataFrame, index: int) -> float:
        """Calculate confidence score for potential bottom."""
        try:
            current = df.iloc[index]
            recent = df.iloc[index-20:index]
            
            confidence = 0.0
            
            # Technical factors
            if current['rsi'] < 25:
                confidence += 0.2
            elif current['rsi'] < 30:
                confidence += 0.15
                
            if current['macd'] > current['macd_signal']:
                confidence += 0.15
                
            if current['volume'] > recent['volume'].mean():
                confidence += 0.1
                
            if current['close'] < current['bb_lower']:
                confidence += 0.1
                
            # Volatility factors
            if 'volatility_60m' in current:
                if current['volatility_60m'] > recent['volatility_60m'].quantile(0.8):
                    confidence += 0.1
                    
            # Pattern factors
            if self._is_double_bottom(df, index):
                confidence += 0.2
                
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"Error calculating bottom confidence: {e}")
            return 0.0
    
    def _identify_divergences(self, df: pd.DataFrame) -> List[Dict]:
        """Identify price vs indicator divergences."""
        divergences = []
        
        try:
            for i in range(50, len(df) - 10):
                # RSI divergence
                if self._is_rsi_divergence(df, i):
                    divergences.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'type': 'RSI_DIVERGENCE',
                        'direction': 'BEARISH' if df.iloc[i]['rsi'] < df.iloc[i-10]['rsi'] else 'BULLISH'
                    })
                    
                # MACD divergence
                if self._is_macd_divergence(df, i):
                    divergences.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'type': 'MACD_DIVERGENCE',
                        'direction': 'BEARISH' if df.iloc[i]['macd'] < df.iloc[i-10]['macd'] else 'BULLISH'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error identifying divergences: {e}")
            
        return divergences
    
    def _is_rsi_divergence(self, df: pd.DataFrame, index: int) -> bool:
        """Check for RSI divergence."""
        try:
            recent = df.iloc[index-20:index+1]
            
            # Price making higher high but RSI making lower high (bearish)
            price_higher = recent['close'].iloc[-1] > recent['close'].iloc[-10]
            rsi_lower = recent['rsi'].iloc[-1] < recent['rsi'].iloc[-10]
            
            # Price making lower low but RSI making higher low (bullish)
            price_lower = recent['close'].iloc[-1] < recent['close'].iloc[-10]
            rsi_higher = recent['rsi'].iloc[-1] > recent['rsi'].iloc[-10]
            
            return (price_higher and rsi_lower) or (price_lower and rsi_higher)
            
        except Exception as e:
            self.logger.error(f"Error checking RSI divergence: {e}")
            return False
    
    def _is_macd_divergence(self, df: pd.DataFrame, index: int) -> bool:
        """Check for MACD divergence."""
        try:
            recent = df.iloc[index-20:index+1]
            
            # Price making higher high but MACD making lower high (bearish)
            price_higher = recent['close'].iloc[-1] > recent['close'].iloc[-10]
            macd_lower = recent['macd'].iloc[-1] < recent['macd'].iloc[-10]
            
            # Price making lower low but MACD making higher low (bullish)
            price_lower = recent['close'].iloc[-1] < recent['close'].iloc[-10]
            macd_higher = recent['macd'].iloc[-1] > recent['macd'].iloc[-10]
            
            return (price_higher and macd_lower) or (price_lower and macd_higher)
            
        except Exception as e:
            self.logger.error(f"Error checking MACD divergence: {e}")
            return False
    
    def _is_head_and_shoulders(self, df: pd.DataFrame, index: int) -> bool:
        """Check for head and shoulders pattern."""
        # Simplified implementation - would need more sophisticated pattern recognition
        return False
    
    def _is_double_bottom(self, df: pd.DataFrame, index: int) -> bool:
        """Check for double bottom pattern."""
        # Simplified implementation - would need more sophisticated pattern recognition
        return False
    
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
    
    def analyze_market(self, days: int = 365) -> Dict:
        """Perform comprehensive market analysis."""
        try:
            self.logger.info("Starting comprehensive ETH market analysis...")
            
            # Get ETH data
            eth_data = self.get_eth_data(days)
            if eth_data.empty:
                raise ValueError("No ETH data available")
            
            # Calculate technical indicators
            eth_data = self.calculate_technical_indicators(eth_data)
            eth_data = self.calculate_volatility_metrics(eth_data)
            
            # Get macro data
            start_date = eth_data.index.min().strftime('%Y-%m-%d')
            end_date = eth_data.index.max().strftime('%Y-%m-%d')
            macro_data = self.get_macro_data(start_date, end_date)
            
            # Identify patterns
            patterns = self.identify_patterns(eth_data)
            
            # Generate analysis results
            analysis = {
                'eth_data': eth_data,
                'macro_data': macro_data,
                'patterns': patterns,
                'summary': self._generate_summary(eth_data, patterns)
            }
            
            self.logger.info("Market analysis completed successfully")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {e}")
            return {}
    
    def _generate_summary(self, df: pd.DataFrame, patterns: Dict) -> Dict:
        """Generate analysis summary."""
        try:
            summary = {
                'data_period': f"{df.index.min()} to {df.index.max()}",
                'total_records': len(df),
                'price_range': f"${df['close'].min():,.2f} - ${df['close'].max():,.2f}",
                'current_price': f"${df['close'].iloc[-1]:,.2f}",
                'current_rsi': f"{df['rsi'].iloc[-1]:.1f}",
                'current_macd': f"{df['macd'].iloc[-1]:.4f}",
                'tops_identified': len(patterns['tops']),
                'bottoms_identified': len(patterns['bottoms']),
                'divergences_identified': len(patterns['divergences']),
                'recent_patterns': self._get_recent_patterns(patterns, 30)  # Last 30 days
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return {}
    
    def _get_recent_patterns(self, patterns: Dict, days: int) -> List[Dict]:
        """Get patterns from the last N days."""
        try:
            recent_patterns = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if pattern['timestamp'] >= cutoff_date:
                        recent_patterns.append({
                            'type': pattern_type,
                            'timestamp': pattern['timestamp'],
                            'price': pattern.get('price', 0),
                            'confidence': pattern.get('confidence', 0)
                        })
            
            return sorted(recent_patterns, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting recent patterns: {e}")
            return []


def main():
    """Main function to demonstrate the ETH tops and bottoms strategy."""
    
    print("🚀 ETH Tops and Bottoms Strategy Analysis")
    print("=" * 60)
    print()
    
    # Initialize strategy
    strategy = ETHTopBottomStrategy()
    
    # Perform analysis
    print("📊 Analyzing ETH market data...")
    analysis = strategy.analyze_market(days=365)
    
    if not analysis:
        print("❌ Analysis failed. Please check data availability.")
        return
    
    # Display results
    summary = analysis['summary']
    patterns = analysis['patterns']
    
    print("📈 Analysis Results:")
    print(f"  • Data Period: {summary['data_period']}")
    print(f"  • Total Records: {summary['total_records']}")
    print(f"  • Price Range: {summary['price_range']}")
    print(f"  • Current Price: {summary['current_price']}")
    print(f"  • Current RSI: {summary['current_rsi']}")
    print(f"  • Current MACD: {summary['current_macd']}")
    print()
    
    print("🎯 Pattern Identification:")
    print(f"  • Tops Identified: {summary['tops_identified']}")
    print(f"  • Bottoms Identified: {summary['bottoms_identified']}")
    print(f"  • Divergences Identified: {summary['divergences_identified']}")
    print()
    
    # Display recent patterns
    recent_patterns = summary['recent_patterns']
    if recent_patterns:
        print("📅 Recent Patterns (Last 30 Days):")
        for pattern in recent_patterns[:5]:  # Show top 5
            print(f"  • {pattern['type'].upper()}: {pattern['timestamp'].strftime('%Y-%m-%d')} "
                  f"at ${pattern['price']:,.2f} (Confidence: {pattern['confidence']:.1%})")
    else:
        print("📅 No recent patterns identified")
    
    print()
    print("✅ Analysis completed successfully!")
    print()
    print("Next steps:")
    print("1. Review identified patterns for trading opportunities")
    print("2. Validate signals with additional technical analysis")
    print("3. Implement risk management rules")
    print("4. Begin paper trading with small position sizes")


if __name__ == "__main__":
    main() 
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from src.signals.strategies.base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection
from src.data.sqlite_helper import CryptoDatabase


class MomentumStrategy(SignalStrategy):
    """
    Strategy that generates trading signals based on price momentum.
    
    Logic:
    - Calculates short-term and long-term moving averages
    - Generates LONG signals when short-term MA > long-term MA (uptrend)
    - Generates SHORT signals when short-term MA < long-term MA (downtrend)
    - Uses RSI for overbought/oversold conditions
    - Position sizing based on momentum strength
    """
    
    def __init__(self, config_path: str = "config/strategies/momentum_strategy.json"):
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
        self.database = CryptoDatabase()
        
        # Extract configuration parameters
        self.assets = self.config.get('assets', ['bitcoin', 'ethereum'])
        self.short_window = self.config.get('short_window', 10)  # 10-period short MA
        self.long_window = self.config.get('long_window', 30)   # 30-period long MA
        self.rsi_window = self.config.get('rsi_window', 14)     # 14-period RSI
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.base_position_size = self.config.get('base_position_size', 0.02)
        self.max_position_size = self.config.get('max_position_size', 0.05)
        self.min_confidence = self.config.get('min_confidence', 0.6)
        
        self.logger.info(f"Momentum Strategy initialized with {len(self.assets)} assets, "
                        f"{self.short_window}/{self.long_window} MA windows, "
                        f"{self.rsi_window}-period RSI")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data to calculate momentum metrics and identify opportunities.
        
        Args:
            market_data: Dictionary containing market data for each asset
            
        Returns:
            Dictionary containing analysis results with momentum metrics and opportunities
        """
        self.logger.info("Starting momentum analysis")
        
        analysis_results = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'strategy_name': 'MomentumStrategy',
            'momentum_metrics': {},
            'opportunities': [],
            'market_conditions': {}
        }
        
        try:
            for asset in self.assets:
                if asset not in market_data:
                    self.logger.warning(f"No market data available for {asset}")
                    continue
                
                df = market_data[asset]
                if df.empty:
                    self.logger.warning(f"Empty dataframe for {asset}")
                    continue
                
                # Calculate momentum metrics
                momentum_metrics = self._calculate_momentum_metrics(df, asset)
                analysis_results['momentum_metrics'][asset] = momentum_metrics
                
                # Identify trading opportunities
                opportunities = self._identify_opportunities(df, asset, momentum_metrics)
                analysis_results['opportunities'].extend(opportunities)
                
                # Store market conditions
                analysis_results['market_conditions'][asset] = {
                    'short_ma': momentum_metrics['short_ma'],
                    'long_ma': momentum_metrics['long_ma'],
                    'rsi': momentum_metrics['rsi'],
                    'momentum_strength': momentum_metrics['momentum_strength'],
                    'price': df['close'].iloc[-1] if not df.empty else None
                }
            
            self.logger.info(f"Analysis complete. Found {len(analysis_results['opportunities'])} opportunities")
            
        except Exception as e:
            self.logger.error(f"Error during momentum analysis: {e}")
            raise
        
        return analysis_results
    
    def _calculate_momentum_metrics(self, df: pd.DataFrame, asset: str) -> Dict[str, Any]:
        """
        Calculate momentum indicators for the given asset.
        
        Args:
            df: DataFrame with OHLCV data
            asset: Asset symbol
            
        Returns:
            Dictionary containing momentum metrics
        """
        try:
            # Calculate moving averages
            short_ma = df['close'].rolling(window=self.short_window).mean()
            long_ma = df['close'].rolling(window=self.long_window).mean()
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Calculate momentum strength
            momentum_strength = (short_ma.iloc[-1] - long_ma.iloc[-1]) / long_ma.iloc[-1]
            
            # Calculate price momentum (rate of change)
            price_momentum = (df['close'].iloc[-1] - df['close'].iloc[-self.short_window]) / df['close'].iloc[-self.short_window]
            
            return {
                'short_ma': short_ma.iloc[-1],
                'long_ma': long_ma.iloc[-1],
                'rsi': rsi.iloc[-1],
                'momentum_strength': momentum_strength,
                'price_momentum': price_momentum,
                'ma_cross': short_ma.iloc[-1] > long_ma.iloc[-1],
                'rsi_overbought': rsi.iloc[-1] > self.rsi_overbought,
                'rsi_oversold': rsi.iloc[-1] < self.rsi_oversold
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum metrics for {asset}: {e}")
            return {}
    
    def _identify_opportunities(self, df: pd.DataFrame, asset: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify trading opportunities based on momentum metrics.
        
        Args:
            df: DataFrame with OHLCV data
            asset: Asset symbol
            metrics: Momentum metrics
            
        Returns:
            List of trading opportunities
        """
        opportunities = []
        
        try:
            current_price = df['close'].iloc[-1]
            
            # LONG signal: Short MA > Long MA and RSI not overbought
            if (metrics['ma_cross'] and 
                not metrics['rsi_overbought'] and 
                metrics['momentum_strength'] > 0.01):  # 1% momentum threshold
                
                confidence = min(0.9, 0.6 + abs(metrics['momentum_strength']) * 10)
                position_size = min(self.max_position_size, 
                                  self.base_position_size * (1 + abs(metrics['momentum_strength']) * 5))
                
                opportunities.append({
                    'asset': asset,
                    'signal_type': 'LONG',
                    'direction': 'BUY',
                    'price': current_price,
                    'confidence': confidence,
                    'position_size': position_size,
                    'stop_loss': current_price * 0.95,  # 5% stop loss
                    'take_profit': current_price * 1.15,  # 15% take profit
                    'reason': f"Momentum uptrend: MA cross + {metrics['momentum_strength']:.2%} strength"
                })
            
            # SHORT signal: Short MA < Long MA and RSI not oversold
            elif (not metrics['ma_cross'] and 
                  not metrics['rsi_oversold'] and 
                  metrics['momentum_strength'] < -0.01):  # -1% momentum threshold
                
                confidence = min(0.9, 0.6 + abs(metrics['momentum_strength']) * 10)
                position_size = min(self.max_position_size, 
                                  self.base_position_size * (1 + abs(metrics['momentum_strength']) * 5))
                
                opportunities.append({
                    'asset': asset,
                    'signal_type': 'SHORT',
                    'direction': 'SELL',
                    'price': current_price,
                    'confidence': confidence,
                    'position_size': position_size,
                    'stop_loss': current_price * 1.05,  # 5% stop loss
                    'take_profit': current_price * 0.85,  # 15% take profit
                    'reason': f"Momentum downtrend: MA cross + {metrics['momentum_strength']:.2%} strength"
                })
            
        except Exception as e:
            self.logger.error(f"Error identifying opportunities for {asset}: {e}")
        
        return opportunities
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> List[TradingSignal]:
        """
        Generate trading signals from market data.
        
        Args:
            df: DataFrame with OHLCV data
            asset: Asset symbol
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        try:
            # Analyze the data
            market_data = {asset: df}
            analysis = self.analyze(market_data)
            
            # Convert opportunities to signals
            for opportunity in analysis['opportunities']:
                if opportunity['asset'] == asset:
                    signal = TradingSignal(
                        timestamp=int(datetime.now().timestamp() * 1000),
                        asset=asset,
                        signal_type=SignalType(opportunity['signal_type']),
                        direction=SignalDirection(opportunity['direction']),
                        price=opportunity['price'],
                        confidence=opportunity['confidence'],
                        strategy_name='MomentumStrategy',
                        position_size=opportunity['position_size'],
                        stop_loss=opportunity['stop_loss'],
                        take_profit=opportunity['take_profit'],
                        metadata={
                            'reason': opportunity['reason'],
                            'momentum_strength': analysis['momentum_metrics'][asset]['momentum_strength'],
                            'rsi': analysis['momentum_metrics'][asset]['rsi']
                        }
                    )
                    signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"Error generating signals for {asset}: {e}")
        
        return signals
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters for logging/optimization."""
        return {
            'strategy_name': 'MomentumStrategy',
            'short_window': self.short_window,
            'long_window': self.long_window,
            'rsi_window': self.rsi_window,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'base_position_size': self.base_position_size,
            'max_position_size': self.max_position_size,
            'min_confidence': self.min_confidence
        }

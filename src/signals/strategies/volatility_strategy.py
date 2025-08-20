import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from src.signals.strategies.base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection
from src.data.sqlite_helper import CryptoDatabase


class VolatilityStrategy(SignalStrategy):
    """
    Strategy that generates trading signals based on volatility breakouts.
    
    Logic:
    - Calculates 15-minute rolling volatility (standard deviation of returns)
    - Compares current volatility against historical thresholds (e.g., 95th percentile)
    - Generates LONG signals when volatility exceeds threshold (potential breakout)
    - Generates SHORT signals when volatility is extremely high (potential reversal)
    - Uses position sizing based on volatility magnitude
    """
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
        self.database = CryptoDatabase()
        
        # Extract configuration parameters
        self.assets = self.config.get('assets', ['bitcoin', 'ethereum'])
        self.volatility_window = self.config.get('volatility_window', 15)  # 15-minute window
        self.historical_hours = self.config.get('historical_hours', 24)  # 24-hour window as requested
        self.volatility_threshold_percentile = self.config.get('volatility_threshold_percentile', 90)  # 90th percentile as requested
        self.extreme_volatility_percentile = self.config.get('extreme_volatility_percentile', 95)
        self.base_position_size = self.config.get('base_position_size', 0.02)
        self.max_position_size = self.config.get('max_position_size', 0.05)
        self.min_confidence = self.config.get('min_confidence', 0.6)
        
        self.logger.info(f"Volatility Strategy initialized with {len(self.assets)} assets, "
                        f"{self.volatility_window}-minute window, "
                        f"{self.volatility_threshold_percentile}th percentile threshold, "
                        f"{self.historical_hours}-hour historical window")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data to calculate volatility metrics and identify opportunities.
        
        Args:
            market_data: Dictionary containing market data for each asset
            
        Returns:
            Dictionary containing analysis results with volatility metrics and opportunities
        """
        self.logger.info("Starting volatility analysis")
        
        analysis_results = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'strategy_name': 'VolatilityStrategy',
            'volatility_metrics': {},
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
                
                # Calculate volatility metrics
                volatility_metrics = self._calculate_volatility_metrics(df, asset)
                analysis_results['volatility_metrics'][asset] = volatility_metrics
                
                # Identify trading opportunities
                opportunities = self._identify_opportunities(df, asset, volatility_metrics)
                analysis_results['opportunities'].extend(opportunities)
                
                # Store market conditions
                analysis_results['market_conditions'][asset] = {
                    'current_volatility': volatility_metrics['current_volatility'],
                    'historical_threshold': volatility_metrics['historical_threshold'],
                    'volatility_percentile': volatility_metrics['volatility_percentile'],
                    'price': df['close'].iloc[-1] if not df.empty else None
                }
            
            self.logger.info(f"Analysis complete. Found {len(analysis_results['opportunities'])} opportunities")
            
        except Exception as e:
            self.logger.error(f"Error during volatility analysis: {e}")
            raise
        
        return analysis_results
    
    def _calculate_volatility_metrics(self, df: pd.DataFrame, asset: str) -> Dict[str, Any]:
        """
        Calculate volatility metrics for an asset.
        
        Args:
            df: DataFrame with OHLCV data
            asset: Asset name
            
        Returns:
            Dictionary containing volatility metrics
        """
        # Ensure data is sorted by timestamp
        df = df.sort_values('timestamp').copy()
        
        # Calculate returns (log returns for better statistical properties)
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Calculate rolling volatility (standard deviation of returns)
        # Adjust window based on actual data frequency
        # Use a minimum window size for daily data
        min_window = max(5, len(df) // 20)  # At least 5 periods, or 5% of data
        df['volatility'] = df['returns'].rolling(window=min_window).std() * np.sqrt(252)  # Annualized (252 trading days)
        
        # Calculate historical volatility threshold
        historical_volatility = df['volatility'].dropna()
        if len(historical_volatility) < 5:
            self.logger.warning(f"Insufficient data for {asset} volatility calculation")
            return {
                'current_volatility': 0.0,
                'historical_threshold': 0.0,
                'volatility_percentile': 0.0,
                'extreme_threshold': 0.0
            }
        
        historical_threshold = np.percentile(historical_volatility, self.volatility_threshold_percentile)
        extreme_threshold = np.percentile(historical_volatility, self.extreme_volatility_percentile)
        
        # Current volatility
        current_volatility = df['volatility'].iloc[-1] if not df['volatility'].isna().iloc[-1] else 0.0
        
        # Calculate percentile of current volatility
        volatility_percentile = np.percentile(historical_volatility, 
                                           [p for p in range(101) if np.percentile(historical_volatility, p) >= current_volatility][0])
        
        return {
            'current_volatility': current_volatility,
            'historical_threshold': historical_threshold,
            'extreme_threshold': extreme_threshold,
            'volatility_percentile': volatility_percentile,
            'historical_volatility_mean': historical_volatility.mean(),
            'historical_volatility_std': historical_volatility.std()
        }
    
    def _identify_opportunities(self, df: pd.DataFrame, asset: str, 
                               volatility_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify trading opportunities based on volatility analysis.
        
        Args:
            df: DataFrame with market data
            asset: Asset name
            volatility_metrics: Calculated volatility metrics
            
        Returns:
            List of trading opportunities
        """
        opportunities = []
        
        current_volatility = volatility_metrics['current_volatility']
        historical_threshold = volatility_metrics['historical_threshold']
        extreme_threshold = volatility_metrics['extreme_threshold']
        current_price = df['close'].iloc[-1]
        
        # Skip if insufficient data
        if current_volatility == 0.0 or historical_threshold == 0.0:
            return opportunities
        
        # Calculate signal strength based on volatility magnitude
        volatility_ratio = current_volatility / volatility_metrics['historical_volatility_mean']
        
        # LONG signal: Volatility breakout (above threshold but not extreme)
        if current_volatility > historical_threshold and current_volatility <= extreme_threshold:
            signal_strength = min(1.0, volatility_ratio / 2.0)  # Cap at 1.0
            confidence = min(0.9, 0.6 + (signal_strength * 0.3))
            
            opportunities.append({
                'asset': asset,
                'signal_type': 'LONG',
                'signal_strength': signal_strength,
                'confidence': confidence,
                'volatility': current_volatility,
                'threshold': historical_threshold,
                'volatility_ratio': volatility_ratio,
                'reason': f'Volatility breakout: {current_volatility:.2%} > {historical_threshold:.2%} threshold'
            })
        
        # SHORT signal: Extreme volatility (potential reversal)
        elif current_volatility > extreme_threshold:
            signal_strength = min(1.0, volatility_ratio / 3.0)  # More conservative for shorts
            confidence = min(0.8, 0.5 + (signal_strength * 0.3))
            
            opportunities.append({
                'asset': asset,
                'signal_type': 'SHORT',
                'signal_strength': signal_strength,
                'confidence': confidence,
                'volatility': current_volatility,
                'threshold': extreme_threshold,
                'volatility_ratio': volatility_ratio,
                'reason': f'Extreme volatility: {current_volatility:.2%} > {extreme_threshold:.2%} extreme threshold'
            })
        
        return opportunities
    
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """
        Generate trading signals from volatility analysis results.
        
        Args:
            analysis_results: Results from the analyze method
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        for opportunity in analysis_results.get('opportunities', []):
            try:
                asset = opportunity['asset']
                signal_type = opportunity['signal_type']
                signal_strength = opportunity['signal_strength']
                confidence = opportunity['confidence']
                current_price = analysis_results['market_conditions'][asset]['price']
                
                # Skip if confidence is too low
                if confidence < self.min_confidence:
                    continue
                
                # Calculate position size based on volatility and confidence
                position_size = self._calculate_position_size(signal_strength, confidence)
                
                # Calculate stop loss and take profit based on volatility
                stop_loss, take_profit = self._calculate_risk_levels(
                    current_price, signal_type, opportunity['volatility']
                )
                
                # Determine signal strength enum
                if signal_strength >= 0.8:
                    strength_enum = SignalStrength.STRONG
                elif signal_strength >= 0.6:
                    strength_enum = SignalStrength.MODERATE
                else:
                    strength_enum = SignalStrength.WEAK
                
                # Create trading signal
                signal = TradingSignal(
                    symbol=asset,
                    signal_type=SignalType(signal_type),
                    direction=SignalDirection.BUY if SignalType(signal_type) == SignalType.LONG else SignalDirection.SELL,
                    timestamp=analysis_results['timestamp'],
                    price=current_price,
                    strategy_name=analysis_results['strategy_name'],
                    signal_strength=strength_enum,
                    confidence=confidence,
                    position_size=position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    max_risk=0.02,  # Maximum 2% risk per trade
                    analysis_data={
                        'volatility': opportunity['volatility'],
                        'volatility_threshold': opportunity['threshold'],
                        'volatility_ratio': opportunity['volatility_ratio'],
                        'reason': opportunity['reason'],
                        'volatility_window_minutes': self.volatility_window
                    }
                )
                
                signals.append(signal)
                
                self.logger.info(f"Generated {signal_type} signal for {asset} "
                               f"(volatility: {opportunity['volatility']:.2%}, "
                               f"confidence: {confidence:.3f})")
                
            except Exception as e:
                self.logger.error(f"Failed to generate signal for {opportunity.get('asset', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Generated {len(signals)} volatility-based trading signals")
        return signals
    
    def _calculate_position_size(self, signal_strength: float, confidence: float) -> float:
        """
        Calculate position size based on signal strength and confidence.
        
        Args:
            signal_strength: Signal strength (0.0 to 1.0)
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Position size as percentage of portfolio
        """
        # Base position size adjusted by signal strength and confidence
        position_size = self.base_position_size * signal_strength * confidence
        
        # Cap at maximum position size
        return min(position_size, self.max_position_size)
    
    def _calculate_risk_levels(self, current_price: float, signal_type: str, 
                              volatility: float) -> tuple[Optional[float], Optional[float]]:
        """
        Calculate stop loss and take profit levels based on volatility.
        
        Args:
            current_price: Current asset price
            signal_type: Signal type (LONG or SHORT)
            volatility: Current volatility level
            
        Returns:
            Tuple of (stop_loss, take_profit) prices
        """
        # Use volatility to determine risk levels
        # Higher volatility = wider stops
        volatility_multiplier = min(3.0, max(1.0, volatility * 100))  # Scale volatility
        
        if signal_type == 'LONG':
            stop_loss = current_price * (1 - (0.02 * volatility_multiplier))  # 2% base stop
            take_profit = current_price * (1 + (0.04 * volatility_multiplier))  # 4% base target
        elif signal_type == 'SHORT':
            stop_loss = current_price * (1 + (0.02 * volatility_multiplier))
            take_profit = current_price * (1 - (0.04 * volatility_multiplier))
        else:
            return None, None
        
        return stop_loss, take_profit
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Return strategy parameters for logging and optimization.
        
        Returns:
            Dictionary containing strategy parameters
        """
        return {
            'assets': self.assets,
            'volatility_window': self.volatility_window,
            'historical_hours': self.historical_hours,
            'volatility_threshold_percentile': self.volatility_threshold_percentile,
            'extreme_volatility_percentile': self.extreme_volatility_percentile,
            'base_position_size': self.base_position_size,
            'max_position_size': self.max_position_size,
            'min_confidence': self.min_confidence
        } 
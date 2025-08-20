import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging

from src.signals.strategies.base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection
from src.data.sqlite_helper import CryptoDatabase


class VIXCorrelationStrategy(SignalStrategy):
    """
    Strategy that generates trading signals based on VIX-crypto correlation analysis.
    
    Logic:
    - LONG signals when VIX-crypto correlation < strong_negative threshold (e.g., -0.6)
    - SHORT signals when VIX-crypto correlation > strong_positive threshold (e.g., 0.6)
    - Uses rolling correlation windows to capture changing market dynamics
    """
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
        self.database = CryptoDatabase()
        
        # Extract configuration parameters
        self.assets = self.config.get('assets', ['bitcoin', 'ethereum', 'binancecoin'])
        self.correlation_thresholds = self.config.get('correlation_thresholds', {
            'strong_negative': -0.6,
            'strong_positive': 0.6
        })
        self.lookback_days = self.config.get('lookback_days', 30)
        self.position_size = self.config.get('position_size', 0.02)
        
        self.logger.info(f"VIX Correlation Strategy initialized with {len(self.assets)} assets, "
                        f"{self.lookback_days} day lookback")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze VIX-crypto correlations for all configured assets.
        
        Args:
            market_data: Optional market data (not used - strategy gets its own data)
            
        Returns:
            Dict containing correlation analysis results for each asset
        """
        analysis_results = {
            'timestamp': datetime.now(),
            'strategy_name': self.config.get('name', 'VIX_Correlation_Strategy'),
            'correlation_analysis': {},
            'signal_opportunities': []
        }
        
        for asset in self.assets:
            try:
                # Get combined crypto + VIX data from database
                df = self.database.get_combined_analysis_data(asset, days=self.lookback_days)
                
                if df.empty:
                    self.logger.warning(f"No data available for {asset}")
                    continue
                
                # Calculate correlations
                correlation_data = self._calculate_correlations(df, asset)
                analysis_results['correlation_analysis'][asset] = correlation_data
                
                # Check for signal opportunities
                if correlation_data['current_correlation'] is not None:
                    signal_opportunity = self._evaluate_signal_opportunity(asset, correlation_data)
                    if signal_opportunity:
                        analysis_results['signal_opportunities'].append(signal_opportunity)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {asset}: {e}")
                continue
        
        self.logger.info(f"Analyzed {len(analysis_results['correlation_analysis'])} assets, "
                        f"found {len(analysis_results['signal_opportunities'])} signal opportunities")
        
        return analysis_results
    
    def _calculate_correlations(self, df: pd.DataFrame, asset: str) -> Dict[str, Any]:
        """Calculate VIX-crypto correlations with multiple timeframes"""
        
        # Ensure we have both VIX and price data
        if 'vix_value' not in df.columns or df['vix_value'].isna().all():
            self.logger.warning(f"No VIX data available for {asset} correlation analysis")
            return {
                'current_correlation': None,
                'correlation_strength': 'INSUFFICIENT_DATA',
                'data_points': len(df),
                'vix_availability': 0.0
            }
        
        # Clean data - remove rows where either VIX or price is missing
        clean_df = df.dropna(subset=['vix_value', 'close'])
        
        if len(clean_df) < 10:  # Need minimum data points for correlation
            self.logger.warning(f"Insufficient clean data for {asset}: {len(clean_df)} points")
            return {
                'current_correlation': None,
                'correlation_strength': 'INSUFFICIENT_DATA',
                'data_points': len(clean_df),
                'vix_availability': len(clean_df) / len(df)
            }
        
        # Calculate rolling correlations with different windows
        correlation_windows = [7, 14, 21, 30]
        correlations = {}
        
        for window in correlation_windows:
            if len(clean_df) >= window:
                rolling_corr = clean_df['close'].rolling(window=window).corr(clean_df['vix_value'])
                correlations[f'{window}d_correlation'] = rolling_corr.iloc[-1]
        
        # Use the longest available window as current correlation
        current_correlation = None
        for window in reversed(correlation_windows):
            if f'{window}d_correlation' in correlations and not np.isnan(correlations[f'{window}d_correlation']):
                current_correlation = correlations[f'{window}d_correlation']
                break
        
        # Determine correlation strength
        correlation_strength = self._classify_correlation_strength(current_correlation)
        
        return {
            'current_correlation': current_correlation,
            'correlation_strength': correlation_strength,
            'correlations_by_window': correlations,
            'data_points': len(clean_df),
            'vix_availability': len(clean_df) / len(df),
            'latest_vix': clean_df['vix_value'].iloc[-1] if not clean_df.empty else None,
            'latest_price': clean_df['close'].iloc[-1] if not clean_df.empty else None
        }
    
    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength based on absolute value"""
        if correlation is None or np.isnan(correlation):
            return 'INSUFFICIENT_DATA'
        
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return 'VERY_STRONG'
        elif abs_corr >= 0.5:
            return 'STRONG'
        elif abs_corr >= 0.3:
            return 'MODERATE'
        elif abs_corr >= 0.1:
            return 'WEAK'
        else:
            return 'NEGLIGIBLE'
    
    def _evaluate_signal_opportunity(self, asset: str, correlation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if current correlation presents a trading opportunity"""
        correlation = correlation_data['current_correlation']
        
        if correlation is None:
            return None
        
        # Check against thresholds
        strong_negative = self.correlation_thresholds['strong_negative']
        strong_positive = self.correlation_thresholds['strong_positive']
        
        signal_type = None
        signal_strength = SignalStrength.WEAK
        confidence = 0.0
        
        if correlation <= strong_negative:
            # Strong negative correlation - crypto moves opposite to VIX
            # When VIX is high (fear), crypto tends to be low - potential LONG opportunity
            signal_type = SignalType.LONG
            confidence = min(abs(correlation) / abs(strong_negative), 1.0)
            signal_strength = SignalStrength.STRONG if confidence > 0.8 else SignalStrength.MODERATE
            
        elif correlation >= strong_positive:
            # Strong positive correlation - crypto moves with VIX
            # When VIX is high, crypto also high - potential SHORT opportunity
            signal_type = SignalType.SHORT
            confidence = min(correlation / strong_positive, 1.0)
            signal_strength = SignalStrength.STRONG if confidence > 0.8 else SignalStrength.MODERATE
        
        if signal_type:
            return {
                'asset': asset,
                'signal_type': signal_type,
                'signal_strength': signal_strength,
                'confidence': confidence,
                'correlation': correlation,
                'latest_price': correlation_data['latest_price'],
                'latest_vix': correlation_data['latest_vix']
            }
        
        return None
    
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """
        Generate trading signals based on correlation analysis.
        
        Args:
            analysis_results: Results from analyze() method
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        for opportunity in analysis_results.get('signal_opportunities', []):
            try:
                # Calculate risk management parameters
                current_price = opportunity['latest_price']
                vix_level = opportunity['latest_vix']
                
                # Adjust position size based on VIX level (higher VIX = more volatile = smaller position)
                vix_adjustment = max(0.5, min(1.0, 25.0 / max(vix_level, 10.0)))  # Scale based on VIX
                adjusted_position_size = self.position_size * vix_adjustment
                
                # Set stop loss and take profit based on signal type and VIX
                if opportunity['signal_type'] == SignalType.LONG:
                    stop_loss = current_price * 0.95  # 5% stop loss
                    take_profit = current_price * 1.10  # 10% take profit
                elif opportunity['signal_type'] == SignalType.SHORT:
                    stop_loss = current_price * 1.05  # 5% stop loss
                    take_profit = current_price * 0.90  # 10% take profit
                else:
                    stop_loss = None
                    take_profit = None
                
                # Create trading signal
                signal = TradingSignal(
                    symbol=opportunity['asset'],
                    signal_type=opportunity['signal_type'],
                    direction=SignalDirection.BUY if opportunity['signal_type'] == SignalType.LONG else SignalDirection.SELL,
                    timestamp=analysis_results['timestamp'],
                    price=current_price,
                    strategy_name=analysis_results['strategy_name'],
                    signal_strength=opportunity['signal_strength'],
                    confidence=opportunity['confidence'],
                    position_size=adjusted_position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    max_risk=0.02,  # Maximum 2% risk per trade
                    correlation_value=opportunity['correlation'],
                    analysis_data={
                        'vix_level': vix_level,
                        'correlation_strength': self._classify_correlation_strength(opportunity['correlation']),
                        'vix_adjustment_factor': vix_adjustment
                    }
                )
                
                signals.append(signal)
                
                self.logger.info(f"Generated {signal.signal_type.value} signal for {signal.symbol} "
                               f"(correlation: {opportunity['correlation']:.3f}, "
                               f"confidence: {signal.confidence:.3f})")
                
            except Exception as e:
                self.logger.error(f"Failed to generate signal for {opportunity.get('asset', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Generated {len(signals)} trading signals")
        return signals
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters for logging/optimization"""
        return {
            'strategy_name': self.config.get('name', 'VIX_Correlation_Strategy'),
            'assets': self.assets,
            'correlation_thresholds': self.correlation_thresholds,
            'lookback_days': self.lookback_days,
            'position_size': self.position_size,
            'version': '1.0.0'
        } 
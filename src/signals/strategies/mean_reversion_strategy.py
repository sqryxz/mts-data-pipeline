import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging

from src.signals.strategies.base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength
from src.data.sqlite_helper import CryptoDatabase


class MeanReversionStrategy(SignalStrategy):
    """
    Strategy that generates mean reversion signals based on VIX spikes and crypto drawdowns.
    
    Logic:
    - LONG signals when VIX > spike threshold (e.g., 25) AND crypto drawdown > threshold (e.g., 10%)
    - Based on the premise that high VIX + oversold crypto conditions create mean reversion opportunities
    - Uses rolling highs to calculate drawdowns from recent peaks
    """
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
        self.database = CryptoDatabase()
        
        # Extract configuration parameters
        self.assets = self.config.get('assets', ['bitcoin', 'ethereum', 'binancecoin'])
        self.vix_spike_threshold = self.config.get('vix_spike_threshold', 25)
        self.drawdown_threshold = self.config.get('drawdown_threshold', 0.10)  # 10%
        self.lookback_days = self.config.get('lookback_days', 14)
        self.position_size = self.config.get('position_size', 0.025)
        
        self.logger.info(f"Mean Reversion Strategy initialized with {len(self.assets)} assets, "
                        f"VIX threshold: {self.vix_spike_threshold}, "
                        f"drawdown threshold: {self.drawdown_threshold*100}%")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market conditions for mean reversion opportunities.
        
        Args:
            market_data: Optional market data (not used - strategy gets its own data)
            
        Returns:
            Dict containing analysis results for each asset
        """
        analysis_results = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'strategy_name': self.config.get('name', 'Mean_Reversion_Strategy'),
            'market_analysis': {},
            'signal_opportunities': []
        }
        
        for asset in self.assets:
            try:
                # Get combined crypto + VIX data from database
                df = self.database.get_combined_analysis_data(asset, days=self.lookback_days)
                
                if df.empty:
                    self.logger.warning(f"No data available for {asset}")
                    continue
                
                # Analyze mean reversion conditions
                asset_analysis = self._analyze_mean_reversion_conditions(df, asset)
                analysis_results['market_analysis'][asset] = asset_analysis
                
                # Check for signal opportunities
                if asset_analysis['meets_criteria']:
                    signal_opportunity = self._evaluate_mean_reversion_opportunity(asset, asset_analysis)
                    if signal_opportunity:
                        analysis_results['signal_opportunities'].append(signal_opportunity)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {asset}: {e}")
                continue
        
        self.logger.info(f"Analyzed {len(analysis_results['market_analysis'])} assets, "
                        f"found {len(analysis_results['signal_opportunities'])} mean reversion opportunities")
        
        return analysis_results
    
    def _analyze_mean_reversion_conditions(self, df: pd.DataFrame, asset: str) -> Dict[str, Any]:
        """Analyze VIX spike and crypto drawdown conditions"""
        
        # Check if we have VIX data
        if 'vix_value' not in df.columns or df['vix_value'].isna().all():
            self.logger.warning(f"No VIX data available for {asset} analysis")
            return {
                'meets_criteria': False,
                'reason': 'NO_VIX_DATA',
                'current_vix': None,
                'current_price': df['close'].iloc[-1] if not df.empty else None,
                'drawdown_from_high': None
            }
        
        # Clean data
        clean_df = df.dropna(subset=['vix_value', 'close'])
        
        if len(clean_df) < 5:  # Need minimum data points
            self.logger.warning(f"Insufficient data for {asset}: {len(clean_df)} points")
            return {
                'meets_criteria': False,
                'reason': 'INSUFFICIENT_DATA',
                'data_points': len(clean_df)
            }
        
        # Get current values
        current_vix = clean_df['vix_value'].iloc[-1]
        current_price = clean_df['close'].iloc[-1]
        
        # Check VIX spike condition
        vix_spike_detected = current_vix > self.vix_spike_threshold
        
        # Calculate drawdown from recent high
        # Use a rolling window to find the highest price in recent period
        rolling_window = min(len(clean_df), 14)  # 14-day rolling high
        rolling_high = clean_df['close'].rolling(window=rolling_window, min_periods=1).max()
        recent_high = rolling_high.iloc[-1]
        
        # Calculate current drawdown
        drawdown_from_high = (recent_high - current_price) / recent_high
        drawdown_condition_met = drawdown_from_high > self.drawdown_threshold
        
        # Calculate additional metrics
        vix_percentile = self._calculate_vix_percentile(clean_df['vix_value'])
        price_rsi = self._calculate_rsi(clean_df['close'])
        
        # Determine if conditions are met
        meets_criteria = vix_spike_detected and drawdown_condition_met
        
        return {
            'meets_criteria': meets_criteria,
            'current_vix': current_vix,
            'vix_spike_detected': vix_spike_detected,
            'vix_threshold': self.vix_spike_threshold,
            'current_price': current_price,
            'recent_high': recent_high,
            'drawdown_from_high': drawdown_from_high,
            'drawdown_condition_met': drawdown_condition_met,
            'drawdown_threshold': self.drawdown_threshold,
            'vix_percentile': vix_percentile,
            'price_rsi': price_rsi,
            'data_points': len(clean_df)
        }
    
    def _calculate_vix_percentile(self, vix_series: pd.Series) -> float:
        """Calculate current VIX percentile relative to recent history"""
        if len(vix_series) < 2:
            return 50.0  # Default to 50th percentile
        
        current_vix = vix_series.iloc[-1]
        percentile = (vix_series < current_vix).sum() / len(vix_series) * 100
        return percentile
    
    def _calculate_rsi(self, price_series: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index) for price series"""
        if len(price_series) < period + 1:
            return 50.0  # Default to neutral RSI
        
        # Calculate price changes
        delta = price_series.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period, min_periods=1).mean()
        avg_losses = losses.rolling(window=period, min_periods=1).mean()
        
        # Calculate RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.empty else 50.0
    
    def _evaluate_mean_reversion_opportunity(self, asset: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the quality of the mean reversion opportunity"""
        
        # Calculate confidence based on multiple factors
        confidence_factors = []
        
        # VIX spike magnitude (higher = better for mean reversion)
        vix_excess = analysis['current_vix'] - analysis['vix_threshold']
        vix_factor = min(vix_excess / 10.0, 1.0)  # Normalize to 0-1
        confidence_factors.append(vix_factor)
        
        # Drawdown magnitude (deeper = higher confidence in bounce)
        drawdown_excess = analysis['drawdown_from_high'] - analysis['drawdown_threshold']
        drawdown_factor = min(drawdown_excess / 0.10, 1.0)  # Normalize to 0-1
        confidence_factors.append(drawdown_factor)
        
        # VIX percentile (higher percentile = more extreme = higher confidence)
        vix_percentile_factor = analysis['vix_percentile'] / 100.0
        confidence_factors.append(vix_percentile_factor)
        
        # RSI oversold condition (lower RSI = higher confidence)
        rsi_factor = max(0, (30 - analysis['price_rsi']) / 30)  # RSI < 30 is oversold
        confidence_factors.append(max(rsi_factor, 0.1))  # Minimum 0.1 factor
        
        # Calculate overall confidence
        confidence = np.mean(confidence_factors)
        
        # Determine signal strength
        if confidence > 0.7:
            signal_strength = SignalStrength.STRONG
        elif confidence > 0.5:
            signal_strength = SignalStrength.MODERATE
        else:
            signal_strength = SignalStrength.WEAK
        
        return {
            'asset': asset,
            'signal_type': SignalType.LONG,  # Mean reversion always generates LONG signals
            'signal_strength': signal_strength,
            'confidence': confidence,
            'current_price': analysis['current_price'],
            'current_vix': analysis['current_vix'],
            'drawdown_from_high': analysis['drawdown_from_high'],
            'vix_percentile': analysis['vix_percentile'],
            'price_rsi': analysis['price_rsi'],
            'confidence_factors': {
                'vix_factor': vix_factor,
                'drawdown_factor': drawdown_factor,
                'vix_percentile_factor': vix_percentile_factor,
                'rsi_factor': rsi_factor
            }
        }
    
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """
        Generate mean reversion trading signals.
        
        Args:
            analysis_results: Results from analyze() method
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        for opportunity in analysis_results.get('signal_opportunities', []):
            try:
                # Get signal parameters
                current_price = opportunity['current_price']
                vix_level = opportunity['current_vix']
                confidence = opportunity['confidence']
                drawdown = opportunity['drawdown_from_high']
                
                # Adjust position size based on confidence and VIX level
                # Higher VIX = more volatility = smaller position
                # Higher confidence = larger position
                vix_adjustment = max(0.5, min(1.0, 25.0 / max(vix_level, 15.0)))
                confidence_adjustment = 0.5 + (confidence * 0.5)  # Scale from 0.5 to 1.0
                
                adjusted_position_size = self.position_size * vix_adjustment * confidence_adjustment
                adjusted_position_size = min(adjusted_position_size, 0.05)  # Cap at 5%
                
                # Set risk management parameters for mean reversion
                # Tighter stops for mean reversion due to higher probability
                stop_loss_pct = 0.03 + (drawdown * 0.5)  # 3-8% stop loss based on drawdown
                stop_loss = current_price * (1 - stop_loss_pct)
                
                # Take profit based on drawdown recovery
                take_profit_pct = drawdown * 0.6  # Target 60% recovery of drawdown
                take_profit = current_price * (1 + take_profit_pct)
                
                # Create trading signal
                signal = TradingSignal(
                    asset=opportunity['asset'],
                    signal_type=SignalType.LONG,
                    timestamp=analysis_results['timestamp'],
                    price=current_price,
                    strategy_name=analysis_results['strategy_name'],
                    signal_strength=opportunity['signal_strength'],
                    confidence=confidence,
                    position_size=adjusted_position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    max_risk=0.03,  # Maximum 3% risk per trade
                    analysis_data={
                        'vix_level': vix_level,
                        'drawdown_from_high': drawdown,
                        'vix_percentile': opportunity['vix_percentile'],
                        'price_rsi': opportunity['price_rsi'],
                        'vix_adjustment_factor': vix_adjustment,
                        'confidence_adjustment_factor': confidence_adjustment,
                        'stop_loss_pct': stop_loss_pct,
                        'take_profit_pct': take_profit_pct,
                        'confidence_factors': opportunity['confidence_factors']
                    }
                )
                
                signals.append(signal)
                
                self.logger.info(f"Generated {signal.signal_type.value} signal for {signal.asset} "
                               f"(VIX: {vix_level:.1f}, drawdown: {drawdown*100:.1f}%, "
                               f"confidence: {confidence:.3f})")
                
            except Exception as e:
                self.logger.error(f"Failed to generate signal for {opportunity.get('asset', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Generated {len(signals)} mean reversion signals")
        return signals
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters for logging/optimization"""
        return {
            'strategy_name': self.config.get('name', 'Mean_Reversion_Strategy'),
            'assets': self.assets,
            'vix_spike_threshold': self.vix_spike_threshold,
            'drawdown_threshold': self.drawdown_threshold,
            'lookback_days': self.lookback_days,
            'position_size': self.position_size,
            'version': '1.0.0'
        } 
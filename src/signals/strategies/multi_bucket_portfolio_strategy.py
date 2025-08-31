"""
Multi-Bucket Crypto Portfolio Strategy

Systematic multi-bucket crypto portfolio exploiting:
1. Cross-sectional momentum (7/14/30d)
2. Residual (idiosyncratic) momentum after removing BTC/ETH beta
3. Mean-reversion on overextended short-term moves with RSI divergence
4. Pair/spread convergence (e.g. ETH-ENA)
5. Dynamic risk modulation via correlation regime
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.linear_model import LinearRegression
import warnings

from src.signals.strategies.base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection
from src.data.sqlite_helper import CryptoDatabase


class MultiBucketPortfolioStrategy(SignalStrategy):
    """
    Comprehensive multi-bucket crypto portfolio strategy implementing systematic
    momentum, residual analysis, mean-reversion, pair trading, and dynamic risk management.
    """
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
        self.database = CryptoDatabase()
        
        # Extract configuration parameters
        self.assets = self.config['assets']
        self.momentum_params = self.config['momentum_parameters']
        self.residual_params = self.config['residual_parameters']
        self.mean_reversion_params = self.config['mean_reversion_parameters']
        self.pair_params = self.config['pair_trade_parameters']
        self.correlation_params = self.config['correlation_regime_parameters']
        self.position_params = self.config['position_sizing']
        self.risk_params = self.config['risk_management']
        self.portfolio_params = self.config['portfolio_structure']
        self.entry_exit_params = self.config['entry_exit_rules']
        
        # Initialize state variables
        self.portfolio_state = {
            'peak_equity': None,
            'current_drawdown': 0.0,
            'risk_off_mode': False,
            'last_correlation_regime': None,
            'active_positions': {},
            'performance_metrics': {}
        }
        
        self.logger.info(f"Multi-Bucket Portfolio Strategy initialized with {len(self.assets['universe'])} assets")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive market analysis including momentum, residual, correlation, and regime analysis."""
        self.logger.info("Starting multi-bucket portfolio analysis")
        
        analysis_results = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'strategy_name': 'MultiBucketPortfolioStrategy',
            'momentum_analysis': {},
            'residual_analysis': {},
            'correlation_analysis': {},
            'pair_analysis': {},
            'regime_analysis': {},
            'opportunities': [],
            'risk_summary': {}
        }
        
        try:
            # 1. Momentum Analysis
            momentum_analysis = self._analyze_momentum(market_data)
            analysis_results['momentum_analysis'] = momentum_analysis
            
            # 2. Residual Analysis
            residual_analysis = self._analyze_residual_momentum(market_data)
            analysis_results['residual_analysis'] = residual_analysis
            
            # 3. Correlation Analysis
            correlation_analysis = self._analyze_correlations(market_data)
            analysis_results['correlation_analysis'] = correlation_analysis
            
            # 4. Pair Trading Analysis
            pair_analysis = self._analyze_pair_trades(market_data)
            analysis_results['pair_analysis'] = pair_analysis
            
            # 5. Regime Analysis
            regime_analysis = self._analyze_correlation_regime(correlation_analysis)
            analysis_results['regime_analysis'] = regime_analysis
            
            # 6. Generate Opportunities
            opportunities = self._generate_opportunities(
                momentum_analysis, residual_analysis, 
                correlation_analysis, pair_analysis, regime_analysis
            )
            analysis_results['opportunities'] = opportunities
            
            # 7. Risk Summary
            risk_summary = self._generate_risk_summary(
                opportunities, regime_analysis, market_data
            )
            analysis_results['risk_summary'] = risk_summary
            
            self.logger.info(f"Analysis complete. Found {len(opportunities)} opportunities")
            
        except Exception as e:
            self.logger.error(f"Error during multi-bucket analysis: {e}")
            raise
        
        return analysis_results
    
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """Generate trading signals from analysis results."""
        signals = []
        
        opportunities = analysis_results.get('opportunities', [])
        regime_analysis = analysis_results.get('regime_analysis', {})
        
        # Apply risk-off mode if triggered
        if regime_analysis.get('risk_off_trigger', False):
            self.portfolio_state['risk_off_mode'] = True
            self.logger.warning("Risk-off mode triggered - reducing position sizes")
        
        for opportunity in opportunities:
            try:
                signal = self._create_trading_signal(opportunity, regime_analysis)
                if signal:
                    signals.append(signal)
            except Exception as e:
                self.logger.error(f"Error creating signal for {opportunity.get('asset', 'unknown')}: {e}")
        
        return signals
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters for logging/optimization."""
        return {
            'strategy_name': 'MultiBucketPortfolioStrategy',
            'version': self.config.get('version', '1.0.0'),
            'momentum_parameters': self.momentum_params,
            'residual_parameters': self.residual_params,
            'correlation_parameters': self.correlation_params,
            'position_parameters': self.position_params,
            'risk_parameters': self.risk_params,
            'portfolio_state': self.portfolio_state
        }
    
    def _analyze_momentum(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cross-sectional momentum across multiple horizons."""
        momentum_analysis = {}
        
        for asset in self.assets['universe']:
            if asset not in market_data:
                continue
                
            df = market_data[asset]
            if df.empty or len(df) < max(self.momentum_params['horizons']):
                continue
            
            # Calculate momentum returns for each horizon
            momentum_returns = {}
            z_scores = {}
            
            for horizon in self.momentum_params['horizons']:
                if len(df) > horizon:
                    # Calculate momentum return
                    momentum_return = (df['close'].iloc[-1] / df['close'].iloc[-horizon-1]) - 1
                    momentum_returns[f'M{horizon}'] = momentum_return
                    
                    # Calculate z-score over rolling window
                    z_score = self._calculate_momentum_zscore(df, horizon)
                    z_scores[f'Z{horizon}'] = z_score
            
            # Composite momentum score
            if z_scores:
                composite_momentum = self._calculate_composite_momentum(z_scores)
                acceleration = momentum_returns.get('M7', 0) - momentum_returns.get('M14', 0)
                momentum_strength = self._calculate_momentum_strength(df, asset)
                
                momentum_analysis[asset] = {
                    'momentum_returns': momentum_returns,
                    'z_scores': z_scores,
                    'composite_momentum': composite_momentum,
                    'acceleration': acceleration,
                    'momentum_strength': momentum_strength,
                    'trend_alignment': self._check_trend_alignment(momentum_returns),
                    'current_price': df['close'].iloc[-1] if not df.empty else None
                }
        
        return momentum_analysis
    
    def _analyze_residual_momentum(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze residual momentum after removing BTC/ETH beta."""
        residual_analysis = {}
        
        # Get factor asset returns (BTC as primary factor)
        btc_returns = self._calculate_returns(market_data.get('bitcoin', pd.DataFrame()))
        if btc_returns.empty:
            return residual_analysis
        
        for asset in self.assets['universe']:
            if asset in self.assets['factor_assets'] or asset not in market_data:
                continue
                
            asset_returns = self._calculate_returns(market_data[asset])
            if asset_returns.empty or len(asset_returns) < self.residual_params['regression_window']:
                continue
            
            # Align returns
            aligned_returns = pd.concat([asset_returns, btc_returns], axis=1).dropna()
            if len(aligned_returns) < self.residual_params['regression_window']:
                continue
            
            # Calculate beta and residuals
            beta, residuals = self._calculate_beta_residuals(
                aligned_returns.iloc[:, 0],  # Asset returns
                aligned_returns.iloc[:, 1]   # BTC returns
            )
            
            if residuals is not None and len(residuals) >= self.residual_params['residual_window']:
                residual_zscore = self._calculate_residual_zscore(residuals)
                
                residual_analysis[asset] = {
                    'beta': beta,
                    'residuals': residuals[-self.residual_params['residual_window']:],
                    'residual_zscore': residual_zscore,
                    'residual_mean': np.mean(residuals[-self.residual_params['residual_window']:]),
                    'residual_std': np.std(residuals[-self.residual_params['residual_window']:])
                }
        
        return residual_analysis
    
    def _analyze_correlations(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlations across multiple timeframes."""
        correlation_analysis = {}
        
        # Calculate returns for all assets
        returns_data = {}
        for asset in self.assets['universe']:
            if asset in market_data:
                returns = self._calculate_returns(market_data[asset])
                if not returns.empty:
                    returns_data[asset] = returns
        
        if len(returns_data) < 2:
            return correlation_analysis
        
        # Calculate correlation matrix for each window
        for window in self.correlation_params['correlation_windows']:
            correlation_matrix = self._calculate_correlation_matrix(returns_data, window)
            correlation_analysis[f'{window}d'] = correlation_matrix
        
        # Calculate average correlation
        avg_correlation = self._calculate_average_correlation(correlation_analysis)
        correlation_analysis['average_correlation'] = avg_correlation
        
        return correlation_analysis
    
    def _analyze_pair_trades(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pair trading opportunities."""
        pair_analysis = {}
        
        for pair in self.assets['pairs']:
            long_asset = pair['long']
            short_asset = pair['short']
            pair_name = pair['name']
            
            if long_asset not in market_data or short_asset not in market_data:
                continue
            
            long_df = market_data[long_asset]
            short_df = market_data[short_asset]
            
            if long_df.empty or short_df.empty:
                continue
            
            # Calculate spread
            spread, spread_zscore, correlation_metrics = self._calculate_pair_spread(
                long_df, short_df, pair_name
            )
            
            if spread is not None:
                pair_analysis[pair_name] = {
                    'spread': spread,
                    'spread_zscore': spread_zscore,
                    'correlation_metrics': correlation_metrics,
                    'long_price': long_df['close'].iloc[-1] if not long_df.empty else None,
                    'short_price': short_df['close'].iloc[-1] if not short_df.empty else None
                }
        
        return pair_analysis
    
    def _analyze_correlation_regime(self, correlation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlation regime and determine leverage factor."""
        avg_correlation = correlation_analysis.get('average_correlation', 0.5)
        leverage_factor = self._calculate_leverage_factor(avg_correlation)
        regime_shift = self._detect_regime_shift(avg_correlation)
        breadth_collapse = self._detect_breadth_collapse()
        
        regime_analysis = {
            'average_correlation': avg_correlation,
            'leverage_factor': leverage_factor,
            'regime_shift': regime_shift,
            'breadth_collapse': breadth_collapse,
            'risk_off_trigger': regime_shift or breadth_collapse
        }
        
        return regime_analysis
    
    def _generate_opportunities(self, momentum_analysis: Dict, residual_analysis: Dict,
                              correlation_analysis: Dict, pair_analysis: Dict,
                              regime_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate trading opportunities across all buckets."""
        opportunities = []
        
        # 1. Momentum Long Opportunities
        momentum_opportunities = self._generate_momentum_opportunities(momentum_analysis, regime_analysis)
        opportunities.extend(momentum_opportunities)
        
        # 2. Residual Opportunities
        residual_opportunities = self._generate_residual_opportunities(residual_analysis, momentum_analysis)
        opportunities.extend(residual_opportunities)
        
        # 3. Mean Reversion Opportunities
        mean_reversion_opportunities = self._generate_mean_reversion_opportunities(
            momentum_analysis, regime_analysis
        )
        opportunities.extend(mean_reversion_opportunities)
        
        # 4. Pair Trading Opportunities
        pair_opportunities = self._generate_pair_opportunities(pair_analysis)
        opportunities.extend(pair_opportunities)
        
        return opportunities
    
    def _generate_momentum_opportunities(self, momentum_analysis: Dict, regime_analysis: Dict) -> List[Dict]:
        """Generate momentum long opportunities."""
        opportunities = []
        
        for asset, analysis in momentum_analysis.items():
            cm = analysis.get('composite_momentum', 0)
            m7 = analysis.get('momentum_returns', {}).get('M7', 0)
            acc = analysis.get('acceleration', 0)
            z30 = analysis.get('z_scores', {}).get('Z30', 0)
            ms = analysis.get('momentum_strength', 0)
            trend_aligned = analysis.get('trend_alignment', False)
            
            # Entry conditions
            if (cm > self.momentum_params['composite_threshold'] and
                m7 > self.momentum_params['base_momentum_threshold'] and
                trend_aligned and
                (acc > self.momentum_params['acceleration_threshold'] or z30 > self.momentum_params['established_trend_threshold']) and
                ms > 0):
                
                position_size = self._calculate_momentum_position_size(asset, analysis, regime_analysis)
                
                opportunities.append({
                    'asset': asset,
                    'bucket': 'momentum_long',
                    'signal_type': 'LONG',
                    'confidence': min(cm / 2.0, 1.0),
                    'position_size': position_size,
                    'entry_price': analysis.get('current_price'),
                    'stop_loss': self._calculate_stop_loss(asset, analysis, 'long'),
                    'take_profit': None,
                    'analysis': analysis
                })
        
        return opportunities
    
    def _generate_residual_opportunities(self, residual_analysis: Dict, momentum_analysis: Dict) -> List[Dict]:
        """Generate residual momentum opportunities."""
        opportunities = []
        
        for asset, analysis in residual_analysis.items():
            residual_z = analysis.get('residual_zscore', 0)
            momentum_analysis_asset = momentum_analysis.get(asset, {})
            
            # Long residual opportunity
            if residual_z > self.residual_params['residual_threshold']:
                base_position_size = self._calculate_base_position_size(asset, 'residual_long')
                if residual_z > 1.5:
                    base_position_size *= self.position_params['residual_boost_multiplier']
                
                opportunities.append({
                    'asset': asset,
                    'bucket': 'residual_long',
                    'signal_type': 'LONG',
                    'confidence': min(residual_z / 3.0, 1.0),
                    'position_size': base_position_size,
                    'entry_price': momentum_analysis_asset.get('current_price'),
                    'stop_loss': self._calculate_stop_loss(asset, momentum_analysis_asset, 'long'),
                    'take_profit': None,
                    'analysis': analysis
                })
            
            # Short residual opportunity
            elif residual_z < -self.residual_params['residual_threshold']:
                base_position_size = self._calculate_base_position_size(asset, 'residual_short')
                
                opportunities.append({
                    'asset': asset,
                    'bucket': 'residual_short',
                    'signal_type': 'SHORT',
                    'confidence': min(abs(residual_z) / 3.0, 1.0),
                    'position_size': base_position_size,
                    'entry_price': momentum_analysis_asset.get('current_price'),
                    'stop_loss': self._calculate_stop_loss(asset, momentum_analysis_asset, 'short'),
                    'take_profit': None,
                    'analysis': analysis
                })
        
        return opportunities
    
    def _generate_mean_reversion_opportunities(self, momentum_analysis: Dict, regime_analysis: Dict) -> List[Dict]:
        """Generate mean reversion opportunities."""
        opportunities = []
        
        # Only generate mean reversion signals in low correlation regime
        if regime_analysis.get('average_correlation', 0.5) >= self.correlation_params['low_correlation_threshold']:
            return opportunities
        
        for asset, analysis in momentum_analysis.items():
            z7 = analysis.get('z_scores', {}).get('Z7', 0)
            ms = analysis.get('momentum_strength', 0)
            
            # Overextension short opportunity
            if (z7 > self.mean_reversion_params['overextension_threshold'] and ms < 0):
                base_position_size = self._calculate_base_position_size(asset, 'mean_reversion_short')
                base_position_size *= self.position_params['mean_reversion_size_multiplier']
                
                opportunities.append({
                    'asset': asset,
                    'bucket': 'mean_reversion_short',
                    'signal_type': 'SHORT',
                    'confidence': min(z7 / 4.0, 1.0),
                    'position_size': base_position_size,
                    'entry_price': analysis.get('current_price'),
                    'stop_loss': self._calculate_stop_loss(asset, analysis, 'short'),
                    'take_profit': analysis.get('current_price') * (1 - self.mean_reversion_params['reversion_target']),
                    'analysis': analysis
                })
            
            # Oversold long opportunity
            elif (z7 < self.mean_reversion_params['oversold_threshold'] and 
                  ms > self.mean_reversion_params['momentum_strength_threshold']):
                base_position_size = self._calculate_base_position_size(asset, 'mean_reversion_long')
                base_position_size *= self.position_params['mean_reversion_size_multiplier']
                
                opportunities.append({
                    'asset': asset,
                    'bucket': 'mean_reversion_long',
                    'signal_type': 'LONG',
                    'confidence': min(abs(z7) / 4.0, 1.0),
                    'position_size': base_position_size,
                    'entry_price': analysis.get('current_price'),
                    'stop_loss': self._calculate_stop_loss(asset, analysis, 'long'),
                    'take_profit': analysis.get('current_price') * (1 + self.mean_reversion_params['reversion_target']),
                    'analysis': analysis
                })
        
        return opportunities
    
    def _generate_pair_opportunities(self, pair_analysis: Dict) -> List[Dict]:
        """Generate pair trading opportunities."""
        opportunities = []
        
        for pair_name, analysis in pair_analysis.items():
            spread_zscore = analysis.get('spread_zscore', 0)
            correlation_metrics = analysis.get('correlation_metrics', {})
            corr_30d = correlation_metrics.get('30d', 0)
            corr_7d = correlation_metrics.get('7d', 0)
            corr_7d_prev = correlation_metrics.get('7d_prev', 0)
            
            # Long spread opportunity
            if (spread_zscore < -self.pair_params['entry_threshold'] and
                corr_30d > self.pair_params['correlation_threshold'] and
                (corr_7d_prev - corr_7d) >= self.pair_params['correlation_decline_threshold']):
                
                opportunities.append({
                    'pair_name': pair_name,
                    'bucket': 'pair_long_spread',
                    'signal_type': 'PAIR_LONG',
                    'confidence': min(abs(spread_zscore) / 4.0, 1.0),
                    'position_size': self._calculate_base_position_size(pair_name, 'pair_trade'),
                    'entry_price': analysis.get('spread'),
                    'stop_loss': analysis.get('spread') * (1 + self.pair_params['hard_stop_threshold']),
                    'take_profit': 0,
                    'analysis': analysis
                })
            
            # Short spread opportunity
            elif (spread_zscore > self.pair_params['entry_threshold'] and
                  corr_30d > self.pair_params['correlation_threshold'] and
                  (corr_7d_prev - corr_7d) >= self.pair_params['correlation_decline_threshold']):
                
                opportunities.append({
                    'pair_name': pair_name,
                    'bucket': 'pair_short_spread',
                    'signal_type': 'PAIR_SHORT',
                    'confidence': min(spread_zscore / 4.0, 1.0),
                    'position_size': self._calculate_base_position_size(pair_name, 'pair_trade'),
                    'entry_price': analysis.get('spread'),
                    'stop_loss': analysis.get('spread') * (1 - self.pair_params['hard_stop_threshold']),
                    'take_profit': 0,
                    'analysis': analysis
                })
        
        return opportunities
    
    def _create_trading_signal(self, opportunity: Dict, regime_analysis: Dict) -> Optional[TradingSignal]:
        """Create a trading signal from an opportunity."""
        try:
            # Determine signal type
            if opportunity['signal_type'] == 'LONG':
                signal_type = SignalType.LONG
                direction = SignalDirection.BUY
            elif opportunity['signal_type'] == 'SHORT':
                signal_type = SignalType.SHORT
                direction = SignalDirection.SELL
            elif opportunity['signal_type'] in ['PAIR_LONG', 'PAIR_SHORT']:
                signal_type = SignalType.LONG if opportunity['signal_type'] == 'PAIR_LONG' else SignalType.SHORT
                direction = SignalDirection.BUY if opportunity['signal_type'] == 'PAIR_LONG' else SignalDirection.SELL
            else:
                return None
            
            # Determine signal strength
            confidence = opportunity.get('confidence', 0.5)
            if confidence > 0.8:
                signal_strength = SignalStrength.STRONG
            elif confidence > 0.6:
                signal_strength = SignalStrength.MODERATE
            else:
                signal_strength = SignalStrength.WEAK
            
            # Apply leverage factor if in risk-off mode
            position_size = opportunity.get('position_size', 0.02)
            if self.portfolio_state['risk_off_mode']:
                position_size *= regime_analysis.get('leverage_factor', 0.4)
            
            # Create signal
            signal = TradingSignal(
                symbol=opportunity.get('asset', opportunity.get('pair_name', 'unknown')),
                signal_type=signal_type,
                direction=direction,
                timestamp=datetime.now(),
                price=opportunity.get('entry_price', 0.0),
                strategy_name='MultiBucketPortfolioStrategy',
                signal_strength=signal_strength,
                confidence=confidence,
                position_size=position_size,
                stop_loss=opportunity.get('stop_loss'),
                take_profit=opportunity.get('take_profit'),
                max_risk=self.risk_params.get('max_risk_per_trade', 0.02),
                analysis_data=opportunity.get('analysis'),
                metadata={
                    'bucket': opportunity.get('bucket'),
                    'regime_analysis': regime_analysis
                }
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error creating trading signal: {e}")
            return None
    
    # Helper methods for calculations
    def _calculate_returns(self, df: pd.DataFrame) -> pd.Series:
        """Calculate daily returns from price data."""
        if df.empty or 'close' not in df.columns:
            return pd.Series()
        returns = df['close'].pct_change().dropna()
        return returns
    
    def _calculate_momentum_zscore(self, df: pd.DataFrame, horizon: int) -> float:
        """Calculate z-score for momentum over rolling window."""
        if len(df) < self.momentum_params['zscore_window']:
            return 0.0
        
        # Calculate momentum series
        momentum_series = []
        for i in range(horizon, len(df) - self.momentum_params['zscore_window']):
            momentum = (df['close'].iloc[i] / df['close'].iloc[i-horizon]) - 1
            momentum_series.append(momentum)
        
        if len(momentum_series) < 10:
            return 0.0
        
        # Calculate z-score
        mean_momentum = np.mean(momentum_series)
        std_momentum = np.std(momentum_series)
        
        if std_momentum == 0:
            return 0.0
        
        current_momentum = (df['close'].iloc[-1] / df['close'].iloc[-horizon-1]) - 1
        zscore = (current_momentum - mean_momentum) / std_momentum
        
        return zscore
    
    def _calculate_composite_momentum(self, z_scores: Dict[str, float]) -> float:
        """Calculate composite momentum score using weighted z-scores."""
        weights = self.momentum_params['weights']
        horizons = self.momentum_params['horizons']
        
        composite_score = 0.0
        for i, horizon in enumerate(horizons):
            z_key = f'Z{horizon}'
            if z_key in z_scores and i < len(weights):
                composite_score += weights[i] * z_scores[z_key]
        
        return composite_score
    
    def _calculate_momentum_strength(self, df: pd.DataFrame, asset: str) -> float:
        """Calculate momentum strength (placeholder for RSI divergence integration)."""
        if df.empty or len(df) < 14:
            return 0.0
        
        # Simple momentum strength based on recent price action
        recent_returns = df['close'].pct_change().tail(14)
        positive_days = (recent_returns > 0).sum()
        momentum_strength = (positive_days / 14) - 0.5  # Range: -0.5 to 0.5
        
        return momentum_strength
    
    def _check_trend_alignment(self, momentum_returns: Dict[str, float]) -> bool:
        """Check if momentum is aligned across timeframes."""
        m7 = momentum_returns.get('M7', 0)
        m14 = momentum_returns.get('M14', 0)
        m30 = momentum_returns.get('M30', 0)
        
        return m7 > 0 and m14 > 0 and m30 > 0
    
    def _calculate_beta_residuals(self, asset_returns: pd.Series, factor_returns: pd.Series) -> Tuple[float, Optional[np.ndarray]]:
        """Calculate beta and residuals from linear regression."""
        if len(asset_returns) < self.residual_params['regression_window']:
            return 0.0, None
        
        # Use recent data for regression
        recent_asset = asset_returns.tail(self.residual_params['regression_window'])
        recent_factor = factor_returns.tail(self.residual_params['regression_window'])
        
        # Align data
        aligned_data = pd.concat([recent_asset, recent_factor], axis=1).dropna()
        if len(aligned_data) < 10:
            return 0.0, None
        
        # Linear regression
        X = aligned_data.iloc[:, 1].values.reshape(-1, 1)  # Factor returns
        y = aligned_data.iloc[:, 0].values  # Asset returns
        
        try:
            model = LinearRegression()
            model.fit(X, y)
            beta = model.coef_[0]
            residuals = y - model.predict(X)
            return beta, residuals
        except Exception as e:
            self.logger.warning(f"Error in beta calculation: {e}")
            return 0.0, None
    
    def _calculate_residual_zscore(self, residuals: np.ndarray) -> float:
        """Calculate z-score of recent residuals."""
        if len(residuals) < self.residual_params['residual_window']:
            return 0.0
        
        recent_residuals = residuals[-self.residual_params['residual_window']:]
        mean_residual = np.mean(recent_residuals)
        std_residual = np.std(recent_residuals)
        
        if std_residual == 0:
            return 0.0
        
        current_residual = recent_residuals[-1]
        zscore = (current_residual - mean_residual) / std_residual
        
        return zscore
    
    def _calculate_correlation_matrix(self, returns_data: Dict[str, pd.Series], window: int) -> pd.DataFrame:
        """Calculate correlation matrix for given window."""
        # Align all return series
        aligned_returns = pd.DataFrame(returns_data)
        aligned_returns = aligned_returns.dropna()
        
        if len(aligned_returns) < window:
            return pd.DataFrame()
        
        # Calculate rolling correlation
        correlation_matrix = aligned_returns.tail(window).corr()
        return correlation_matrix
    
    def _calculate_average_correlation(self, correlation_analysis: Dict[str, Any]) -> float:
        """Calculate average correlation across all timeframes."""
        correlations = []
        
        for timeframe, corr_matrix in correlation_analysis.items():
            if isinstance(corr_matrix, pd.DataFrame) and not corr_matrix.empty:
                # Get upper triangle of correlation matrix (excluding diagonal)
                upper_triangle = corr_matrix.where(
                    np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
                )
                valid_correlations = upper_triangle.values.flatten()
                valid_correlations = valid_correlations[~np.isnan(valid_correlations)]
                
                if len(valid_correlations) > 0:
                    correlations.extend(valid_correlations)
        
        if correlations:
            return np.mean(correlations)
        else:
            return 0.5  # Default neutral correlation
    
    def _calculate_pair_spread(self, long_df: pd.DataFrame, short_df: pd.DataFrame, pair_name: str) -> Tuple[Optional[float], Optional[float], Dict]:
        """Calculate pair spread and related metrics."""
        if long_df.empty or short_df.empty:
            return None, None, {}
        
        # Align data
        min_length = min(len(long_df), len(short_df))
        long_prices = long_df['close'].tail(min_length)
        short_prices = short_df['close'].tail(min_length)
        
        if min_length < self.pair_params['spread_window']:
            return None, None, {}
        
        # Calculate spread
        spread = long_prices.iloc[-1] - short_prices.iloc[-1]
        
        # Calculate spread z-score
        spread_series = long_prices - short_prices
        if len(spread_series) >= self.pair_params['zscore_window']:
            recent_spreads = spread_series.tail(self.pair_params['zscore_window'])
            spread_mean = np.mean(recent_spreads)
            spread_std = np.std(recent_spreads)
            
            if spread_std > 0:
                spread_zscore = (spread - spread_mean) / spread_std
            else:
                spread_zscore = 0.0
        else:
            spread_zscore = 0.0
        
        # Calculate correlation metrics
        correlation_metrics = {}
        for window in [7, 30]:
            if len(long_prices) >= window:
                corr = long_prices.tail(window).corr(short_prices.tail(window))
                correlation_metrics[f'{window}d'] = corr
        
        # Calculate 7-day correlation change
        if len(long_prices) >= 14:
            corr_7d_current = long_prices.tail(7).corr(short_prices.tail(7))
            corr_7d_prev = long_prices.tail(14).head(7).corr(short_prices.tail(14).head(7))
            correlation_metrics['7d'] = corr_7d_current
            correlation_metrics['7d_prev'] = corr_7d_prev
        
        return spread, spread_zscore, correlation_metrics
    
    def _calculate_leverage_factor(self, avg_correlation: float) -> float:
        """Calculate leverage factor based on correlation regime."""
        low_threshold = self.correlation_params['low_correlation_threshold']
        high_threshold = self.correlation_params['high_correlation_threshold']
        reduction_factor = self.correlation_params['leverage_reduction_factor']
        
        if avg_correlation <= low_threshold:
            return 1.0
        elif avg_correlation >= high_threshold:
            return reduction_factor
        else:
            # Linear interpolation
            factor = 1.0 - ((avg_correlation - low_threshold) / (high_threshold - low_threshold)) * (1.0 - reduction_factor)
            return factor
    
    def _detect_regime_shift(self, current_correlation: float) -> bool:
        """Detect correlation regime shift."""
        if self.portfolio_state['last_correlation_regime'] is None:
            self.portfolio_state['last_correlation_regime'] = current_correlation
            return False
        
        correlation_change = abs(current_correlation - self.portfolio_state['last_correlation_regime'])
        regime_shift = (correlation_change > self.correlation_params['regime_shift_threshold'] and 
                       current_correlation > 0.25)
        
        self.portfolio_state['last_correlation_regime'] = current_correlation
        return regime_shift
    
    def _detect_breadth_collapse(self) -> bool:
        """Detect breadth collapse (placeholder implementation)."""
        return False
    
    def _calculate_momentum_position_size(self, asset: str, analysis: Dict, regime_analysis: Dict) -> float:
        """Calculate position size for momentum trades."""
        base_size = self.position_params['max_single_asset_exposure'] * 0.1
        
        # Adjust for confidence
        confidence = analysis.get('composite_momentum', 0) / 2.0
        if confidence > 0.8:
            multiplier = self.position_params['confidence_multiplier']['high']
        elif confidence > 0.6:
            multiplier = self.position_params['confidence_multiplier']['medium']
        else:
            multiplier = self.position_params['confidence_multiplier']['low']
        
        position_size = base_size * multiplier
        position_size *= regime_analysis.get('leverage_factor', 1.0)
        
        return min(position_size, self.position_params['max_single_asset_exposure'])
    
    def _calculate_base_position_size(self, asset: str, bucket_type: str) -> float:
        """Calculate base position size for different bucket types."""
        base_size = self.position_params['max_single_asset_exposure'] * 0.05
        
        # Adjust for bucket type
        if bucket_type == 'residual_long':
            base_size *= 0.8
        elif bucket_type == 'residual_short':
            base_size *= 0.6
        elif bucket_type == 'mean_reversion_long':
            base_size *= 0.4
        elif bucket_type == 'mean_reversion_short':
            base_size *= 0.3
        elif bucket_type == 'pair_trade':
            base_size *= 0.7
        
        return base_size
    
    def _calculate_stop_loss(self, asset: str, analysis: Dict, direction: str) -> Optional[float]:
        """Calculate stop loss based on ATR."""
        current_price = analysis.get('current_price')
        if current_price is None:
            return None
        
        # Simple percentage-based stop
        if direction == 'long':
            stop_loss = current_price * 0.95  # 5% stop loss
        else:
            stop_loss = current_price * 1.05  # 5% stop loss
        
        return stop_loss
    
    def _generate_risk_summary(self, opportunities: List[Dict], regime_analysis: Dict, market_data: Dict) -> Dict[str, Any]:
        """Generate risk summary for the portfolio."""
        total_exposure = sum(opp.get('position_size', 0) for opp in opportunities)
        
        # Calculate portfolio beta (simplified)
        portfolio_beta = 0.0
        for opp in opportunities:
            if 'analysis' in opp and 'beta' in opp['analysis']:
                portfolio_beta += opp['position_size'] * opp['analysis']['beta']
        
        risk_summary = {
            'total_exposure': total_exposure,
            'portfolio_beta': portfolio_beta,
            'leverage_factor': regime_analysis.get('leverage_factor', 1.0),
            'risk_off_mode': self.portfolio_state['risk_off_mode'],
            'average_correlation': regime_analysis.get('average_correlation', 0.5),
            'opportunity_count': len(opportunities),
            'bucket_distribution': self._calculate_bucket_distribution(opportunities)
        }
        
        return risk_summary
    
    def _calculate_bucket_distribution(self, opportunities: List[Dict]) -> Dict[str, float]:
        """Calculate distribution across buckets."""
        bucket_totals = {}
        total_exposure = sum(opp.get('position_size', 0) for opp in opportunities)
        
        for opp in opportunities:
            bucket = opp.get('bucket', 'unknown')
            bucket_totals[bucket] = bucket_totals.get(bucket, 0) + opp.get('position_size', 0)
        
        # Convert to percentages
        bucket_distribution = {}
        for bucket, exposure in bucket_totals.items():
            if total_exposure > 0:
                bucket_distribution[bucket] = exposure / total_exposure
            else:
                bucket_distribution[bucket] = 0.0
        
        return bucket_distribution

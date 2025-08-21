"""
Enhanced Mosaic Analyzer for generating actionable correlation insights.
Provides detailed trading opportunities, market context, and specific recommendations.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from dataclasses import dataclass
from enum import Enum


class MarketRegime(Enum):
    """Market regime classification based on correlation patterns."""
    DIVERSIFIED = "diversified"  # Low correlations, good for diversification
    TRENDING = "trending"        # High positive correlations, trending market
    VOLATILE = "volatile"        # High negative correlations, volatile environment
    MIXED = "mixed"             # Mixed correlation patterns


class CorrelationStrength(Enum):
    """Correlation strength classification."""
    VERY_STRONG = "very_strong"  # |r| >= 0.8
    STRONG = "strong"            # 0.6 <= |r| < 0.8
    MODERATE = "moderate"        # 0.4 <= |r| < 0.6
    WEAK = "weak"               # 0.2 <= |r| < 0.4
    NEGLIGIBLE = "negligible"   # |r| < 0.2


@dataclass
class TradingOpportunity:
    """Data class for trading opportunities."""
    pair: str
    opportunity_type: str  # 'correlation_trade', 'divergence', 'breakdown', 'momentum'
    timeframe: str
    correlation: float
    confidence: str  # 'high', 'medium', 'low'
    entry_signal: str
    risk_level: str  # 'low', 'medium', 'high'
    expected_duration: str
    notes: str


@dataclass
class MarketInsight:
    """Data class for market insights."""
    insight_type: str  # 'regime', 'structure', 'risk', 'opportunity'
    title: str
    description: str
    importance: str  # 'high', 'medium', 'low'
    actionable: bool
    timeframe: Optional[str] = None


class EnhancedMosaicAnalyzer:
    """
    Enhanced analyzer for daily correlation mosaics.
    Provides actionable insights, trading opportunities, and market context.
    """
    
    def __init__(self):
        """Initialize the enhanced mosaic analyzer."""
        self.logger = logging.getLogger(__name__)
        
        # Configuration for analysis thresholds
        self.config = {
            'correlation_thresholds': {
                'very_strong': 0.8,
                'strong': 0.6,
                'moderate': 0.4,
                'weak': 0.2
            },
            'significance_threshold': 0.05,
            'min_sample_size': 100,
            'trading_timeframes': ['7d', '14d', '30d'],
            'macro_indicators': ['VIX', 'DXY', 'TREASURY', 'USDT'],
            'crypto_majors': ['BTC', 'ETH'],
            'crypto_alts': ['SOL', 'XRP', 'SUI', 'ENA', 'BTT']
        }
    
    def analyze_mosaic(self, mosaic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform enhanced analysis of daily correlation mosaic.
        
        Args:
            mosaic_data: Raw mosaic data from generator
            
        Returns:
            Dict[str, Any]: Enhanced analysis with actionable insights
        """
        try:
            self.logger.info("Starting enhanced mosaic analysis")
            
            correlation_matrix = mosaic_data.get('correlation_matrix', {})
            matrix = correlation_matrix.get('matrix', {})
            summary = correlation_matrix.get('summary', {})
            
            # Perform comprehensive analysis
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'market_regime': self._determine_market_regime(matrix, summary),
                'trading_opportunities': self._identify_trading_opportunities(matrix),
                'market_insights': self._generate_market_insights(matrix, summary),
                'risk_analysis': self._analyze_risk_factors(matrix, summary),
                'portfolio_recommendations': self._generate_portfolio_recommendations(matrix, summary),
                'correlation_breakdown_signals': self._detect_breakdown_signals(matrix),
                'timeframe_analysis': self._analyze_timeframes(matrix),
                'pair_rankings': self._rank_pairs_by_opportunity(matrix),
                'actionable_summary': self._create_actionable_summary(matrix, summary)
            }
            
            # Add enhanced metrics
            analysis['enhanced_metrics'] = self._calculate_enhanced_metrics(matrix, summary)
            
            # Generate priority alerts
            analysis['priority_alerts'] = self._generate_priority_alerts(analysis)
            
            self.logger.info(f"Enhanced analysis completed: {len(analysis['trading_opportunities'])} opportunities identified")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze mosaic: {e}")
            return {}
    
    def _determine_market_regime(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Determine current market regime based on correlation patterns."""
        try:
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            strong_correlations = summary.get('strong_correlations', 0)
            negative_correlations = summary.get('negative_correlations', 0)
            total_pairs = summary.get('total_pairs', 1)
            
            # Calculate regime metrics
            strong_ratio = strong_correlations / total_pairs
            negative_ratio = negative_correlations / total_pairs
            
            # Determine regime
            if avg_correlation < 0.3 and strong_ratio < 0.2:
                regime = MarketRegime.DIVERSIFIED
                confidence = "high" if avg_correlation < 0.2 else "medium"
                description = "Low correlation environment favorable for diversified strategies"
            elif avg_correlation > 0.6 or strong_ratio > 0.4:
                regime = MarketRegime.TRENDING
                confidence = "high" if strong_ratio > 0.5 else "medium"
                description = "High correlation environment indicating trending market conditions"
            elif negative_ratio > 0.3:
                regime = MarketRegime.VOLATILE
                confidence = "high" if negative_ratio > 0.4 else "medium"
                description = "High negative correlation environment suggesting volatile conditions"
            else:
                regime = MarketRegime.MIXED
                confidence = "medium"
                description = "Mixed correlation patterns with no clear directional bias"
            
            return {
                'regime': regime.value,
                'confidence': confidence,
                'description': description,
                'metrics': {
                    'avg_correlation': avg_correlation,
                    'strong_ratio': strong_ratio,
                    'negative_ratio': negative_ratio
                },
                'implications': self._get_regime_implications(regime)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to determine market regime: {e}")
            return {'regime': 'unknown', 'confidence': 'low', 'description': 'Unable to determine market regime'}
    
    def _identify_trading_opportunities(self, matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific trading opportunities from correlation matrix."""
        opportunities = []
        
        try:
            for pair, correlations in matrix.items():
                # Skip pairs with insufficient data
                if self._has_insufficient_data(correlations):
                    continue
                
                # Analyze each timeframe
                for timeframe in self.config['trading_timeframes']:
                    if timeframe not in correlations:
                        continue
                    
                    data = correlations[timeframe]
                    correlation = data.get('correlation', 0.0)
                    significance = data.get('significance', False)
                    p_value = data.get('p_value', 1.0)
                    
                    if self._is_nan(correlation) or not significance:
                        continue
                    
                    # Identify opportunity types
                    opportunity = self._classify_opportunity(pair, timeframe, correlation, p_value)
                    if opportunity:
                        opportunities.append(opportunity)
            
            # Sort by confidence and potential
            opportunities.sort(key=lambda x: (
                x['confidence'] == 'high',
                abs(x['correlation']),
                x['risk_level'] == 'low'
            ), reverse=True)
            
            return opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            self.logger.error(f"Failed to identify trading opportunities: {e}")
            return []
    
    def _classify_opportunity(self, pair: str, timeframe: str, correlation: float, p_value: float) -> Optional[Dict[str, Any]]:
        """Classify a specific trading opportunity."""
        try:
            abs_corr = abs(correlation)
            
            # Determine opportunity type and details
            if abs_corr >= 0.8:
                opportunity_type = "momentum_trade"
                entry_signal = f"Strong {'positive' if correlation > 0 else 'negative'} correlation - consider pair trading"
                confidence = "high"
                risk_level = "medium"
                expected_duration = self._get_expected_duration(timeframe)
            elif abs_corr >= 0.6:
                opportunity_type = "correlation_trade"
                entry_signal = f"Moderate {'positive' if correlation > 0 else 'negative'} correlation - monitor for entries"
                confidence = "medium"
                risk_level = "medium"
                expected_duration = self._get_expected_duration(timeframe)
            elif abs_corr <= 0.1 and self._is_normally_correlated(pair):
                opportunity_type = "divergence_trade"
                entry_signal = "Low correlation suggests potential divergence opportunity"
                confidence = "medium"
                risk_level = "high"
                expected_duration = "short_term"
            else:
                return None
            
            # Generate specific notes based on pair type
            notes = self._generate_opportunity_notes(pair, correlation, timeframe)
            
            return {
                'pair': pair,
                'opportunity_type': opportunity_type,
                'timeframe': timeframe,
                'correlation': correlation,
                'confidence': confidence,
                'entry_signal': entry_signal,
                'risk_level': risk_level,
                'expected_duration': expected_duration,
                'notes': notes,
                'p_value': p_value
            }
            
        except Exception as e:
            self.logger.error(f"Failed to classify opportunity for {pair}: {e}")
            return None
    
    def _generate_market_insights(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable market insights."""
        insights = []
        
        try:
            # Market structure analysis
            insights.extend(self._analyze_market_structure(matrix, summary))
            
            # Crypto vs macro analysis
            insights.extend(self._analyze_crypto_macro_dynamics(matrix))
            
            # Major vs alt analysis
            insights.extend(self._analyze_major_alt_dynamics(matrix))
            
            # Risk concentration analysis
            insights.extend(self._analyze_risk_concentration(matrix, summary))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate market insights: {e}")
            return []
    
    def _analyze_risk_factors(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk factors from correlation patterns."""
        try:
            risk_factors = {
                'overall_risk_level': 'medium',
                'concentration_risk': 'low',
                'correlation_risk': 'medium',
                'diversification_effectiveness': 'good',
                'specific_risks': [],
                'risk_mitigation_suggestions': []
            }
            
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            strong_correlations = summary.get('strong_correlations', 0)
            total_pairs = summary.get('total_pairs', 1)
            
            # Assess concentration risk
            strong_ratio = strong_correlations / total_pairs
            if strong_ratio > 0.5:
                risk_factors['concentration_risk'] = 'high'
                risk_factors['specific_risks'].append("High correlation concentration detected")
                risk_factors['risk_mitigation_suggestions'].append("Consider reducing position sizes in highly correlated assets")
            elif strong_ratio > 0.3:
                risk_factors['concentration_risk'] = 'medium'
                risk_factors['specific_risks'].append("Moderate correlation concentration")
            
            # Assess overall correlation risk
            if avg_correlation > 0.7:
                risk_factors['correlation_risk'] = 'high'
                risk_factors['overall_risk_level'] = 'high'
                risk_factors['diversification_effectiveness'] = 'poor'
                risk_factors['specific_risks'].append("Very high average correlation reduces diversification benefits")
                risk_factors['risk_mitigation_suggestions'].append("Consider alternative assets or reduce overall exposure")
            elif avg_correlation < 0.3:
                risk_factors['correlation_risk'] = 'low'
                risk_factors['diversification_effectiveness'] = 'excellent'
            
            # Check for specific high-risk pairs
            high_risk_pairs = self._identify_high_risk_pairs(matrix)
            if high_risk_pairs:
                risk_factors['specific_risks'].extend([f"High correlation detected: {pair}" for pair in high_risk_pairs[:3]])
                risk_factors['risk_mitigation_suggestions'].append("Monitor position sizing in highly correlated pairs")
            
            return risk_factors
            
        except Exception as e:
            self.logger.error(f"Failed to analyze risk factors: {e}")
            return {'overall_risk_level': 'unknown'}
    
    def _generate_portfolio_recommendations(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific portfolio management recommendations."""
        recommendations = []
        
        try:
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            
            # Diversification recommendations
            if avg_correlation < 0.3:
                recommendations.append({
                    'type': 'diversification',
                    'priority': 'high',
                    'action': 'Increase position sizes',
                    'rationale': 'Low correlation environment provides excellent diversification benefits',
                    'implementation': 'Consider equal-weight or risk-parity allocation'
                })
            elif avg_correlation > 0.6:
                recommendations.append({
                    'type': 'concentration',
                    'priority': 'high',
                    'action': 'Reduce position sizes or number of assets',
                    'rationale': 'High correlation reduces diversification effectiveness',
                    'implementation': 'Focus on best-performing assets or add uncorrelated alternatives'
                })
            
            # Specific pair recommendations
            pair_recommendations = self._generate_pair_specific_recommendations(matrix)
            recommendations.extend(pair_recommendations)
            
            # Rebalancing recommendations
            rebalancing_recs = self._generate_rebalancing_recommendations(matrix, summary)
            recommendations.extend(rebalancing_recs)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate portfolio recommendations: {e}")
            return []
    
    def _detect_breakdown_signals(self, matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect correlation breakdown signals that may indicate trading opportunities."""
        breakdown_signals = []
        
        try:
            for pair, correlations in matrix.items():
                # Compare short-term vs long-term correlations
                short_term = correlations.get('7d', {}).get('correlation', np.nan)
                long_term = correlations.get('60d', {}).get('correlation', np.nan)
                
                if self._is_nan(short_term) or self._is_nan(long_term):
                    continue
                
                # Detect significant changes
                change = abs(short_term - long_term)
                if change > 0.3:  # Significant breakdown threshold
                    breakdown_signals.append({
                        'pair': pair,
                        'short_term_correlation': short_term,
                        'long_term_correlation': long_term,
                        'change_magnitude': change,
                        'signal_type': 'breakdown' if change > 0.5 else 'shift',
                        'direction': 'increasing' if short_term > long_term else 'decreasing',
                        'trading_implication': self._get_breakdown_trading_implication(short_term, long_term, change)
                    })
            
            # Sort by magnitude of change
            breakdown_signals.sort(key=lambda x: x['change_magnitude'], reverse=True)
            return breakdown_signals[:5]  # Return top 5 signals
            
        except Exception as e:
            self.logger.error(f"Failed to detect breakdown signals: {e}")
            return []
    
    def _analyze_timeframes(self, matrix: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlation patterns across different timeframes."""
        try:
            timeframe_analysis = {}
            
            for timeframe in ['7d', '14d', '30d', '60d']:
                correlations = []
                significant_count = 0
                strong_count = 0
                
                for pair, data in matrix.items():
                    if timeframe in data:
                        corr = data[timeframe].get('correlation', np.nan)
                        sig = data[timeframe].get('significance', False)
                        
                        if not self._is_nan(corr):
                            correlations.append(corr)
                            if sig:
                                significant_count += 1
                            if abs(corr) >= 0.6:
                                strong_count += 1
                
                if correlations:
                    timeframe_analysis[timeframe] = {
                        'avg_correlation': np.mean(correlations),
                        'max_correlation': np.max(np.abs(correlations)),
                        'significant_pairs': significant_count,
                        'strong_pairs': strong_count,
                        'total_pairs': len(correlations),
                        'recommendation': self._get_timeframe_recommendation(timeframe, correlations, significant_count, strong_count)
                    }
            
            # Identify best timeframe for trading
            best_timeframe = self._identify_best_trading_timeframe(timeframe_analysis)
            timeframe_analysis['best_for_trading'] = best_timeframe
            
            return timeframe_analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze timeframes: {e}")
            return {}
    
    def _rank_pairs_by_opportunity(self, matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank pairs by trading opportunity potential."""
        try:
            pair_scores = []
            
            for pair, correlations in matrix.items():
                if self._has_insufficient_data(correlations):
                    continue
                
                # Calculate opportunity score
                score = self._calculate_opportunity_score(pair, correlations)
                if score > 0:
                    pair_scores.append({
                        'pair': pair,
                        'opportunity_score': score,
                        'best_timeframe': self._get_best_timeframe_for_pair(correlations),
                        'recommendation': self._get_pair_recommendation(pair, correlations, score)
                    })
            
            # Sort by opportunity score
            pair_scores.sort(key=lambda x: x['opportunity_score'], reverse=True)
            return pair_scores[:10]  # Return top 10 pairs
            
        except Exception as e:
            self.logger.error(f"Failed to rank pairs: {e}")
            return []
    
    def _create_actionable_summary(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Create a concise, actionable summary of the analysis."""
        try:
            # Calculate key metrics
            total_opportunities = len([p for p in matrix.keys() if not self._has_insufficient_data(matrix[p])])
            high_value_pairs = len([p for p in matrix.keys() if self._calculate_opportunity_score(p, matrix[p]) > 0.7])
            
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            
            # Generate summary
            return {
                'market_conditions': self._summarize_market_conditions(avg_correlation, summary),
                'top_recommendations': self._get_top_recommendations(matrix, summary),
                'immediate_actions': self._get_immediate_actions(matrix, summary),
                'monitoring_priorities': self._get_monitoring_priorities(matrix),
                'risk_alerts': self._get_risk_alerts(matrix, summary),
                'opportunity_count': total_opportunities,
                'high_value_opportunities': high_value_pairs
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create actionable summary: {e}")
            return {}
    
    # Helper methods
    def _is_nan(self, value) -> bool:
        """Check if value is NaN."""
        try:
            return np.isnan(float(value))
        except (TypeError, ValueError):
            return True
    
    def _has_insufficient_data(self, correlations: Dict[str, Any]) -> bool:
        """Check if correlation data is insufficient for analysis."""
        for timeframe_data in correlations.values():
            if isinstance(timeframe_data, dict):
                correlation = timeframe_data.get('correlation', np.nan)
                if not self._is_nan(correlation):
                    return False
        return True
    
    def _is_normally_correlated(self, pair: str) -> bool:
        """Check if pair is normally expected to be correlated."""
        # Crypto-crypto pairs are normally correlated
        crypto_assets = self.config['crypto_majors'] + self.config['crypto_alts']
        parts = pair.split('_')
        if len(parts) == 2:
            return all(part in crypto_assets for part in parts)
        return False
    
    def _get_expected_duration(self, timeframe: str) -> str:
        """Get expected duration for a trading opportunity based on timeframe."""
        duration_map = {
            '7d': 'short_term',
            '14d': 'medium_term',
            '30d': 'medium_term',
            '60d': 'long_term'
        }
        return duration_map.get(timeframe, 'medium_term')
    
    def _generate_opportunity_notes(self, pair: str, correlation: float, timeframe: str) -> str:
        """Generate specific notes for a trading opportunity."""
        parts = pair.split('_')
        if len(parts) != 2:
            return "Monitor correlation changes for trading signals"
        
        asset1, asset2 = parts
        
        if correlation > 0.8:
            return f"Very strong positive correlation between {asset1} and {asset2} - consider momentum strategies"
        elif correlation < -0.8:
            return f"Very strong negative correlation between {asset1} and {asset2} - consider hedging strategies"
        elif correlation > 0.6:
            return f"Strong positive correlation - {asset1} and {asset2} tend to move together on {timeframe} timeframe"
        elif correlation < -0.6:
            return f"Strong negative correlation - {asset1} and {asset2} tend to move opposite on {timeframe} timeframe"
        else:
            return f"Moderate correlation pattern - monitor for changes in {timeframe} relationship"
    
    def _get_regime_implications(self, regime: MarketRegime) -> List[str]:
        """Get trading implications for market regime."""
        implications_map = {
            MarketRegime.DIVERSIFIED: [
                "Excellent environment for diversified portfolios",
                "Consider increasing position sizes",
                "Risk-parity strategies likely to perform well"
            ],
            MarketRegime.TRENDING: [
                "Strong directional moves likely",
                "Momentum strategies favored",
                "Reduce diversification, focus on best performers"
            ],
            MarketRegime.VOLATILE: [
                "High volatility environment",
                "Consider hedging strategies",
                "Reduce position sizes, increase cash allocation"
            ],
            MarketRegime.MIXED: [
                "Mixed signals in market",
                "Maintain balanced approach",
                "Monitor for regime changes"
            ]
        }
        return implications_map.get(regime, ["Monitor market conditions carefully"])
    
    def _calculate_enhanced_metrics(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional enhanced metrics."""
        try:
            metrics = {}
            
            # Calculate cross-timeframe consistency
            consistency_scores = []
            for pair, correlations in matrix.items():
                timeframe_corrs = []
                for tf in ['7d', '14d', '30d', '60d']:
                    if tf in correlations:
                        corr = correlations[tf].get('correlation', np.nan)
                        if not self._is_nan(corr):
                            timeframe_corrs.append(corr)
                
                if len(timeframe_corrs) >= 2:
                    consistency = 1.0 - np.std(timeframe_corrs)
                    consistency_scores.append(max(0, consistency))
            
            metrics['avg_consistency'] = np.mean(consistency_scores) if consistency_scores else 0.0
            metrics['pairs_with_data'] = len([p for p in matrix.keys() if not self._has_insufficient_data(matrix[p])])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate enhanced metrics: {e}")
            return {}
    
    def _generate_priority_alerts(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate priority alerts based on analysis."""
        alerts = []
        
        try:
            # High-value trading opportunities
            opportunities = analysis.get('trading_opportunities', [])
            high_confidence_ops = [op for op in opportunities if op.get('confidence') == 'high']
            
            if len(high_confidence_ops) >= 3:
                alerts.append({
                    'priority': 'high',
                    'type': 'opportunity',
                    'message': f"{len(high_confidence_ops)} high-confidence trading opportunities identified",
                    'action_required': True
                })
            
            # Risk alerts
            risk_analysis = analysis.get('risk_analysis', {})
            if risk_analysis.get('overall_risk_level') == 'high':
                alerts.append({
                    'priority': 'high',
                    'type': 'risk',
                    'message': "High risk environment detected",
                    'action_required': True
                })
            
            # Breakdown signals
            breakdown_signals = analysis.get('correlation_breakdown_signals', [])
            if len(breakdown_signals) >= 2:
                alerts.append({
                    'priority': 'medium',
                    'type': 'breakdown',
                    'message': f"{len(breakdown_signals)} correlation breakdown signals detected",
                    'action_required': False
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to generate priority alerts: {e}")
            return []
    
    # Additional helper methods for comprehensive analysis
    def _analyze_market_structure(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze overall market structure insights."""
        insights = []
        
        try:
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            
            if avg_correlation < 0.2:
                insights.append({
                    'insight_type': 'structure',
                    'title': 'Excellent Diversification Environment',
                    'description': f'Average correlation of {avg_correlation:.3f} indicates strong diversification benefits',
                    'importance': 'high',
                    'actionable': True,
                    'timeframe': 'current'
                })
            elif avg_correlation > 0.7:
                insights.append({
                    'insight_type': 'structure',
                    'title': 'High Correlation Warning',
                    'description': f'Average correlation of {avg_correlation:.3f} suggests reduced diversification effectiveness',
                    'importance': 'high',
                    'actionable': True,
                    'timeframe': 'current'
                })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to analyze market structure: {e}")
            return []
    
    def _analyze_crypto_macro_dynamics(self, matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze crypto vs macro correlations."""
        insights = []
        
        try:
            crypto_macro_pairs = []
            for pair in matrix.keys():
                parts = pair.split('_')
                if len(parts) == 2:
                    asset1, asset2 = parts
                    if (asset1 in self.config['crypto_majors'] + self.config['crypto_alts'] and 
                        asset2 in self.config['macro_indicators']):
                        crypto_macro_pairs.append(pair)
            
            if crypto_macro_pairs:
                # Analyze strongest crypto-macro correlations
                strong_macro_corrs = []
                for pair in crypto_macro_pairs:
                    correlations = matrix.get(pair, {})
                    for tf, data in correlations.items():
                        corr = data.get('correlation', np.nan)
                        if not self._is_nan(corr) and abs(corr) > 0.5:
                            strong_macro_corrs.append((pair, tf, corr))
                
                if strong_macro_corrs:
                    insights.append({
                        'insight_type': 'structure',
                        'title': 'Crypto-Macro Correlation Alert',
                        'description': f'Strong correlations detected between crypto and macro factors: {len(strong_macro_corrs)} instances',
                        'importance': 'medium',
                        'actionable': True,
                        'timeframe': 'current'
                    })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to analyze crypto-macro dynamics: {e}")
            return []
    
    def _analyze_major_alt_dynamics(self, matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze major crypto vs altcoin correlations."""
        insights = []
        
        try:
            major_alt_pairs = []
            for pair in matrix.keys():
                parts = pair.split('_')
                if len(parts) == 2:
                    asset1, asset2 = parts
                    if ((asset1 in self.config['crypto_majors'] and asset2 in self.config['crypto_alts']) or
                        (asset1 in self.config['crypto_alts'] and asset2 in self.config['crypto_majors'])):
                        major_alt_pairs.append(pair)
            
            if major_alt_pairs:
                avg_corrs = {}
                for tf in ['7d', '14d', '30d', '60d']:
                    corrs = []
                    for pair in major_alt_pairs:
                        correlations = matrix.get(pair, {})
                        if tf in correlations:
                            corr = correlations[tf].get('correlation', np.nan)
                            if not self._is_nan(corr):
                                corrs.append(corr)
                    
                    if corrs:
                        avg_corrs[tf] = np.mean(corrs)
                
                if avg_corrs:
                    max_tf = max(avg_corrs, key=avg_corrs.get)
                    max_corr = avg_corrs[max_tf]
                    
                    if abs(max_corr) > 0.6:
                        insights.append({
                            'insight_type': 'structure',
                            'title': f'Strong Major-Alt Correlation on {max_tf}',
                            'description': f'Average correlation of {max_corr:.3f} between majors and alts suggests {"synchronized" if max_corr > 0 else "divergent"} movement',
                            'importance': 'medium',
                            'actionable': True,
                            'timeframe': max_tf
                        })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to analyze major-alt dynamics: {e}")
            return []
    
    def _analyze_risk_concentration(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze risk concentration patterns."""
        insights = []
        
        try:
            strong_correlations = summary.get('strong_correlations', 0)
            total_pairs = summary.get('total_pairs', 1)
            concentration_ratio = strong_correlations / total_pairs
            
            if concentration_ratio > 0.5:
                insights.append({
                    'insight_type': 'risk',
                    'title': 'High Risk Concentration Detected',
                    'description': f'{concentration_ratio:.1%} of pairs show strong correlation - diversification may be compromised',
                    'importance': 'high',
                    'actionable': True,
                    'timeframe': 'current'
                })
            elif concentration_ratio < 0.2:
                insights.append({
                    'insight_type': 'opportunity',
                    'title': 'Low Risk Concentration',
                    'description': f'Only {concentration_ratio:.1%} of pairs strongly correlated - excellent diversification opportunity',
                    'importance': 'medium',
                    'actionable': True,
                    'timeframe': 'current'
                })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to analyze risk concentration: {e}")
            return []
    
    def _identify_high_risk_pairs(self, matrix: Dict[str, Any]) -> List[str]:
        """Identify pairs with consistently high correlations across timeframes."""
        high_risk_pairs = []
        
        try:
            for pair, correlations in matrix.items():
                high_corr_count = 0
                total_timeframes = 0
                
                for tf_data in correlations.values():
                    if isinstance(tf_data, dict):
                        corr = tf_data.get('correlation', np.nan)
                        if not self._is_nan(corr):
                            total_timeframes += 1
                            if abs(corr) >= 0.7:
                                high_corr_count += 1
                
                if total_timeframes > 0 and high_corr_count / total_timeframes >= 0.75:
                    high_risk_pairs.append(pair)
            
            return high_risk_pairs
            
        except Exception as e:
            self.logger.error(f"Failed to identify high risk pairs: {e}")
            return []
    
    def _generate_pair_specific_recommendations(self, matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for specific pairs."""
        recommendations = []
        
        try:
            # Analyze each pair for specific recommendations
            for pair, correlations in matrix.items():
                if self._has_insufficient_data(correlations):
                    continue
                
                # Get strongest correlation across timeframes
                max_corr = 0
                best_tf = None
                for tf, data in correlations.items():
                    corr = data.get('correlation', np.nan)
                    if not self._is_nan(corr) and abs(corr) > abs(max_corr):
                        max_corr = corr
                        best_tf = tf
                
                if abs(max_corr) >= 0.7:
                    action = "Reduce relative position sizes" if max_corr > 0 else "Consider as hedge pair"
                    recommendations.append({
                        'type': 'pair_specific',
                        'priority': 'high' if abs(max_corr) >= 0.8 else 'medium',
                        'action': action,
                        'rationale': f'{pair} shows {abs(max_corr):.3f} correlation on {best_tf}',
                        'implementation': f'Monitor {pair} relationship closely for changes'
                    })
            
            return recommendations[:5]  # Return top 5 pair-specific recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate pair-specific recommendations: {e}")
            return []
    
    def _generate_rebalancing_recommendations(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate portfolio rebalancing recommendations."""
        recommendations = []
        
        try:
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            
            if avg_correlation > 0.6:
                recommendations.append({
                    'type': 'rebalancing',
                    'priority': 'high',
                    'action': 'Reduce portfolio concentration',
                    'rationale': 'High average correlation reduces diversification benefits',
                    'implementation': 'Consider reducing positions in highly correlated assets or adding uncorrelated alternatives'
                })
            elif avg_correlation < 0.3:
                recommendations.append({
                    'type': 'rebalancing',
                    'priority': 'medium',
                    'action': 'Consider increasing allocation to well-diversified assets',
                    'rationale': 'Low correlation environment provides excellent diversification',
                    'implementation': 'Equal-weight or volatility-adjusted allocation may be optimal'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate rebalancing recommendations: {e}")
            return []
    
    def _get_breakdown_trading_implication(self, short_term: float, long_term: float, change: float) -> str:
        """Get trading implication for correlation breakdown."""
        if change > 0.5:
            if short_term > long_term:
                return "Strong correlation increase - consider momentum strategies"
            else:
                return "Strong correlation breakdown - consider mean reversion strategies"
        else:
            return "Moderate correlation shift - monitor for continuation"
    
    def _get_timeframe_recommendation(self, timeframe: str, correlations: List[float], 
                                    significant_count: int, strong_count: int) -> str:
        """Get recommendation for specific timeframe."""
        avg_corr = np.mean(np.abs(correlations))
        
        if avg_corr < 0.3:
            return f"{timeframe} shows excellent diversification - consider for portfolio construction"
        elif avg_corr > 0.6:
            return f"{timeframe} shows high correlation - use for momentum strategies"
        elif strong_count > len(correlations) * 0.3:
            return f"{timeframe} has many strong correlations - monitor for trading opportunities"
        else:
            return f"{timeframe} shows moderate correlation patterns"
    
    def _identify_best_trading_timeframe(self, timeframe_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Identify the best timeframe for current trading opportunities."""
        try:
            best_tf = None
            best_score = 0
            
            for tf, data in timeframe_analysis.items():
                if tf == 'best_for_trading':
                    continue
                
                # Score based on number of strong correlations and significance
                strong_pairs = data.get('strong_pairs', 0)
                significant_pairs = data.get('significant_pairs', 0)
                total_pairs = data.get('total_pairs', 1)
                
                # Prefer timeframes with moderate number of strong correlations
                # (too many = less opportunity, too few = less actionable)
                ideal_strong_ratio = 0.3
                strong_ratio = strong_pairs / total_pairs
                significance_ratio = significant_pairs / total_pairs
                
                score = significance_ratio * (1 - abs(strong_ratio - ideal_strong_ratio))
                
                if score > best_score:
                    best_score = score
                    best_tf = tf
            
            return {
                'timeframe': best_tf,
                'score': best_score,
                'reason': f'Optimal balance of significant and actionable correlations'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to identify best trading timeframe: {e}")
            return {'timeframe': '14d', 'score': 0.5, 'reason': 'Default recommendation'}
    
    def _calculate_opportunity_score(self, pair: str, correlations: Dict[str, Any]) -> float:
        """Calculate opportunity score for a pair."""
        try:
            score = 0.0
            
            for tf, data in correlations.items():
                if not isinstance(data, dict):
                    continue
                
                corr = data.get('correlation', np.nan)
                significance = data.get('significance', False)
                
                if self._is_nan(corr) or not significance:
                    continue
                
                # Score based on correlation strength and actionability
                abs_corr = abs(corr)
                
                if abs_corr >= 0.8:
                    score += 1.0  # Very actionable
                elif abs_corr >= 0.6:
                    score += 0.7
                elif abs_corr >= 0.4:
                    score += 0.4
                elif abs_corr <= 0.1:
                    score += 0.5  # Divergence opportunity
                
                # Bonus for shorter timeframes (more immediate opportunities)
                if tf == '7d':
                    score *= 1.2
                elif tf == '14d':
                    score *= 1.1
            
            return min(score, 3.0)  # Cap at 3.0
            
        except Exception as e:
            self.logger.error(f"Failed to calculate opportunity score for {pair}: {e}")
            return 0.0
    
    def _get_best_timeframe_for_pair(self, correlations: Dict[str, Any]) -> str:
        """Get the best timeframe for trading a specific pair."""
        try:
            best_tf = None
            best_score = 0
            
            for tf, data in correlations.items():
                if not isinstance(data, dict):
                    continue
                
                corr = data.get('correlation', np.nan)
                significance = data.get('significance', False)
                
                if self._is_nan(corr) or not significance:
                    continue
                
                # Score based on actionability
                abs_corr = abs(corr)
                score = 0
                
                if abs_corr >= 0.8 or abs_corr <= 0.1:
                    score = abs_corr if abs_corr >= 0.8 else (0.1 - abs_corr) * 10
                elif abs_corr >= 0.6:
                    score = abs_corr * 0.8
                
                if score > best_score:
                    best_score = score
                    best_tf = tf
            
            return best_tf or '14d'
            
        except Exception as e:
            self.logger.error(f"Failed to get best timeframe: {e}")
            return '14d'
    
    def _get_pair_recommendation(self, pair: str, correlations: Dict[str, Any], score: float) -> str:
        """Get specific recommendation for a pair."""
        try:
            if score >= 2.0:
                return f"High opportunity - strong trading signals detected for {pair}"
            elif score >= 1.0:
                return f"Moderate opportunity - monitor {pair} for entry signals"
            elif score >= 0.5:
                return f"Low opportunity - consider {pair} for diversification"
            else:
                return f"Minimal opportunity - {pair} shows weak signals"
                
        except Exception as e:
            self.logger.error(f"Failed to get pair recommendation: {e}")
            return "Monitor for changes"
    
    def _summarize_market_conditions(self, avg_correlation: float, summary: Dict[str, Any]) -> str:
        """Summarize current market conditions."""
        try:
            strong_correlations = summary.get('strong_correlations', 0)
            total_pairs = summary.get('total_pairs', 1)
            strong_ratio = strong_correlations / total_pairs
            
            if avg_correlation < 0.3 and strong_ratio < 0.2:
                return "Excellent diversification environment with low correlation across assets"
            elif avg_correlation > 0.6 or strong_ratio > 0.4:
                return "High correlation environment - trending market conditions likely"
            elif summary.get('negative_correlations', 0) > total_pairs * 0.3:
                return "High volatility environment with significant negative correlations"
            else:
                return "Mixed correlation environment with moderate diversification benefits"
                
        except Exception as e:
            self.logger.error(f"Failed to summarize market conditions: {e}")
            return "Market conditions analysis unavailable"
    
    def _get_top_recommendations(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
        """Get top 3 actionable recommendations."""
        try:
            recommendations = []
            
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            strong_correlations = summary.get('strong_correlations', 0)
            total_pairs = summary.get('total_pairs', 1)
            
            # Top recommendation based on market regime
            if avg_correlation < 0.3:
                recommendations.append("Increase position sizes - excellent diversification opportunity")
            elif avg_correlation > 0.6:
                recommendations.append("Reduce portfolio concentration - high correlation reduces diversification")
            else:
                recommendations.append("Maintain balanced allocation - moderate correlation environment")
            
            # Second recommendation based on opportunities
            high_opportunity_pairs = [p for p in matrix.keys() if self._calculate_opportunity_score(p, matrix[p]) > 1.0]
            if len(high_opportunity_pairs) >= 3:
                recommendations.append(f"Focus on {len(high_opportunity_pairs)} high-opportunity pairs for active trading")
            else:
                recommendations.append("Limited active trading opportunities - focus on long-term positioning")
            
            # Third recommendation based on risk
            if strong_correlations / total_pairs > 0.5:
                recommendations.append("Monitor position sizing carefully - high correlation concentration detected")
            else:
                recommendations.append("Current correlation levels support diversified strategies")
            
            return recommendations[:3]
            
        except Exception as e:
            self.logger.error(f"Failed to get top recommendations: {e}")
            return ["Monitor market conditions", "Maintain balanced portfolio", "Review correlation changes"]
    
    def _get_immediate_actions(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
        """Get immediate actions required based on analysis."""
        try:
            actions = []
            
            # Check for high-priority situations
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            
            if avg_correlation > 0.8:
                actions.append("URGENT: Reduce portfolio concentration - extremely high correlation detected")
            
            # Check for breakdown signals
            breakdown_count = 0
            for pair, correlations in matrix.items():
                short_term = correlations.get('7d', {}).get('correlation', np.nan)
                long_term = correlations.get('60d', {}).get('correlation', np.nan)
                
                if not self._is_nan(short_term) and not self._is_nan(long_term):
                    if abs(short_term - long_term) > 0.5:
                        breakdown_count += 1
            
            if breakdown_count >= 3:
                actions.append(f"Monitor {breakdown_count} pairs showing correlation breakdowns for trading opportunities")
            
            # Check for high-value opportunities
            high_value_opportunities = len([p for p in matrix.keys() if self._calculate_opportunity_score(p, matrix[p]) > 2.0])
            if high_value_opportunities >= 2:
                actions.append(f"Evaluate {high_value_opportunities} high-value trading opportunities immediately")
            
            if not actions:
                actions.append("No immediate actions required - continue monitoring")
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Failed to get immediate actions: {e}")
            return ["Monitor market conditions for changes"]
    
    def _get_monitoring_priorities(self, matrix: Dict[str, Any]) -> List[str]:
        """Get monitoring priorities based on analysis."""
        try:
            priorities = []
            
            # High-opportunity pairs
            high_opportunity_pairs = []
            for pair, correlations in matrix.items():
                if self._calculate_opportunity_score(pair, correlations) > 1.5:
                    high_opportunity_pairs.append(pair)
            
            if high_opportunity_pairs:
                priorities.append(f"Monitor high-opportunity pairs: {', '.join(high_opportunity_pairs[:3])}")
            
            # Breakdown candidates
            breakdown_candidates = []
            for pair, correlations in matrix.items():
                short_term = correlations.get('7d', {}).get('correlation', np.nan)
                medium_term = correlations.get('30d', {}).get('correlation', np.nan)
                
                if not self._is_nan(short_term) and not self._is_nan(medium_term):
                    if abs(short_term - medium_term) > 0.3:
                        breakdown_candidates.append(pair)
            
            if breakdown_candidates:
                priorities.append(f"Watch for correlation changes: {', '.join(breakdown_candidates[:3])}")
            
            # Risk concentration
            high_risk_pairs = self._identify_high_risk_pairs(matrix)
            if high_risk_pairs:
                priorities.append(f"Monitor risk concentration: {', '.join(high_risk_pairs[:3])}")
            
            if not priorities:
                priorities.append("Continue routine monitoring of all correlation pairs")
            
            return priorities
            
        except Exception as e:
            self.logger.error(f"Failed to get monitoring priorities: {e}")
            return ["Monitor all pairs for correlation changes"]
    
    def _get_risk_alerts(self, matrix: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
        """Get risk alerts based on analysis."""
        try:
            alerts = []
            
            avg_correlation = abs(summary.get('average_correlation_strength', 0.0))
            strong_correlations = summary.get('strong_correlations', 0)
            total_pairs = summary.get('total_pairs', 1)
            
            # High correlation risk
            if avg_correlation > 0.7:
                alerts.append(f"HIGH RISK: Average correlation {avg_correlation:.3f} - diversification severely compromised")
            elif avg_correlation > 0.5:
                alerts.append(f"MEDIUM RISK: Average correlation {avg_correlation:.3f} - reduced diversification effectiveness")
            
            # Concentration risk
            if strong_correlations / total_pairs > 0.6:
                alerts.append(f"HIGH CONCENTRATION: {strong_correlations}/{total_pairs} pairs strongly correlated")
            
            # Specific high-risk pairs
            very_high_corr_pairs = []
            for pair, correlations in matrix.items():
                for tf_data in correlations.values():
                    if isinstance(tf_data, dict):
                        corr = tf_data.get('correlation', np.nan)
                        if not self._is_nan(corr) and abs(corr) >= 0.9:
                            very_high_corr_pairs.append(pair)
                            break
            
            if very_high_corr_pairs:
                alerts.append(f"EXTREME CORRELATION: {', '.join(very_high_corr_pairs[:3])} showing correlation >= 0.9")
            
            if not alerts:
                alerts.append("No significant risk alerts - correlation levels within normal ranges")
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get risk alerts: {e}")
            return ["Risk analysis unavailable"]

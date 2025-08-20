"""
Statistical analyzer for correlation analysis module.
Provides statistical analysis utilities for correlation changes.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats


class StatisticalAnalyzer:
    """
    Statistical analysis utilities for correlation analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the statistical analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.config = {
            'z_score_threshold': 3.0,
            'significance_level': 0.05,
            'min_historical_points': 20,
            'confidence_level': 0.95
        }
        
        if config:
            self.config.update(config)
    
    def calculate_correlation_zscore(self, current: float, historical: List[float]) -> float:
        """
        Calculate z-score for correlation change.
        
        Args:
            current: Current correlation value
            historical: List of historical correlation values
            
        Returns:
            float: Z-score for the correlation change
        """
        try:
            if not historical or len(historical) < self.config['min_historical_points']:
                self.logger.warning(f"Insufficient historical data: {len(historical) if historical else 0} < {self.config['min_historical_points']}")
                return np.nan
            
            # Convert to numpy array for calculations
            historical_array = np.array(historical)
            
            # Calculate mean and standard deviation of historical correlations
            mean_correlation = np.mean(historical_array)
            std_correlation = np.std(historical_array)
            
            if std_correlation == 0:
                self.logger.warning("Zero standard deviation in historical correlations")
                return np.nan
            
            # Calculate z-score
            z_score = (current - mean_correlation) / std_correlation
            
            self.logger.debug(f"Z-score calculation: current={current:.4f}, mean={mean_correlation:.4f}, std={std_correlation:.4f}, z_score={z_score:.4f}")
            
            return z_score
            
        except Exception as e:
            self.logger.error(f"Z-score calculation failed: {e}")
            return np.nan
    
    def calculate_correlation_significance(self, correlation: float, sample_size: int) -> Dict[str, float]:
        """
        Calculate statistical significance of correlation.
        
        Args:
            correlation: Correlation coefficient
            sample_size: Number of data points used in correlation
            
        Returns:
            Dict[str, float]: Dictionary with p-value, t-statistic, and significance
        """
        try:
            if sample_size < 3:
                return {'p_value': np.nan, 't_statistic': np.nan, 'significant': False}
            
            # Handle perfect correlations (±1) to avoid division by zero
            if abs(correlation) >= 0.9999:
                # Perfect correlation is always significant with p-value approaching 0
                return {
                    'p_value': 0.0,
                    't_statistic': np.inf if correlation > 0 else -np.inf,
                    'significant': True
                }
            
            # Calculate t-statistic for correlation
            t_statistic = correlation * np.sqrt((sample_size - 2) / (1 - correlation**2))
            
            # Calculate p-value (two-tailed test)
            p_value = 2 * (1 - stats.t.cdf(abs(t_statistic), sample_size - 2))
            
            # Determine significance
            significant = p_value < self.config['significance_level']
            
            result = {
                'p_value': p_value,
                't_statistic': t_statistic,
                'significant': significant
            }
            
            self.logger.debug(f"Correlation significance: r={correlation:.4f}, n={sample_size}, t={t_statistic:.4f}, p={p_value:.4f}, significant={significant}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Correlation significance calculation failed: {e}")
            return {'p_value': np.nan, 't_statistic': np.nan, 'significant': False}
    
    def calculate_confidence_interval(self, correlation: float, sample_size: int, confidence_level: float = None) -> Dict[str, float]:
        """
        Calculate confidence interval for correlation coefficient.
        
        Args:
            correlation: Correlation coefficient
            sample_size: Number of data points used in correlation
            confidence_level: Confidence level (default from config)
            
        Returns:
            Dict[str, float]: Dictionary with lower and upper confidence bounds
        """
        try:
            if sample_size < 3:
                return {'lower': np.nan, 'upper': np.nan}
            
            if confidence_level is None:
                confidence_level = self.config['confidence_level']
            
            # Fisher's z-transformation
            z_correlation = 0.5 * np.log((1 + correlation) / (1 - correlation))
            
            # Standard error of z-transformed correlation
            se_z = 1 / np.sqrt(sample_size - 3)
            
            # Critical value for confidence interval
            alpha = 1 - confidence_level
            critical_value = stats.norm.ppf(1 - alpha / 2)
            
            # Confidence interval for z-transformed correlation
            z_lower = z_correlation - critical_value * se_z
            z_upper = z_correlation + critical_value * se_z
            
            # Transform back to correlation scale
            lower_correlation = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
            upper_correlation = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
            
            result = {
                'lower': lower_correlation,
                'upper': upper_correlation
            }
            
            self.logger.debug(f"Confidence interval: r={correlation:.4f}, CI=[{lower_correlation:.4f}, {upper_correlation:.4f}]")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Confidence interval calculation failed: {e}")
            return {'lower': np.nan, 'upper': np.nan}
    
    def detect_correlation_breakout(self, current_correlation: float, historical_correlations: List[float]) -> Dict[str, any]:
        """
        Detect correlation breakout using z-score analysis.
        
        Args:
            current_correlation: Current correlation value
            historical_correlations: List of historical correlation values
            
        Returns:
            Dict[str, any]: Breakout detection results
        """
        try:
            # Calculate z-score
            z_score = self.calculate_correlation_zscore(current_correlation, historical_correlations)
            
            if np.isnan(z_score):
                return {
                    'breakout_detected': False,
                    'z_score': np.nan,
                    'severity': 'none',
                    'direction': 'none'
                }
            
            # Determine if breakout is detected
            breakout_detected = abs(z_score) >= self.config['z_score_threshold']
            
            # Determine severity
            if abs(z_score) >= 4.0:
                severity = 'extreme'
            elif abs(z_score) >= 3.5:
                severity = 'high'
            elif abs(z_score) >= 3.0:
                severity = 'moderate'
            else:
                severity = 'low'
            
            # Determine direction
            if z_score > 0:
                direction = 'positive'
            elif z_score < 0:
                direction = 'negative'
            else:
                direction = 'none'
            
            result = {
                'breakout_detected': breakout_detected,
                'z_score': z_score,
                'severity': severity,
                'direction': direction,
                'threshold': self.config['z_score_threshold']
            }
            
            if breakout_detected:
                self.logger.info(f"Correlation breakout detected: z_score={z_score:.4f}, severity={severity}, direction={direction}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Correlation breakout detection failed: {e}")
            return {
                'breakout_detected': False,
                'z_score': np.nan,
                'severity': 'none',
                'direction': 'none'
            }
    
    def analyze_correlation_stability(self, correlation_series: pd.Series, window_days: int = 30) -> Dict[str, float]:
        """
        Analyze the stability of correlation over time.
        
        Args:
            correlation_series: Time series of correlation values
            window_days: Window size for stability analysis
            
        Returns:
            Dict[str, float]: Stability metrics
        """
        try:
            if correlation_series.empty:
                return {'stability_score': np.nan, 'volatility': np.nan, 'trend': np.nan}
            
            # Calculate stability metrics
            volatility = correlation_series.std()
            trend = correlation_series.diff().mean()
            
            # Calculate stability score (inverse of volatility, normalized)
            max_volatility = 2.0  # Maximum expected volatility for correlations
            stability_score = max(0, 1 - (volatility / max_volatility))
            
            result = {
                'stability_score': stability_score,
                'volatility': volatility,
                'trend': trend
            }
            
            self.logger.debug(f"Correlation stability: score={stability_score:.4f}, volatility={volatility:.4f}, trend={trend:.4f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Correlation stability analysis failed: {e}")
            return {'stability_score': np.nan, 'volatility': np.nan, 'trend': np.nan}

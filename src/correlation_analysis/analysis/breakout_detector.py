"""
Breakout detector for correlation analysis module.
Detects correlation breakouts using z-score analysis.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from scipy import stats

from .statistical_analyzer import StatisticalAnalyzer


class BreakoutDetector:
    """
    Detects correlation breakouts using statistical analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the breakout detector.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = {
            'z_score_threshold': 3.0,
            'min_data_points': 20,
            'confidence_level': 0.95,
            'breakout_confirmation_windows': 2,
            'min_breakout_duration_minutes': 15,
            'persistence_validation_enabled': True,
            'statistical_validation_enabled': True,
            'regime_change_detection_enabled': True
        }
        if config:
            self.config.update(config)
        
        self.statistical_analyzer = StatisticalAnalyzer(config)
        
        self.logger.info(f"Breakout detector initialized with threshold: {self.config['z_score_threshold']}")
    
    def detect_correlation_breakout(self, z_score: float, threshold: float = None) -> bool:
        """
        Detect correlation breakout based on z-score.
        
        Args:
            z_score: Z-score value to check
            threshold: Z-score threshold (defaults to config value)
            
        Returns:
            bool: True if breakout detected
        """
        try:
            if threshold is None:
                threshold = self.config['z_score_threshold']
            
            # Check if z-score exceeds threshold
            breakout_detected = abs(z_score) >= threshold
            
            if breakout_detected:
                self.logger.info(f"Correlation breakout detected: z_score={z_score:.4f}, threshold={threshold}")
            else:
                self.logger.debug(f"No breakout detected: z_score={z_score:.4f}, threshold={threshold}")
            
            return breakout_detected
            
        except Exception as e:
            self.logger.error(f"Error detecting correlation breakout: {e}")
            return False
    
    def detect_breakout_with_analysis(self, current_correlation: float, historical_correlations: List[float]) -> Dict[str, Any]:
        """
        Detect correlation breakout with comprehensive analysis.
        
        Args:
            current_correlation: Current correlation value
            historical_correlations: List of historical correlation values
            
        Returns:
            Dict[str, Any]: Breakout analysis results
        """
        try:
            if len(historical_correlations) < self.config['min_data_points']:
                self.logger.warning(f"Insufficient historical data: {len(historical_correlations)} < {self.config['min_data_points']}")
                return {
                    'breakout_detected': False,
                    'z_score': np.nan,
                    'severity': 'none',
                    'direction': 'none',
                    'confidence': 0.0,
                    'reason': 'insufficient_data'
                }
            
            # Calculate z-score
            z_score = self.statistical_analyzer.calculate_correlation_zscore(current_correlation, historical_correlations)
            
            if np.isnan(z_score):
                return {
                    'breakout_detected': False,
                    'z_score': np.nan,
                    'severity': 'none',
                    'direction': 'none',
                    'confidence': 0.0,
                    'reason': 'invalid_z_score'
                }
            
            # Detect breakout
            breakout_detected = self.detect_correlation_breakout(z_score)
            
            # Determine severity
            severity = self._determine_severity(z_score)
            
            # Determine direction
            direction = self._determine_direction(z_score)
            
            # Calculate confidence
            confidence = self._calculate_confidence(z_score, len(historical_correlations))
            
            # Additional statistical validation if enabled
            statistical_validation = {}
            if self.config.get('statistical_validation_enabled', True):
                statistical_validation = self.validate_breakout_significance(z_score, len(historical_correlations))
            
            result = {
                'breakout_detected': breakout_detected,
                'z_score': float(z_score),
                'severity': severity,
                'direction': direction,
                'confidence': confidence,
                'threshold': self.config['z_score_threshold'],
                'current_correlation': float(current_correlation),
                'historical_mean': float(np.mean(historical_correlations)),
                'historical_std': float(np.std(historical_correlations)),
                'sample_size': len(historical_correlations),
                'timestamp': int(datetime.now().timestamp() * 1000),
                'statistical_validation': statistical_validation
            }
            
            if breakout_detected:
                self.logger.info(f"Breakout analysis: {severity} {direction} breakout detected (z={z_score:.4f}, confidence={confidence:.2f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in breakout analysis: {e}")
            return {
                'breakout_detected': False,
                'z_score': np.nan,
                'severity': 'none',
                'direction': 'none',
                'confidence': 0.0,
                'reason': f'error: {str(e)}'
            }
    
    def validate_breakout_persistence(self, breakouts: List[Dict], min_duration_minutes: int = None) -> List[Dict]:
        """
        Filter breakouts that persist for minimum duration.
        
        Args:
            breakouts: List of breakout detections
            min_duration_minutes: Minimum duration for persistence (defaults to config)
            
        Returns:
            List[Dict]: Filtered breakouts that meet persistence criteria
        """
        try:
            if not self.config.get('persistence_validation_enabled', True):
                return breakouts
            
            if min_duration_minutes is None:
                min_duration_minutes = self.config.get('min_breakout_duration_minutes', 15)
            
            if not breakouts:
                return []
            
            # Sort breakouts by timestamp
            sorted_breakouts = sorted(breakouts, key=lambda x: x.get('timestamp', 0))
            
            persistent_breakouts = []
            current_breakout_start = None
            current_breakout_end = None
            
            for breakout in sorted_breakouts:
                timestamp = breakout.get('timestamp', 0)
                
                if current_breakout_start is None:
                    # Start new breakout period
                    current_breakout_start = timestamp
                    current_breakout_end = timestamp
                else:
                    # Check if this breakout is within the persistence window
                    time_diff_minutes = (timestamp - current_breakout_end) / (1000 * 60)
                    
                    if time_diff_minutes <= min_duration_minutes:
                        # Extend current breakout period
                        current_breakout_end = timestamp
                    else:
                        # Check if previous breakout period meets duration requirement
                        breakout_duration = (current_breakout_end - current_breakout_start) / (1000 * 60)
                        
                        if breakout_duration >= min_duration_minutes:
                            # Add all breakouts in this period to persistent breakouts
                            for b in sorted_breakouts:
                                if current_breakout_start <= b.get('timestamp', 0) <= current_breakout_end:
                                    b['persistence_validated'] = True
                                    b['breakout_duration_minutes'] = breakout_duration
                                    persistent_breakouts.append(b)
                        
                        # Start new breakout period
                        current_breakout_start = timestamp
                        current_breakout_end = timestamp
            
            # Don't forget the last breakout period
            if current_breakout_start is not None:
                breakout_duration = (current_breakout_end - current_breakout_start) / (1000 * 60)
                
                if breakout_duration >= min_duration_minutes:
                    for b in sorted_breakouts:
                        if current_breakout_start <= b.get('timestamp', 0) <= current_breakout_end:
                            b['persistence_validated'] = True
                            b['breakout_duration_minutes'] = breakout_duration
                            persistent_breakouts.append(b)
            
            self.logger.info(f"Persistence validation: {len(persistent_breakouts)}/{len(breakouts)} breakouts validated")
            return persistent_breakouts
            
        except Exception as e:
            self.logger.error(f"Error in breakout persistence validation: {e}")
            return breakouts
    
    def validate_breakout_significance(self, z_score: float, sample_size: int) -> Dict[str, float]:
        """
        Validate breakout significance using additional statistical tests.
        
        Args:
            z_score: Z-score value
            sample_size: Number of data points
            
        Returns:
            Dict[str, float]: Statistical validation results
        """
        try:
            if not self.config.get('statistical_validation_enabled', True):
                return {}
            
            validation_results = {}
            
            # Kolmogorov-Smirnov test for normality (if sample size is sufficient)
            if sample_size >= 30:
                try:
                    # Generate theoretical normal distribution for comparison
                    theoretical_data = np.random.normal(0, 1, sample_size)
                    ks_statistic, ks_p_value = stats.ks_2samp([z_score] * sample_size, theoretical_data)
                    validation_results['ks_test_statistic'] = float(ks_statistic)
                    validation_results['ks_test_p_value'] = float(ks_p_value)
                    validation_results['ks_test_significant'] = ks_p_value < 0.05
                except Exception as e:
                    self.logger.debug(f"KS test failed: {e}")
            
            # Chi-square test for goodness of fit
            try:
                # Test if z-score is significantly different from expected normal distribution
                expected_freq = stats.norm.pdf(z_score, 0, 1)
                observed_freq = 1  # Single observation
                chi2_statistic, chi2_p_value = stats.chisquare([observed_freq], [expected_freq])
                validation_results['chi2_test_statistic'] = float(chi2_statistic)
                validation_results['chi2_test_p_value'] = float(chi2_p_value)
                validation_results['chi2_test_significant'] = chi2_p_value < 0.05
            except Exception as e:
                self.logger.debug(f"Chi-square test failed: {e}")
            
            # Confidence interval calculation
            try:
                confidence_level = self.config.get('confidence_level', 0.95)
                z_critical = stats.norm.ppf((1 + confidence_level) / 2)
                margin_of_error = z_critical * (1 / np.sqrt(sample_size))
                
                validation_results['confidence_interval_lower'] = float(z_score - margin_of_error)
                validation_results['confidence_interval_upper'] = float(z_score + margin_of_error)
                validation_results['margin_of_error'] = float(margin_of_error)
            except Exception as e:
                self.logger.debug(f"Confidence interval calculation failed: {e}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error in statistical validation: {e}")
            return {}
    
    def detect_regime_change(self, correlation_series: List[float], window_size: int = 30) -> Dict[str, Any]:
        """
        Detect structural breaks in correlation regime using CUSUM test.
        
        Args:
            correlation_series: List of correlation values over time
            window_size: Size of rolling window for regime detection
            
        Returns:
            Dict[str, Any]: Regime change detection results
        """
        try:
            if not self.config.get('regime_change_detection_enabled', True):
                return {'regime_change_detected': False}
            
            if len(correlation_series) < window_size * 2:
                self.logger.warning(f"Insufficient data for regime change detection: {len(correlation_series)} < {window_size * 2}")
                return {'regime_change_detected': False, 'reason': 'insufficient_data'}
            
            # Calculate rolling mean and standard deviation
            rolling_mean = []
            rolling_std = []
            
            for i in range(window_size, len(correlation_series)):
                window_data = correlation_series[i-window_size:i]
                rolling_mean.append(np.mean(window_data))
                rolling_std.append(np.std(window_data))
            
            if len(rolling_mean) < 10:
                return {'regime_change_detected': False, 'reason': 'insufficient_rolling_data'}
            
            # Calculate CUSUM statistic
            mean_rolling_mean = np.mean(rolling_mean)
            std_rolling_mean = np.std(rolling_mean)
            
            if std_rolling_mean == 0:
                return {'regime_change_detected': False, 'reason': 'no_variation'}
            
            # Calculate CUSUM
            cusum_positive = []
            cusum_negative = []
            
            for i, value in enumerate(rolling_mean):
                if i == 0:
                    cusum_positive.append(max(0, (value - mean_rolling_mean) / std_rolling_mean))
                    cusum_negative.append(max(0, (mean_rolling_mean - value) / std_rolling_mean))
                else:
                    cusum_positive.append(max(0, cusum_positive[i-1] + (value - mean_rolling_mean) / std_rolling_mean))
                    cusum_negative.append(max(0, cusum_negative[i-1] + (mean_rolling_mean - value) / std_rolling_mean))
            
            # Detect regime change if CUSUM exceeds threshold
            cusum_threshold = 2.0  # Configurable threshold
            max_cusum_positive = max(cusum_positive)
            max_cusum_negative = max(cusum_negative)
            
            regime_change_detected = max_cusum_positive > cusum_threshold or max_cusum_negative > cusum_threshold
            
            result = {
                'regime_change_detected': regime_change_detected,
                'cusum_threshold': cusum_threshold,
                'max_cusum_positive': float(max_cusum_positive),
                'max_cusum_negative': float(max_cusum_negative),
                'rolling_mean_mean': float(mean_rolling_mean),
                'rolling_mean_std': float(std_rolling_mean),
                'window_size': window_size
            }
            
            if regime_change_detected:
                self.logger.info(f"Regime change detected: max_cusum_positive={max_cusum_positive:.4f}, max_cusum_negative={max_cusum_negative:.4f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in regime change detection: {e}")
            return {'regime_change_detected': False, 'reason': f'error: {str(e)}'}
    
    def detect_rolling_breakouts(self, correlation_series: List[float], window_size: int = 30) -> List[Dict[str, Any]]:
        """
        Detect breakouts in a rolling window of correlations.
        
        Args:
            correlation_series: List of correlation values over time
            window_size: Size of rolling window for historical comparison
            
        Returns:
            List[Dict[str, Any]]: List of breakout detections
        """
        try:
            if len(correlation_series) < window_size + self.config['min_data_points']:
                self.logger.warning(f"Insufficient data for rolling breakout detection: {len(correlation_series)} < {window_size + self.config['min_data_points']}")
                return []
            
            breakouts = []
            
            for i in range(window_size, len(correlation_series)):
                current_correlation = correlation_series[i]
                historical_window = correlation_series[i-window_size:i]
                
                # Detect breakout for this point
                breakout_result = self.detect_breakout_with_analysis(current_correlation, historical_window)
                
                if breakout_result['breakout_detected']:
                    breakout_result['index'] = i
                    breakout_result['timestamp_index'] = i
                    breakouts.append(breakout_result)
            
            # Apply persistence validation if enabled
            if self.config.get('persistence_validation_enabled', True):
                breakouts = self.validate_breakout_persistence(breakouts)
            
            self.logger.info(f"Detected {len(breakouts)} breakouts in rolling analysis")
            return breakouts
            
        except Exception as e:
            self.logger.error(f"Error in rolling breakout detection: {e}")
            return []
    
    def detect_breakout_clusters(self, breakouts: List[Dict[str, Any]], time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Detect clusters of breakouts within a time window.
        
        Args:
            breakouts: List of breakout detections
            time_window_minutes: Time window for clustering (minutes)
            
        Returns:
            List[Dict[str, Any]]: List of breakout clusters
        """
        try:
            if not breakouts:
                return []
            
            # Sort breakouts by timestamp
            sorted_breakouts = sorted(breakouts, key=lambda x: x.get('timestamp', 0))
            
            clusters = []
            current_cluster = []
            
            for breakout in sorted_breakouts:
                if not current_cluster:
                    current_cluster = [breakout]
                else:
                    # Check if this breakout is within the time window of the last breakout in current cluster
                    last_breakout_time = current_cluster[-1].get('timestamp', 0)
                    current_breakout_time = breakout.get('timestamp', 0)
                    
                    time_diff_minutes = (current_breakout_time - last_breakout_time) / (1000 * 60)
                    
                    if time_diff_minutes <= time_window_minutes:
                        current_cluster.append(breakout)
                    else:
                        # End current cluster and start new one
                        if len(current_cluster) > 1:
                            clusters.append(self._create_cluster_summary(current_cluster))
                        current_cluster = [breakout]
            
            # Don't forget the last cluster
            if len(current_cluster) > 1:
                clusters.append(self._create_cluster_summary(current_cluster))
            
            self.logger.info(f"Detected {len(clusters)} breakout clusters")
            return clusters
            
        except Exception as e:
            self.logger.error(f"Error detecting breakout clusters: {e}")
            return []
    
    def _determine_severity(self, z_score: float) -> str:
        """
        Determine severity level based on z-score.
        
        Args:
            z_score: Z-score value
            
        Returns:
            str: Severity level
        """
        abs_z = abs(z_score)
        
        if abs_z >= 3.0:
            return 'extreme'
        elif abs_z >= 2.5:
            return 'high'
        elif abs_z >= 2.0:
            return 'moderate'
        elif abs_z >= 1.5:
            return 'low'
        else:
            return 'none'
    
    def _determine_direction(self, z_score: float) -> str:
        """
        Determine breakout direction based on z-score.
        
        Args:
            z_score: Z-score value
            
        Returns:
            str: Breakout direction
        """
        if z_score > 0:
            return 'positive'
        elif z_score < 0:
            return 'negative'
        else:
            return 'none'
    
    def _calculate_confidence(self, z_score: float, sample_size: int) -> float:
        """
        Calculate confidence level for breakout detection.
        
        Args:
            z_score: Z-score value
            sample_size: Number of data points
            
        Returns:
            float: Confidence level (0.0 to 1.0)
        """
        try:
            # Base confidence on z-score magnitude and sample size
            z_confidence = min(abs(z_score) / 4.0, 1.0)  # Normalize to 0-1
            
            # Sample size confidence (more data = higher confidence)
            size_confidence = min(sample_size / 100.0, 1.0)
            
            # Combined confidence
            confidence = (z_confidence * 0.7) + (size_confidence * 0.3)
            
            return min(confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def _create_cluster_summary(self, cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create summary for a cluster of breakouts.
        
        Args:
            cluster: List of breakout detections in the cluster
            
        Returns:
            Dict[str, Any]: Cluster summary
        """
        try:
            if not cluster:
                return {}
            
            # Calculate cluster statistics
            z_scores = [b.get('z_score', 0) for b in cluster]
            severities = [b.get('severity', 'none') for b in cluster]
            directions = [b.get('direction', 'none') for b in cluster]
            
            # Determine dominant characteristics
            dominant_severity = max(set(severities), key=severities.count)
            dominant_direction = max(set(directions), key=directions.count)
            
            # Calculate time span
            timestamps = [b.get('timestamp', 0) for b in cluster]
            time_span_minutes = (max(timestamps) - min(timestamps)) / (1000 * 60)
            
            return {
                'cluster_id': f"cluster_{min(timestamps)}",
                'breakout_count': len(cluster),
                'time_span_minutes': time_span_minutes,
                'average_z_score': float(np.mean(z_scores)),
                'max_z_score': float(max(z_scores)),
                'dominant_severity': dominant_severity,
                'dominant_direction': dominant_direction,
                'start_timestamp': min(timestamps),
                'end_timestamp': max(timestamps),
                'breakouts': cluster
            }
            
        except Exception as e:
            self.logger.error(f"Error creating cluster summary: {e}")
            return {}

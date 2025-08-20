"""
Correlation monitor for correlation analysis module.
Monitors single pair for correlation changes and generates alerts on breakouts.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np

from ..data.data_fetcher import DataFetcher
from ..data.data_normalizer import DataNormalizer
from ..core.correlation_calculator import CorrelationCalculator
from ..analysis.statistical_analyzer import StatisticalAnalyzer
from ..analysis.breakout_detector import BreakoutDetector
from ..alerts.correlation_alert_system import CorrelationAlertSystem
from ..alerts.discord_integration import CorrelationDiscordIntegration
from ..storage.correlation_storage import CorrelationStorage
from ..storage.state_manager import CorrelationStateManager


class CorrelationMonitor:
    """
    Monitors a single asset pair for correlation changes and generates alerts on breakouts.
    """
    
    def __init__(self, pair: str, config: Optional[Dict] = None):
        """
        Initialize the correlation monitor for a specific pair.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.pair = pair
        
        # Parse pair into primary and secondary assets
        self.primary_asset, self.secondary_asset = self._parse_pair(pair)
        
        # Configuration with defaults
        self.config = {
            'correlation_windows': [7, 14, 30],
            'min_data_points': 20,
            'z_score_threshold': 3.0,
            'monitoring_interval_minutes': 15,
            'data_lookback_days': 60,
            'alert_on_breakout': True,
            'store_correlation_history': True,
            'store_breakout_history': True,
            'enable_statistical_validation': True,
            'enable_persistence_validation': True,
            'max_retries': 3,
            'retry_delay': 1.0,
            'enable_performance_monitoring': True
        }
        if config:
            self.config.update(config)
        
        # Initialize components
        self.data_fetcher = DataFetcher()
        self.data_normalizer = DataNormalizer()
        self.correlation_calculator = CorrelationCalculator()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.breakout_detector = BreakoutDetector({
            'z_score_threshold': self.config['z_score_threshold'],
            'min_data_points': self.config['min_data_points'],
            'persistence_validation_enabled': self.config['enable_persistence_validation'],
            'statistical_validation_enabled': self.config['enable_statistical_validation']
        })
        self.alert_system = CorrelationAlertSystem()
        
        # Initialize Discord integration if configuration is provided
        discord_config = config.get('discord_config') if config else None
        if discord_config:
            self.discord_integration = CorrelationDiscordIntegration(config=discord_config)
            self.logger.info("Discord integration enabled for correlation alerts")
        else:
            self.discord_integration = CorrelationDiscordIntegration()
            self.logger.info("Discord integration disabled - no configuration provided")
        
        self.storage = CorrelationStorage()
        self.state_manager = CorrelationStateManager()
        
        # Load existing state
        self.state = self.state_manager.load_correlation_state()
        
        self.logger.info(f"Correlation monitor initialized for {pair} with windows: {self.config['correlation_windows']}")
    
    def _parse_pair(self, pair: str) -> Tuple[str, str]:
        """
        Parse pair string into primary and secondary assets.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH', 'bitcoin_ethereum')
            
        Returns:
            Tuple[str, str]: (primary_asset, secondary_asset)
        """
        # Handle common crypto pairs
        pair_mapping = {
            'BTC_ETH': ('bitcoin', 'ethereum'),
            'BTC_USDT': ('bitcoin', 'tether'),
            'ETH_USDT': ('ethereum', 'tether'),
            'BTC_ADA': ('bitcoin', 'cardano'),
            'ETH_ADA': ('ethereum', 'cardano'),
            'BTC_DOGE': ('bitcoin', 'dogecoin'),
            'ETH_DOGE': ('ethereum', 'dogecoin')
        }
        
        if pair in pair_mapping:
            return pair_mapping[pair]
        
        # Handle underscore-separated pairs
        if '_' in pair:
            parts = pair.split('_')
            if len(parts) >= 2:
                # Convert common abbreviations to full names
                asset_mapping = {
                    # Crypto assets
                    'BTC': 'bitcoin',
                    'ETH': 'ethereum',
                    'USDT': 'tether',
                    'ADA': 'cardano',
                    'DOGE': 'dogecoin',
                    'XRP': 'ripple',
                    'LTC': 'litecoin',
                    'BCH': 'bitcoin-cash',
                    'SOL': 'solana',
                    'BTT': 'bittensor',
                    'FET': 'fetch-ai',
                    'OCEAN': 'ocean-protocol',
                    'RNDR': 'render-token',
                    'AGIX': 'singularitynet',
                    'SUI': 'sui',
                    'ENA': 'ethena',
                    
                    # Macro indicators
                    'VIX': 'VIXCLS',
                    'DXY': 'DEXCHUS',
                    'TREASURY': 'DGS10',
                    'FED': 'DFF',
                    'SOFR': 'SOFR',
                    'RRP': 'RRPONTSYD',
                    'BAML': 'BAMLH0A0HYM2',
                    'DEXUSEU': 'DEXUSEU',
                    'DTWEXBGS': 'DTWEXBGS'
                }
                
                primary = asset_mapping.get(parts[0].upper(), parts[0].lower())
                secondary = asset_mapping.get(parts[1].upper(), parts[1].lower())
                
                return primary, secondary
        
        # Default parsing - assume it's already in the correct format
        return pair.lower(), pair.lower()
    
    def monitor_pair(self, pair: str = None) -> Dict[str, Any]:
        """
        Monitor a pair for correlation changes and generate alerts if needed.
        
        Args:
            pair: Asset pair name (optional, uses self.pair if not provided)
            
        Returns:
            Dict[str, Any]: Monitoring results
        """
        if pair is None:
            pair = self.pair
        
        # Start performance monitoring
        start_time = time.time()
        monitoring_timestamp = int(datetime.now().timestamp() * 1000)
        
        self.logger.info(f"Starting correlation monitoring for {pair}")
        
        # Initialize result tracking
        result_data = {
            'success': True,
            'reason': None,
            'correlations': {},
            'breakouts': [],
            'alerts_generated': [],
            'partial_failures': []
        }
        
        # Step 1: Fetch and prepare data (with retry logic)
        data = self._fetch_and_prepare_data_with_retry()
        if data.empty:
            result_data['success'] = False
            result_data['reason'] = "no_data"
            return self._create_monitoring_result(
                pair, success=False, reason="no_data", 
                performance_metrics={'total_time': time.time() - start_time}
            )
        
        # Step 2: Calculate correlations for all windows
        correlations = self._calculate_correlations_with_retry(data, monitoring_timestamp)
        if not correlations:
            result_data['partial_failures'].append("correlation_calculation_failed")
            if result_data['reason'] is None:
                result_data['reason'] = "correlation_calculation_failed"
        
        result_data['correlations'] = correlations
        
        # Step 3: Check for breakouts (only if correlations exist)
        if correlations:
            breakouts = self._detect_breakouts_with_retry(correlations)
            result_data['breakouts'] = breakouts
        else:
            breakouts = []
            result_data['partial_failures'].append("breakout_detection_skipped")
        
        # Step 4: Store correlation history (with atomic updates)
        if correlations:
            storage_success = self._store_correlation_history_atomic(correlations, monitoring_timestamp)
            if not storage_success:
                result_data['partial_failures'].append("correlation_storage_failed")
        
        # Step 5: Store breakout history (with atomic updates)
        if breakouts:
            breakout_storage_success = self._store_breakout_history_atomic(breakouts, monitoring_timestamp)
            if not breakout_storage_success:
                result_data['partial_failures'].append("breakout_storage_failed")
        
        # Step 6: Generate alerts if breakouts detected
        alerts_generated = []
        if self.config['alert_on_breakout'] and breakouts:
            alerts_generated = self._generate_alerts_with_retry(breakouts)
            result_data['alerts_generated'] = alerts_generated
        
        # Step 7: Update state atomically (only if we have some data)
        state_update_success = True
        if correlations or breakouts:
            state_update_success = self._update_state_atomic(correlations, breakouts, monitoring_timestamp)
            if not state_update_success:
                result_data['partial_failures'].append("state_update_failed")
        
        # Determine overall success
        if not correlations and not breakouts:
            result_data['success'] = False
            if result_data['reason'] is None:
                result_data['reason'] = "no_valid_data"
        elif result_data['partial_failures']:
            # Partial success - some operations failed but core functionality worked
            result_data['success'] = len(result_data['partial_failures']) < 3  # Success if less than 3 failures
        
        # Calculate performance metrics
        total_time = time.time() - start_time
        performance_metrics = {
            'total_time': total_time,
            'data_fetch_time': getattr(self, '_data_fetch_time', 0),
            'correlation_calculation_time': getattr(self, '_correlation_calculation_time', 0),
            'breakout_detection_time': getattr(self, '_breakout_detection_time', 0),
            'storage_time': getattr(self, '_storage_time', 0),
            'alert_generation_time': getattr(self, '_alert_generation_time', 0)
        }
        
        result = self._create_monitoring_result(
            pair, 
            success=result_data['success'], 
            reason=result_data['reason'],
            correlations=result_data['correlations'],
            breakouts=result_data['breakouts'],
            alerts_generated=result_data['alerts_generated'],
            performance_metrics=performance_metrics
        )
        
        # Log partial failures
        if result_data['partial_failures']:
            self.logger.warning(f"Partial failures in monitoring {pair}: {result_data['partial_failures']}")
        
        self.logger.info(f"Monitoring completed for {pair}: {len(breakouts)} breakouts, {len(alerts_generated)} alerts, {total_time:.2f}s")
        return result
    
    def _fetch_and_prepare_data_with_retry(self) -> pd.DataFrame:
        """
        Fetch and prepare data with retry logic for transient failures.
        
        Returns:
            pd.DataFrame: Prepared data for correlation analysis
        """
        start_time = time.time()
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                # Fetch raw data
                raw_data = self.data_fetcher.get_crypto_data_for_correlation(
                    self.primary_asset, 
                    self.secondary_asset, 
                    self.config['data_lookback_days']
                )
                
                if raw_data.empty:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"No data available, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        self.logger.warning(f"No data available for {self.primary_asset} and {self.secondary_asset} after {max_retries} attempts")
                        return pd.DataFrame()
                
                # Normalize data for correlation analysis
                normalized_data = self.data_normalizer.normalize_for_correlation(
                    self.primary_asset, 
                    self.secondary_asset, 
                    self.config['data_lookback_days']
                )
                
                if normalized_data.empty:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Data normalization failed, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        self.logger.warning("Data normalization failed after all retries")
                        return pd.DataFrame()
                
                self._data_fetch_time = time.time() - start_time
                self.logger.debug(f"Prepared data: {len(normalized_data)} rows in {self._data_fetch_time:.2f}s")
                return normalized_data
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Data fetch attempt {attempt + 1} failed: {e}, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"Data fetch failed after {max_retries} attempts: {e}")
                    return pd.DataFrame()
        
        return pd.DataFrame()
    
    def _calculate_correlations_with_retry(self, data: pd.DataFrame, timestamp: int) -> Dict[str, Any]:
        """
        Calculate correlations with retry logic.
        
        Args:
            data: Prepared data for correlation analysis
            timestamp: Consistent timestamp for this monitoring cycle
            
        Returns:
            Dict[str, Any]: Correlation results for all windows
        """
        start_time = time.time()
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                correlations = {}
                
                for window_days in self.config['correlation_windows']:
                    # Calculate correlation for this window
                    correlation = self.correlation_calculator.calculate_correlation(
                        data, self.primary_asset, self.secondary_asset, window_days
                    )
                    
                    if not np.isnan(correlation):
                        # Calculate statistical significance
                        significance = self.statistical_analyzer.calculate_correlation_significance(
                            correlation, len(data)
                        )
                        
                        # Calculate confidence interval
                        confidence_interval = self.statistical_analyzer.calculate_confidence_interval(
                            correlation, len(data)
                        )
                        
                        correlations[f'{window_days}d'] = {
                            'correlation': float(correlation),
                            'window_days': window_days,
                            'sample_size': len(data),
                            'timestamp': timestamp,  # Use consistent timestamp
                            'p_value': significance.get('p_value', np.nan),
                            'significant': significance.get('significant', False),
                            'confidence_interval_lower': confidence_interval.get('lower', np.nan),
                            'confidence_interval_upper': confidence_interval.get('upper', np.nan)
                        }
                        
                        self.logger.debug(f"{window_days}d correlation: {correlation:.4f} (p={significance.get('p_value', np.nan):.4f})")
                    else:
                        self.logger.warning(f"Failed to calculate correlation for {window_days}d window")
                
                self._correlation_calculation_time = time.time() - start_time
                return correlations
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Correlation calculation attempt {attempt + 1} failed: {e}, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"Correlation calculation failed after {max_retries} attempts: {e}")
                    return {}
        
        return {}
    
    def _detect_breakouts_with_retry(self, correlations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect correlation breakouts with retry logic.
        
        Args:
            correlations: Correlation results for all windows
            
        Returns:
            List[Dict[str, Any]]: List of detected breakouts
        """
        start_time = time.time()
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                breakouts = []
                
                for window_key, correlation_data in correlations.items():
                    window_days = correlation_data['window_days']
                    current_correlation = correlation_data['correlation']
                    
                    # Get historical correlations for this window
                    historical_correlations = self._get_historical_correlations(window_days)
                    
                    if len(historical_correlations) >= self.config['min_data_points']:
                        # Detect breakout
                        breakout_result = self.breakout_detector.detect_breakout_with_analysis(
                            current_correlation, historical_correlations
                        )
                        
                        if breakout_result['breakout_detected']:
                            breakout_result['pair'] = self.pair
                            breakout_result['window_days'] = window_days
                            breakout_result['window_key'] = window_key
                            # Include p_value from correlation data
                            breakout_result['p_value'] = correlation_data.get('p_value', 0.0)
                            breakout_result['confidence_interval_lower'] = correlation_data.get('confidence_interval_lower', np.nan)
                            breakout_result['confidence_interval_upper'] = correlation_data.get('confidence_interval_upper', np.nan)
                            breakouts.append(breakout_result)
                            
                            self.logger.info(f"Breakout detected for {self.pair} ({window_days}d): "
                                            f"z_score={breakout_result['z_score']:.4f}, "
                                            f"severity={breakout_result['severity']}")
                    else:
                        self.logger.debug(f"Insufficient historical data for {window_days}d window: {len(historical_correlations)} < {self.config['min_data_points']}")
                
                self._breakout_detection_time = time.time() - start_time
                return breakouts
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Breakout detection attempt {attempt + 1} failed: {e}, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"Breakout detection failed after {max_retries} attempts: {e}")
                    return []
        
        return []
    
    def _get_historical_correlations(self, window_days: int, limit: int = 100) -> List[float]:
        """
        Get historical correlations for a specific window (optimized).
        
        Args:
            window_days: Correlation window in days
            limit: Maximum number of historical correlations to retrieve
            
        Returns:
            List[float]: List of historical correlation values
        """
        try:
            # Get from storage with optimized query
            history_df = self.storage.get_correlation_history(
                self.pair, 
                window_days=window_days, 
                limit=limit,
                columns=['correlation']  # Only retrieve needed column
            )
            
            if not history_df.empty:
                return history_df['correlation'].tolist()
            
            # Fallback to state if storage is empty
            if self.pair in self.state.get('correlation_history', {}):
                pair_history = self.state['correlation_history'][self.pair]
                return [h['correlation'] for h in pair_history if h.get('window_days') == window_days]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting historical correlations: {e}")
            return []
    
    def _store_correlation_history_atomic(self, correlations: Dict[str, Any], timestamp: int) -> bool:
        """
        Store correlation history with atomic updates.
        
        Args:
            correlations: Correlation results for all windows
            timestamp: Consistent timestamp for this monitoring cycle
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            if not self.config['store_correlation_history']:
                return True
            
            success_count = 0
            total_count = len(correlations)
            
            for window_key, correlation_data in correlations.items():
                success = self.storage.store_correlation_history(
                    pair=self.pair,
                    timestamp=timestamp,  # Use consistent timestamp
                    correlation=correlation_data['correlation'],
                    window_days=correlation_data['window_days'],
                    sample_size=correlation_data['sample_size'],
                    p_value=correlation_data.get('p_value'),
                    confidence_interval_lower=correlation_data.get('confidence_interval_lower'),
                    confidence_interval_upper=correlation_data.get('confidence_interval_upper')
                )
                
                if success:
                    success_count += 1
                    self.logger.debug(f"Stored correlation history for {self.pair} ({window_key})")
                else:
                    self.logger.warning(f"Failed to store correlation history for {self.pair} ({window_key})")
            
            self._storage_time = time.time() - start_time
            success_rate = success_count / total_count if total_count > 0 else 0.0
            
            if success_rate < 1.0:
                self.logger.warning(f"Partial correlation storage success: {success_count}/{total_count} ({success_rate:.1%})")
            
            return success_rate >= 0.5  # Consider successful if at least 50% stored
                    
        except Exception as e:
            self.logger.error(f"Error storing correlation history: {e}")
            return False
    
    def _store_breakout_history_atomic(self, breakouts: List[Dict[str, Any]], timestamp: int) -> bool:
        """
        Store breakout history with atomic updates.
        
        Args:
            breakouts: List of detected breakouts
            timestamp: Consistent timestamp for this monitoring cycle
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.config['store_breakout_history']:
                return True
            
            success_count = 0
            total_count = len(breakouts)
            
            for breakout in breakouts:
                success = self.storage.store_correlation_breakout(
                    pair=self.pair,
                    timestamp=timestamp,  # Use consistent timestamp
                    z_score=breakout['z_score'],
                    severity=breakout['severity'],
                    direction=breakout['direction'],
                    confidence=breakout['confidence'],
                    threshold=breakout['threshold'],
                    current_correlation=breakout['current_correlation'],
                    historical_mean=breakout['historical_mean'],
                    historical_std=breakout['historical_std'],
                    sample_size=breakout['sample_size']
                )
                
                if success:
                    success_count += 1
                    self.logger.debug(f"Stored breakout history for {self.pair}")
                else:
                    self.logger.warning(f"Failed to store breakout history for {self.pair}")
            
            success_rate = success_count / total_count if total_count > 0 else 0.0
            
            if success_rate < 1.0:
                self.logger.warning(f"Partial breakout storage success: {success_count}/{total_count} ({success_rate:.1%})")
            
            return success_rate >= 0.5  # Consider successful if at least 50% stored
                    
        except Exception as e:
            self.logger.error(f"Error storing breakout history: {e}")
            return False
    
    def _generate_alerts_with_retry(self, breakouts: List[Dict[str, Any]]) -> List[str]:
        """
        Generate alerts with retry logic.
        
        Args:
            breakouts: List of detected breakouts
            
        Returns:
            List[str]: List of generated alert file paths
        """
        start_time = time.time()
        
        try:
            alerts_generated = []
            
            for breakout in breakouts:
                # Prepare correlation data for alert
                correlation_data = {
                    'current_correlation': breakout['current_correlation'],
                    'historical_average': breakout['historical_mean'],
                    'z_score': breakout['z_score'],
                    'p_value': breakout.get('p_value', np.nan),
                    'breakout_detected': breakout['breakout_detected'],
                    'direction': breakout['direction'],
                    'severity': breakout['severity'],
                    'duration_minutes': breakout.get('duration_minutes', 0),
                    'correlation_windows': {breakout['window_key']: breakout['current_correlation']},
                    'confidence_interval': {
                        'lower': breakout.get('confidence_interval_lower', np.nan),
                        'upper': breakout.get('confidence_interval_upper', np.nan)
                    },
                    'sample_size': breakout['sample_size']
                }
                
                # Generate breakdown alert
                alert_path = self.alert_system.generate_breakdown_alert(self.pair, correlation_data)
                
                if alert_path:
                    alerts_generated.append(alert_path)
                    self.logger.info(f"Generated breakout alert: {alert_path}")
                    
                    # Send to Discord if integration is enabled
                    if self.discord_integration.discord:
                        self.logger.info(f"Sending correlation breakdown alert to Discord for {self.pair}")
                        discord_success = self.discord_integration.send_correlation_breakdown_alert(self.pair, correlation_data)
                        if discord_success:
                            self.logger.info(f"✅ Correlation breakdown alert sent to Discord for {self.pair}")
                        else:
                            self.logger.warning(f"⚠️ Failed to send correlation breakdown alert to Discord for {self.pair}")
                else:
                    self.logger.warning(f"Failed to generate alert for {self.pair}")
            
            self._alert_generation_time = time.time() - start_time
            return alerts_generated
            
        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
            return []
    
    def _update_state_atomic(self, correlations: Dict[str, Any], breakouts: List[Dict[str, Any]], timestamp: int) -> bool:
        """
        Update correlation state atomically.
        
        Args:
            correlations: Correlation results for all windows
            breakouts: List of detected breakouts
            timestamp: Consistent timestamp for this monitoring cycle
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a copy of current state for atomic update
            new_state = self.state.copy() if self.state else {}
            
            # Update pairs state
            if 'pairs' not in new_state:
                new_state['pairs'] = {}
            
            new_state['pairs'][self.pair] = {
                'last_correlation': correlations.get('30d', {}).get('correlation', 0.0),
                'last_updated': datetime.now().isoformat()
            }
            
            # Update correlation history
            if 'correlation_history' not in new_state:
                new_state['correlation_history'] = {}
            
            if self.pair not in new_state['correlation_history']:
                new_state['correlation_history'][self.pair] = []
            
            # Add current correlations to history
            for window_key, correlation_data in correlations.items():
                new_state['correlation_history'][self.pair].append({
                    'correlation': correlation_data['correlation'],
                    'timestamp': timestamp,  # Use consistent timestamp
                    'window_days': correlation_data['window_days']
                })
            
            # Update breakout history
            if 'breakout_history' not in new_state:
                new_state['breakout_history'] = {}
            
            if self.pair not in new_state['breakout_history']:
                new_state['breakout_history'][self.pair] = []
            
            # Add current breakouts to history
            for breakout in breakouts:
                new_state['breakout_history'][self.pair].append({
                    'z_score': breakout['z_score'],
                    'severity': breakout['severity'],
                    'timestamp': timestamp  # Use consistent timestamp
                })
            
            # Update settings
            if 'settings' not in new_state:
                new_state['settings'] = {}
            
            new_state['settings']['last_analysis_time'] = datetime.now().isoformat()
            new_state['settings']['total_pairs_analyzed'] = len(new_state['pairs'])
            new_state['settings']['total_breakouts_detected'] = sum(
                len(breakouts) for breakouts in new_state['breakout_history'].values()
            )
            
            # Atomic state update - only update if save succeeds
            if self.state_manager.save_correlation_state(new_state):
                self.state = new_state
                return True
            else:
                self.logger.error("Failed to save state, keeping existing state")
                return False
            
        except Exception as e:
            self.logger.error(f"Error updating state: {e}")
            return False
    
    def _create_monitoring_result(self, pair: str, success: bool, reason: str = None,
                                correlations: Dict[str, Any] = None,
                                breakouts: List[Dict[str, Any]] = None,
                                alerts_generated: List[str] = None,
                                performance_metrics: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Create monitoring result dictionary with performance metrics.
        
        Args:
            pair: Asset pair name
            success: Whether monitoring was successful
            reason: Reason for failure (if any)
            correlations: Correlation results
            breakouts: Detected breakouts
            alerts_generated: Generated alerts
            performance_metrics: Performance timing metrics
            
        Returns:
            Dict[str, Any]: Monitoring result
        """
        result = {
            'pair': pair,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'success': success,
            'reason': reason,
            'correlations': correlations or {},
            'breakouts': breakouts or [],
            'alerts_generated': alerts_generated or [],
            'monitoring_config': self.config
        }
        
        # Add performance metrics if available
        if performance_metrics:
            result['performance_metrics'] = performance_metrics
            
            # Log performance if monitoring is enabled
            if self.config.get('enable_performance_monitoring', True):
                total_time = performance_metrics.get('total_time', 0)
                if total_time > 30:  # Log warning if monitoring takes too long
                    self.logger.warning(f"Slow monitoring performance: {total_time:.2f}s for {pair}")
                else:
                    self.logger.debug(f"Monitoring performance: {total_time:.2f}s for {pair}")
        
        return result
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status.
        
        Returns:
            Dict[str, Any]: Monitoring status
        """
        try:
            # Get latest correlation
            latest_correlation = self.storage.get_latest_correlation(self.pair)
            
            # Get recent breakouts
            recent_breakouts = self.storage.get_correlation_breakouts(
                self.pair, limit=5
            )
            
            # Get correlation statistics
            stats = self.storage.get_correlation_statistics(self.pair)
            
            return {
                'pair': self.pair,
                'primary_asset': self.primary_asset,
                'secondary_asset': self.secondary_asset,
                'latest_correlation': latest_correlation,
                'recent_breakouts': recent_breakouts.to_dict('records') if not recent_breakouts.empty else [],
                'correlation_statistics': stats,
                'monitoring_config': self.config,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting monitoring status: {e}")
            return {}

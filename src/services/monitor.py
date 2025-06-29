"""
Health monitoring service for data freshness checks.

This module provides functionality to monitor the health of collected data
and detect when data becomes stale or outdated.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.data.storage import CSVStorage
from config.macro_settings import MACRO_INDICATORS


logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Health checker for monitoring data freshness and system status.
    
    Provides methods to check if collected data is fresh and within
    expected timeframes for reliable operation.
    """
    
    def __init__(self, 
                 storage: Optional[CSVStorage] = None,
                 freshness_threshold_hours: int = 2):
        """
        Initialize the health checker.
        
        Args:
            storage: CSV storage instance for data access
            freshness_threshold_hours: Hours after which data is considered stale (default: 2)
        """
        self.storage = storage or CSVStorage()
        self.freshness_threshold_hours = freshness_threshold_hours
        self.logger = logging.getLogger(__name__)
    
    def is_data_fresh(self, crypto_id: str) -> bool:
        """
        Check if data for a cryptocurrency is fresh (within expected timeframe).
        
        Args:
            crypto_id: Cryptocurrency identifier (e.g., "bitcoin")
            
        Returns:
            bool: True if data is fresh, False if stale or missing
        """
        status = self.get_data_freshness_status(crypto_id)
        return status['is_fresh']
    
    def get_data_freshness_status(self, crypto_id: str) -> Dict[str, Any]:
        """
        Get detailed data freshness status for a cryptocurrency.
        
        Args:
            crypto_id: Cryptocurrency identifier (e.g., "bitcoin")
            
        Returns:
            Dict with freshness status, latest timestamp, age, and details
        """
        self.logger.debug(f"Checking data freshness for {crypto_id}")
        
        try:
            # Load latest data for the crypto
            ohlcv_data = self.storage.load_ohlcv_data(crypto_id)
            
            if not ohlcv_data:
                return {
                    'crypto_id': crypto_id,
                    'is_fresh': False,
                    'status': 'no_data',
                    'message': f'No data found for {crypto_id}',
                    'latest_timestamp': None,
                    'latest_datetime': None,
                    'age_hours': None,
                    'threshold_hours': self.freshness_threshold_hours,
                    'checked_at': datetime.now().isoformat()
                }
            
            # Find the most recent data point
            latest_data = max(ohlcv_data, key=lambda x: x.timestamp)
            latest_datetime = latest_data.to_datetime()
            current_time = datetime.now()
            
            # Calculate age of the latest data
            age_delta = current_time - latest_datetime
            age_hours = age_delta.total_seconds() / 3600
            
            # Determine if data is fresh
            is_fresh = age_hours <= self.freshness_threshold_hours
            
            status = 'fresh' if is_fresh else 'stale'
            message = (f"Latest data for {crypto_id} is {age_hours:.2f} hours old "
                      f"(threshold: {self.freshness_threshold_hours} hours)")
            
            return {
                'crypto_id': crypto_id,
                'is_fresh': is_fresh,
                'status': status,
                'message': message,
                'latest_timestamp': latest_data.timestamp,
                'latest_datetime': latest_datetime.isoformat(),
                'age_hours': round(age_hours, 2),
                'threshold_hours': self.freshness_threshold_hours,
                'record_count': len(ohlcv_data),
                'checked_at': current_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness for {crypto_id}: {e}")
            return {
                'crypto_id': crypto_id,
                'is_fresh': False,
                'status': 'error',
                'message': f'Error checking data for {crypto_id}: {str(e)}',
                'latest_timestamp': None,
                'latest_datetime': None,
                'age_hours': None,
                'threshold_hours': self.freshness_threshold_hours,
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    def check_all_cryptos_freshness(self, crypto_ids: Optional[list] = None) -> Dict[str, Any]:
        """
        Check data freshness for multiple cryptocurrencies.
        
        Args:
            crypto_ids: List of crypto IDs to check, defaults to top 3
            
        Returns:
            Dict with overall status and individual crypto results
        """
        if crypto_ids is None:
            crypto_ids = ['bitcoin', 'ethereum', 'tether']  # Default top 3
        
        self.logger.info(f"Checking data freshness for {len(crypto_ids)} cryptocurrencies")
        
        results = {}
        fresh_count = 0
        total_count = len(crypto_ids)
        
        for crypto_id in crypto_ids:
            status = self.get_data_freshness_status(crypto_id)
            results[crypto_id] = status
            
            if status['is_fresh']:
                fresh_count += 1
        
        # Determine overall health
        overall_fresh = fresh_count == total_count
        health_status = 'healthy' if overall_fresh else 'degraded' if fresh_count > 0 else 'unhealthy'
        
        return {
            'overall_status': health_status,
            'is_healthy': overall_fresh,
            'fresh_count': fresh_count,
            'total_count': total_count,
            'freshness_percentage': round((fresh_count / total_count) * 100, 1) if total_count > 0 else 0,
            'threshold_hours': self.freshness_threshold_hours,
            'cryptos': results,
            'checked_at': datetime.now().isoformat()
        }
    
    def get_macro_data_freshness_status(self, indicator_key: str) -> Dict[str, Any]:
        """
        Get detailed data freshness status for a macro indicator.
        
        Args:
            indicator_key: Macro indicator key (e.g., "VIX")
            
        Returns:
            Dict with freshness status, latest date, age, and details
        """
        self.logger.debug(f"Checking macro data freshness for {indicator_key}")
        
        try:
            if indicator_key not in MACRO_INDICATORS:
                return {
                    'indicator': indicator_key,
                    'is_fresh': False,
                    'status': 'invalid',
                    'message': f'Unknown indicator: {indicator_key}',
                    'latest_date': None,
                    'age_hours': None,
                    'threshold_hours': self.freshness_threshold_hours,
                    'checked_at': datetime.now().isoformat()
                }
            
            # Load latest macro data
            indicator_config = MACRO_INDICATORS[indicator_key]
            series_id = indicator_config['fred_series_id']
            macro_data = self.storage.load_macro_indicator_data(indicator_key, series_id)
            
            if not macro_data:
                return {
                    'indicator': indicator_key,
                    'is_fresh': False,
                    'status': 'no_data',
                    'message': f'No data found for {indicator_key}',
                    'latest_date': None,
                    'age_hours': None,
                    'threshold_hours': self.freshness_threshold_hours,
                    'checked_at': datetime.now().isoformat()
                }
            
            # Find the most recent data point
            latest_record = max(macro_data, key=lambda x: x.date)
            latest_date = latest_record.date
            current_time = datetime.now()
            
            # Calculate age of the latest data
            age_delta = current_time - latest_date
            age_hours = age_delta.total_seconds() / 3600
            
            # For macro data, use a longer threshold (24 hours) since it's typically daily
            macro_threshold = 24  # hours
            is_fresh = age_hours <= macro_threshold
            
            status = 'fresh' if is_fresh else 'stale'
            message = (f"Latest data for {indicator_key} is {age_hours:.2f} hours old "
                      f"(threshold: {macro_threshold} hours)")
            
            return {
                'indicator': indicator_key,
                'is_fresh': is_fresh,
                'status': status,
                'message': message,
                'latest_date': latest_date.strftime('%Y-%m-%d'),
                'age_hours': round(age_hours, 2),
                'threshold_hours': macro_threshold,
                'record_count': len(macro_data),
                'series_id': series_id,
                'checked_at': current_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking macro data freshness for {indicator_key}: {e}")
            return {
                'indicator': indicator_key,
                'is_fresh': False,
                'status': 'error',
                'message': f'Error checking data for {indicator_key}: {str(e)}',
                'latest_date': None,
                'age_hours': None,
                'threshold_hours': 24,
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    def check_all_macro_freshness(self) -> Dict[str, Any]:
        """
        Check data freshness for all macro indicators.
        
        Returns:
            Dict with overall macro status and individual indicator results
        """
        indicator_keys = list(MACRO_INDICATORS.keys())
        self.logger.info(f"Checking macro data freshness for {len(indicator_keys)} indicators")
        
        results = {}
        fresh_count = 0
        total_count = len(indicator_keys)
        
        for indicator_key in indicator_keys:
            status = self.get_macro_data_freshness_status(indicator_key)
            results[indicator_key] = status
            
            if status['is_fresh']:
                fresh_count += 1
        
        # Determine overall macro health
        overall_fresh = fresh_count == total_count
        health_status = 'healthy' if overall_fresh else 'degraded' if fresh_count > 0 else 'unhealthy'
        
        return {
            'overall_status': health_status,
            'is_healthy': overall_fresh,
            'fresh_count': fresh_count,
            'total_count': total_count,
            'freshness_percentage': round((fresh_count / total_count) * 100, 1) if total_count > 0 else 0,
            'indicators': results,
            'checked_at': datetime.now().isoformat()
        }
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status including data freshness.
        
        Returns:
            Dict with system health information
        """
        self.logger.info("Performing comprehensive system health check")
        
        # Check data freshness for top cryptos
        crypto_freshness_status = self.check_all_cryptos_freshness()
        
        # Check data freshness for macro indicators
        macro_freshness_status = self.check_all_macro_freshness()
        
        # Overall system health is based on both crypto and macro data freshness
        crypto_healthy = crypto_freshness_status['is_healthy']
        macro_healthy = macro_freshness_status['is_healthy']
        system_healthy = crypto_healthy and macro_healthy
        
        # Determine overall status
        if system_healthy:
            status = 'healthy'
            message = 'All components healthy'
        elif crypto_healthy or macro_healthy:
            status = 'degraded'
            message = 'Some components unhealthy'
        else:
            status = 'unhealthy'
            message = 'Multiple components unhealthy'
        
        return {
            'status': status,
            'healthy': system_healthy,
            'components': {
                'crypto_data': crypto_freshness_status,
                'macro_data': macro_freshness_status
            },
            'message': message,
            'checked_at': datetime.now().isoformat()
        } 
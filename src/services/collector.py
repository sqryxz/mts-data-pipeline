"""Data collection service with enhanced error recovery."""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.api.coingecko_client import CoinGeckoClient
from src.data.models import Cryptocurrency, OHLCVData
from src.data.validator import DataValidator
from src.data.storage import CSVStorage
from src.utils.exceptions import (
    APIError, APIRateLimitError, APIConnectionError, APITimeoutError,
    DataValidationError, StorageError
)


logger = logging.getLogger(__name__)


class DataCollector:
    """
    Service for collecting cryptocurrency data with enhanced error recovery.
    
    Provides methods to fetch market data and OHLCV data for cryptocurrencies,
    with comprehensive error handling and recovery mechanisms.
    """
    
    def __init__(self, 
                 api_client: Optional[CoinGeckoClient] = None,
                 validator: Optional[DataValidator] = None,
                 storage: Optional[CSVStorage] = None):
        """
        Initialize the data collector with dependencies.
        
        Args:
            api_client: CoinGecko API client instance
            validator: Data validator instance  
            storage: CSV storage instance
        """
        self.api_client = api_client or CoinGeckoClient()
        self.validator = validator or DataValidator()
        self.storage = storage or CSVStorage()

    def _log_structured_metrics(self, event_type: str, data: Dict[str, Any]):
        """
        Log structured metrics in a consistent, parseable format.
        
        Args:
            event_type: Type of event (e.g., 'collection_start', 'collection_complete')
            data: Metrics data to log
        """
        metrics = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **data
        }
        logger.info(f"METRICS: {json.dumps(metrics, separators=(',', ':'))}")

    def get_top_cryptocurrencies(self, limit: int = 3) -> List[Cryptocurrency]:
        """
        Get top cryptocurrencies by market cap with error recovery.
        
        Args:
            limit: Number of top cryptocurrencies to fetch (default: 3)
            
        Returns:
            List[Cryptocurrency]: List of cryptocurrency objects
            
        Raises:
            Exception: If API request fails or data is invalid
        """
        logger.info(f"Fetching top {limit} cryptocurrencies by market cap")
        
        try:
            # Get market data from API
            market_data = self.api_client.get_top_cryptos(limit)
            
            if not market_data:
                logger.warning("No market data received from API")
                return []
            
            # Convert to Cryptocurrency objects
            cryptocurrencies = []
            for crypto_data in market_data:
                try:
                    # Validate the cryptocurrency data
                    if not self.validator.validate_cryptocurrency_data(crypto_data):
                        logger.warning(f"Invalid cryptocurrency data: {crypto_data}")
                        continue
                    
                    # Create Cryptocurrency object
                    crypto = Cryptocurrency(
                        id=crypto_data['id'],
                        symbol=crypto_data['symbol'],
                        name=crypto_data['name'],
                        market_cap_rank=crypto_data.get('market_cap_rank')
                    )
                    cryptocurrencies.append(crypto)
                    
                except Exception as e:
                    logger.error(f"Error processing cryptocurrency data {crypto_data}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(cryptocurrencies)} cryptocurrencies")
            return cryptocurrencies
            
        except Exception as e:
            logger.error(f"Failed to get top cryptocurrencies: {e}")
            raise

    def _categorize_collection_error(self, error: Exception, crypto_id: str) -> Dict[str, Any]:
        """
        Categorize collection errors for better reporting and handling.
        
        Args:
            error: Exception that occurred
            crypto_id: ID of the cryptocurrency being processed
            
        Returns:
            Dict with error category, message, and metadata
        """
        error_info = {
            'crypto_id': crypto_id,
            'error_message': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.now().isoformat(),
            'category': 'unknown',
            'recoverable': False,
            'retry_recommended': False
        }
        
        # Categorize API errors
        if isinstance(error, APIRateLimitError):
            error_info.update({
                'category': 'rate_limit',
                'recoverable': True,
                'retry_recommended': True,
                'retry_after': getattr(error, 'retry_after', None)
            })
        elif isinstance(error, (APIConnectionError, APITimeoutError)):
            error_info.update({
                'category': 'network',
                'recoverable': True,
                'retry_recommended': True
            })
        elif isinstance(error, APIError):
            # Check status code for categorization
            status_code = getattr(error, 'status_code', None)
            if status_code:
                if status_code in (404, 400):
                    error_info.update({
                        'category': 'client_error',
                        'recoverable': False,
                        'retry_recommended': False
                    })
                elif status_code >= 500:
                    error_info.update({
                        'category': 'server_error',
                        'recoverable': True,
                        'retry_recommended': True
                    })
                else:
                    error_info.update({
                        'category': 'api_error',
                        'recoverable': False,
                        'retry_recommended': False
                    })
        elif isinstance(error, DataValidationError):
            error_info.update({
                'category': 'validation',
                'recoverable': False,
                'retry_recommended': False
            })
        elif isinstance(error, StorageError):
            error_info.update({
                'category': 'storage',
                'recoverable': True,
                'retry_recommended': True
            })
        else:
            error_info.update({
                'category': 'unexpected',
                'recoverable': False,
                'retry_recommended': False
            })
        
        return error_info

    def collect_crypto_data(self, crypto_id: str, days: int = 1) -> Dict[str, Any]:
        """
        Collect and store OHLCV data for a specific cryptocurrency.
        
        Args:
            crypto_id: Cryptocurrency identifier (e.g., "bitcoin")
            days: Number of days of data to collect (default: 1)
            
        Returns:
            Dict with collection results including success status and record count
            
        Raises:
            Exception: If data collection fails
        """
        start_time = datetime.now()
        logger.info(f"Collecting OHLCV data for {crypto_id} ({days} days)")
        
        collection_result = {
            'crypto_id': crypto_id,
            'success': False,
            'records_collected': 0,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_seconds': None,
            'error': None
        }
        
        try:
            # Get OHLC data from API
            ohlc_data = self.api_client.get_ohlc_data(crypto_id, days)
            
            if not ohlc_data:
                logger.warning(f"No OHLC data received for {crypto_id}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                return collection_result
            
            # Validate raw OHLC data structure
            if not self.validator.validate_ohlcv_data(ohlc_data):
                logger.error(f"Invalid OHLC data structure for {crypto_id}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                collection_result['error'] = "Invalid OHLC data structure"
                return collection_result
            
            # Convert to OHLCVData objects
            ohlcv_objects = []
            for ohlc_entry in ohlc_data:
                try:
                    # Extract values from API response [timestamp, open, high, low, close]
                    timestamp = int(ohlc_entry[0])
                    open_price = float(ohlc_entry[1])
                    high = float(ohlc_entry[2])
                    low = float(ohlc_entry[3])
                    close = float(ohlc_entry[4])
                    # Note: CoinGecko OHLC endpoint doesn't provide volume, so we'll use 0
                    volume = 0.0
                    
                    # Create OHLCVData object (this will validate the data)
                    ohlcv = OHLCVData(
                        timestamp=timestamp,
                        open=open_price,
                        high=high,
                        low=low,
                        close=close,
                        volume=volume
                    )
                    ohlcv_objects.append(ohlcv)
                    
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Skipping invalid OHLC entry for {crypto_id}: {ohlc_entry}, error: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to process OHLC entry for {crypto_id}: {ohlc_entry}, error: {e}")
                    continue
            
            if not ohlcv_objects:
                logger.warning(f"No valid OHLCV data processed for {crypto_id}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                collection_result['error'] = "No valid OHLCV data processed"
                return collection_result
            
            # Store the data
            self.storage.save_ohlcv_data(crypto_id, ohlcv_objects)
            
            # Update successful result
            end_time = datetime.now()
            collection_result.update({
                'success': True,
                'records_collected': len(ohlcv_objects),
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            })
            
            # Log structured metrics for individual crypto collection
            self._log_structured_metrics('crypto_collection_complete', {
                'crypto_id': crypto_id,
                'success': True,
                'records_collected': len(ohlcv_objects),
                'duration_seconds': collection_result['duration_seconds'],
                'days_requested': days
            })
            
            logger.info(f"Successfully collected and stored {len(ohlcv_objects)} OHLCV records for {crypto_id}")
            return collection_result
            
        except Exception as e:
            end_time = datetime.now()
            collection_result.update({
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds(),
                'error': str(e)
            })
            
            # Log structured metrics for failed collection
            self._log_structured_metrics('crypto_collection_failed', {
                'crypto_id': crypto_id,
                'success': False,
                'error': str(e),
                'duration_seconds': collection_result['duration_seconds'],
                'days_requested': days
            })
            
            logger.error(f"Failed to collect data for {crypto_id}: {e}")
            raise

    def collect_all_data(self, days: int = 1, max_retries_per_crypto: int = 1) -> Dict[str, Any]:
        """
        Collect OHLCV data for all top 3 cryptocurrencies with enhanced error recovery.
        
        Args:
            days: Number of days of data to collect for each crypto (default: 1)
            max_retries_per_crypto: Maximum retries per crypto before giving up (default: 1)
            
        Returns:
            Dict: Collection results with success/failure counts, error details, and recovery metrics
        """
        start_time = datetime.now()
        logger.info(f"Starting batch collection for top 3 cryptocurrencies ({days} days each)")
        
        # Log structured metrics for collection start
        self._log_structured_metrics('batch_collection_start', {
            'days_requested': days,
            'max_retries_per_crypto': max_retries_per_crypto,
            'target_crypto_count': 3
        })
        
        # Initialize enhanced results tracking
        results = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'retries_used': 0,
            'total_records_collected': 0,
            'details': [],
            'successful_cryptos': [],
            'failed_cryptos': [],
            'error_categories': {},
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_seconds': None
        }
        
        try:
            # Get top 3 cryptocurrencies
            top_cryptos = self.get_top_cryptocurrencies(limit=3)
            
            if not top_cryptos:
                logger.warning("No cryptocurrencies found for batch collection")
                results['end_time'] = datetime.now().isoformat()
                results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                return results
            
            results['total_attempted'] = len(top_cryptos)
            logger.info(f"Found {len(top_cryptos)} cryptocurrencies to collect: {[crypto.id for crypto in top_cryptos]}")
            
            # Collect data for each cryptocurrency with retry logic
            for crypto in top_cryptos:
                crypto_start_time = datetime.now()
                crypto_result = {
                    'crypto_id': crypto.id,
                    'crypto_name': crypto.name,
                    'crypto_symbol': crypto.symbol,
                    'success': False,
                    'error': None,
                    'error_details': None,
                    'attempts': 0,
                    'duration_seconds': None
                }
                
                # Retry loop for individual crypto
                for attempt in range(max_retries_per_crypto + 1):
                    crypto_result['attempts'] = attempt + 1
                    
                    try:
                        logger.info(f"Collecting data for {crypto.name} ({crypto.id}) - attempt {attempt + 1}")
                        
                        # Attempt to collect data for this crypto
                        collection_result = self.collect_crypto_data(crypto.id, days)
                        
                        if collection_result['success']:
                            crypto_result['success'] = True
                            crypto_result['duration_seconds'] = collection_result['duration_seconds']
                            crypto_result['records_collected'] = collection_result['records_collected']
                            results['successful'] += 1
                            results['successful_cryptos'].append(crypto.id)
                            results['total_records_collected'] += collection_result['records_collected']
                            logger.info(f"Successfully collected data for {crypto.name}")
                            break  # Success, exit retry loop
                        else:
                            # Collection returned error result
                            error_msg = collection_result.get('error', 'Collection failed')
                            if attempt < max_retries_per_crypto:
                                logger.warning(f"Attempt {attempt + 1} failed for {crypto.name}: {error_msg}, retrying...")
                                results['retries_used'] += 1
                                continue
                            else:
                                crypto_result['error'] = error_msg
                                crypto_result['error_details'] = {
                                    'category': 'data_unavailable',
                                    'recoverable': True,
                                    'retry_recommended': True
                                }
                    
                    except Exception as e:
                        # Handle individual crypto failure
                        error_details = self._categorize_collection_error(e, crypto.id)
                        
                        if attempt < max_retries_per_crypto and error_details.get('retry_recommended', False):
                            logger.warning(f"Attempt {attempt + 1} failed for {crypto.name}: {e}, retrying...")
                            results['retries_used'] += 1
                            continue
                        else:
                            crypto_result['error'] = str(e)
                            crypto_result['error_details'] = error_details
                            logger.error(f"Failed to collect data for {crypto.name} ({crypto.id}) after {attempt + 1} attempts: {e}")
                            break  # Max retries reached or non-recoverable error
                
                # Update results based on final outcome
                if not crypto_result['success']:
                    crypto_result['duration_seconds'] = (datetime.now() - crypto_start_time).total_seconds()
                    results['failed'] += 1
                    results['failed_cryptos'].append(crypto.id)
                    
                    # Track error categories for reporting
                    if crypto_result['error_details']:
                        category = crypto_result['error_details'].get('category', 'unknown')
                        results['error_categories'][category] = results['error_categories'].get(category, 0) + 1
                
                results['details'].append(crypto_result)
            
            # Calculate final timing
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = (end_time - start_time).total_seconds()
            
            # Log structured metrics for batch collection completion
            self._log_structured_metrics('batch_collection_complete', {
                'total_attempted': results['total_attempted'],
                'successful': results['successful'],
                'failed': results['failed'],
                'total_records_collected': results['total_records_collected'],
                'retries_used': results['retries_used'],
                'duration_seconds': results['duration_seconds'],
                'successful_cryptos': results['successful_cryptos'],
                'failed_cryptos': results['failed_cryptos'],
                'error_categories': results['error_categories']
            })
            
            # Log comprehensive summary
            logger.info(f"Batch collection completed in {results['duration_seconds']:.2f}s: "
                       f"{results['successful']}/{results['total_attempted']} successful, "
                       f"{results['total_records_collected']} total records collected")
            
            if results['retries_used'] > 0:
                logger.info(f"Used {results['retries_used']} retries during collection")
            
            if results['successful_cryptos']:
                logger.info(f"Successfully collected: {', '.join(results['successful_cryptos'])}")
            
            if results['failed_cryptos']:
                logger.warning(f"Failed to collect: {', '.join(results['failed_cryptos'])}")
            
            if results['error_categories']:
                logger.warning(f"Error categories: {results['error_categories']}")
            
            return results
            
        except Exception as e:
            # Handle failure to get top cryptocurrencies
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = (end_time - start_time).total_seconds()
            
            # Log structured metrics for batch collection failure
            self._log_structured_metrics('batch_collection_failed', {
                'total_attempted': results['total_attempted'],
                'successful': results['successful'],
                'failed': results['failed'],
                'total_records_collected': results['total_records_collected'],
                'duration_seconds': results['duration_seconds'],
                'error': str(e),
                'error_stage': 'initialization'
            })
            
            logger.error(f"Failed to get top cryptocurrencies for batch collection: {e}")
            results['details'].append({
                'error': f"Failed to get top cryptocurrencies: {e}",
                'error_details': self._categorize_collection_error(e, 'batch_initialization')
            })
            return results 
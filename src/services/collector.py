"""Data collection service with enhanced error recovery."""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.api.coingecko_client import CoinGeckoClient
from src.data.models import Cryptocurrency, OHLCVData
from src.data.validator import DataValidator
from src.data.sqlite_helper import CryptoDatabase
from src.utils.exceptions import (
    APIError, APIRateLimitError, APIConnectionError, APITimeoutError,
    DataValidationError, StorageError
)
import collections
import numpy as np
import time
import sqlite3


logger = logging.getLogger(__name__)


class RollingVolatilityCalculator:
    def __init__(self, window_size=15):
        self.window_size = window_size
        self.prices = collections.deque(maxlen=window_size)
        self.last_vol = None

    def update(self, price):
        self.prices.append(price)
        if len(self.prices) == self.window_size:
            log_returns = np.log(np.array(self.prices)[1:] / np.array(self.prices)[:-1])
            self.last_vol = np.std(log_returns) * np.sqrt(self.window_size)
        else:
            self.last_vol = None
        return self.last_vol

    def get_volatility(self):
        return self.last_vol

# --- Example integration in your real-time collector ---
# In your real-time price handler for BTCUSDT and ETHUSDT:
#
# btc_vol_calc = RollingVolatilityCalculator(window_size=15)
# eth_vol_calc = RollingVolatilityCalculator(window_size=15)
#
# # On each new 1-minute price:
# btc_vol = btc_vol_calc.update(new_btc_price)
# if btc_vol is not None:
#     # Store in DB
#     conn = sqlite3.connect('data/crypto_data.db')
#     c = conn.cursor()
#     ts = int(time.time())
#     c.execute('''
#         INSERT INTO crypto_volatility (symbol, timestamp, window_minutes, volatility)
#         VALUES (?, ?, ?, ?)
#     ''', ('BTCUSDT', ts, 15, btc_vol))
#     conn.commit()
#     conn.close()
#
# # Repeat for ETHUSDT


class DataCollector:
    """
    Service for collecting cryptocurrency data with enhanced error recovery.
    
    Provides methods to fetch market data and OHLCV data for cryptocurrencies,
    with comprehensive error handling and recovery mechanisms.
    """
    
    def __init__(self, 
                 api_client: Optional[CoinGeckoClient] = None,
                 validator: Optional[DataValidator] = None,
                 database: Optional[CryptoDatabase] = None):
        """
        Initialize the data collector with dependencies.
        
        Args:
            api_client: CoinGecko API client instance
            validator: Data validator instance  
            database: SQLite database instance
        """
        self.api_client = api_client or CoinGeckoClient()
        self.validator = validator or DataValidator()
        self.database = database or CryptoDatabase()

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
        Fetch the top cryptocurrencies by market capitalization.
        
        Args:
            limit: Number of cryptocurrencies to fetch (default: 3)
            
        Returns:
            List of Cryptocurrency objects
            
        Raises:
            APIError: If the API request fails
            DataValidationError: If the response data is invalid
        """
        try:
            logger.info(f"Fetching top {limit} cryptocurrencies by market cap")
            
            # Fetch market data from CoinGecko
            market_data = self.api_client.get_top_cryptos(limit)
            
            if not market_data:
                raise APIError("No market data received from CoinGecko API")
            
            # Validate the response structure
            if not isinstance(market_data, list):
                raise DataValidationError("Expected list of cryptocurrencies, got: " + str(type(market_data)))
            
            # Convert to Cryptocurrency objects
            cryptocurrencies = []
            for crypto_data in market_data:
                try:
                    crypto = Cryptocurrency(
                        id=crypto_data['id'],
                        name=crypto_data['name'],
                        symbol=crypto_data['symbol'],
                        market_cap_rank=crypto_data['market_cap_rank']
                    )
                    cryptocurrencies.append(crypto)
                except KeyError as e:
                    logger.warning(f"Missing field in cryptocurrency data: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing cryptocurrency {crypto_data.get('id', 'unknown')}: {e}")
                    continue
            
            if not cryptocurrencies:
                raise DataValidationError("No valid cryptocurrencies found in API response")
            
            logger.info(f"Successfully fetched {len(cryptocurrencies)} cryptocurrencies")
            return cryptocurrencies
            
        except (APIError, DataValidationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching cryptocurrencies: {e}")
            raise APIError(f"Failed to fetch cryptocurrencies: {e}")

    def _validate_ohlcv_data(self, ohlcv_data: List[OHLCVData]) -> List[OHLCVData]:
        """
        Validate OHLCV data for consistency and completeness.
        
        Args:
            ohlcv_data: List of OHLCV data objects
            
        Returns:
            List of validated OHLCV data objects
        """
        try:
            validated_data = []
            
            for data in ohlcv_data:
                # Validate the data using the validator
                if self.validator.validate_ohlcv_data(data):
                    validated_data.append(data)
                else:
                    logger.warning(f"Invalid OHLCV data: {data}")
            
            logger.info(f"Validated {len(validated_data)} out of {len(ohlcv_data)} OHLCV records")
            return validated_data
            
        except Exception as e:
            logger.error(f"Error validating OHLCV data: {e}")
            raise DataValidationError(f"OHLCV data validation failed: {e}")

    def _convert_ohlcv_to_database_format(self, ohlcv_data: List[OHLCVData], crypto_id: str) -> List[Dict[str, Any]]:
        """
        Convert OHLCV data objects to database format.
        
        Args:
            ohlcv_data: List of OHLCV data objects
            crypto_id: Cryptocurrency identifier
            
        Returns:
            List of dictionaries ready for database insertion
        """
        db_records = []
        
        for data in ohlcv_data:
            # Convert timestamp to date string for database
            date_str = data.to_datetime().strftime('%Y-%m-%d')
            
            record = {
                'cryptocurrency': crypto_id,  # Fixed: was 'crypto_id' 
                'timestamp': data.timestamp,
                'date_str': date_str,        # Added: required field
                'open': data.open,
                'high': data.high,
                'low': data.low,
                'close': data.close,
                'volume': data.volume
            }
            db_records.append(record)
        
        return db_records

    def _convert_market_chart_to_ohlcv(self, prices: List[List], volumes: List[List], crypto_id: str) -> List[OHLCVData]:
        """
        Convert market chart data (prices and volumes) to OHLCV format.
        
        Args:
            prices: List of [timestamp, price] pairs
            volumes: List of [timestamp, volume] pairs
            crypto_id: Cryptocurrency identifier for logging
            
        Returns:
            List of OHLCVData objects
        """
        ohlcv_objects = []
        
        # Create a dict of volumes by timestamp for quick lookup
        volume_dict = {int(vol[0]): float(vol[1]) for vol in volumes if len(vol) >= 2}
        
        for price_entry in prices:
            try:
                if len(price_entry) < 2:
                    continue
                    
                timestamp = int(price_entry[0])
                price = float(price_entry[1])
                
                # Get corresponding volume or default to 0
                volume = volume_dict.get(timestamp, 0.0)
                
                # For market chart data, we treat each price point as a candle
                # where open = high = low = close = price
                ohlcv = OHLCVData(
                    timestamp=timestamp,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=volume
                )
                ohlcv_objects.append(ohlcv)
                
            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"Skipping invalid price entry for {crypto_id}: {price_entry}, error: {e}")
                continue
            except Exception as e:
                logger.warning(f"Failed to process price entry for {crypto_id}: {price_entry}, error: {e}")
                continue
        
        logger.info(f"Converted {len(ohlcv_objects)} price points to OHLCV format for {crypto_id}")
        return ohlcv_objects

    def _categorize_error(self, error: Exception) -> str:
        """
        Categorize errors for better metrics and recovery strategies.
        
        Args:
            error: Exception that occurred
            
        Returns:
            String category of the error
        """
        if isinstance(error, APIRateLimitError):
            return "rate_limit"
        elif isinstance(error, APITimeoutError):
            return "timeout"
        elif isinstance(error, APIConnectionError):
            return "connection"
        elif isinstance(error, DataValidationError):
            return "validation"
        elif isinstance(error, StorageError):
            return "storage"
        else:
            return "unknown"

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
            # Get market chart data from API (includes volume)
            market_data = self.api_client.get_market_chart_data(crypto_id, days)
            
            if not market_data:
                logger.warning(f"No market data received for {crypto_id}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                return collection_result
            
            # Extract price and volume data
            prices = market_data.get('prices', [])
            volumes = market_data.get('total_volumes', [])
            
            if not prices:
                logger.warning(f"No price data received for {crypto_id}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                collection_result['error'] = "No price data received"
                return collection_result
            
            # Convert market chart data to OHLCV format
            ohlcv_objects = self._convert_market_chart_to_ohlcv(prices, volumes, crypto_id)
            
            if not ohlcv_objects:
                logger.warning(f"No valid OHLCV data processed for {crypto_id}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                collection_result['error'] = "No valid OHLCV data processed"
                return collection_result
            
            # Check for incremental collection - filter out existing data
            latest_timestamp = self.database.get_latest_crypto_timestamp(crypto_id)
            if latest_timestamp:
                # Filter out data that already exists in database
                new_ohlcv_objects = [obj for obj in ohlcv_objects if obj.timestamp > latest_timestamp]
                if not new_ohlcv_objects:
                    logger.info(f"No new data to store for {crypto_id} - latest timestamp {latest_timestamp} is up to date")
                    end_time = datetime.now()
                    collection_result.update({
                        'success': True,
                        'records_collected': 0,
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds()
                    })
                    return collection_result
                
                logger.info(f"Filtered {len(ohlcv_objects) - len(new_ohlcv_objects)} existing records for {crypto_id}")
                ohlcv_objects = new_ohlcv_objects
            
            # Convert OHLCV objects to database format
            db_records = self._convert_ohlcv_to_database_format(ohlcv_objects, crypto_id)
            
            # Store the data in database
            inserted_count = self.database.insert_crypto_data(db_records)
            
            # Update successful result
            end_time = datetime.now()
            collection_result.update({
                'success': True,
                'records_collected': inserted_count,
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            })
            
            # Log structured metrics for individual crypto collection
            self._log_structured_metrics('crypto_collection_complete', {
                'crypto_id': crypto_id,
                'success': True,
                'records_collected': inserted_count,
                'duration_seconds': collection_result['duration_seconds'],
                'days_requested': days
            })
            
            logger.info(f"Successfully collected and stored {inserted_count} new OHLCV records for {crypto_id}")
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

    def collect_crypto_data_range(self, crypto_id: str, start_timestamp: int, end_timestamp: int) -> Dict[str, Any]:
        """
        Collect and store OHLCV data for a specific cryptocurrency within a date range.
        
        This method uses the CoinGecko range endpoint for more precise data collection
        and ensures hourly granularity for ranges of 1-90 days.
        
        Args:
            crypto_id: Cryptocurrency identifier (e.g., "bitcoin")
            start_timestamp: Start timestamp in Unix format (seconds)
            end_timestamp: End timestamp in Unix format (seconds)
            
        Returns:
            Dict with collection results including success status and record count
            
        Raises:
            Exception: If data collection fails
        """
        start_time = datetime.now()
        start_date = datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d')
        end_date = datetime.fromtimestamp(end_timestamp).strftime('%Y-%m-%d')
        
        logger.info(f"Collecting OHLCV data for {crypto_id} from {start_date} to {end_date}")
        
        collection_result = {
            'crypto_id': crypto_id,
            'success': False,
            'records_collected': 0,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_seconds': None,
            'error': None,
            'date_range': {'start': start_date, 'end': end_date}
        }
        
        try:
            # Get market chart data from API using range endpoint
            market_data = self.api_client.get_market_chart_range_data(crypto_id, start_timestamp, end_timestamp)
            
            if not market_data:
                logger.warning(f"No market data received for {crypto_id} in range {start_date} to {end_date}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                return collection_result
            
            # Extract price and volume data
            prices = market_data.get('prices', [])
            volumes = market_data.get('total_volumes', [])
            
            if not prices:
                logger.warning(f"No price data received for {crypto_id} in range {start_date} to {end_date}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                collection_result['error'] = "No price data received"
                return collection_result
            
            # Convert market chart data to OHLCV format
            ohlcv_objects = self._convert_market_chart_to_ohlcv(prices, volumes, crypto_id)
            
            if not ohlcv_objects:
                logger.warning(f"No valid OHLCV data processed for {crypto_id} in range {start_date} to {end_date}")
                collection_result['end_time'] = datetime.now().isoformat()
                collection_result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                collection_result['error'] = "No valid OHLCV data processed"
                return collection_result
            
            # Check for incremental collection - filter out existing data
            latest_timestamp = self.database.get_latest_crypto_timestamp(crypto_id)
            if latest_timestamp:
                # Filter out data that already exists in database
                new_ohlcv_objects = [obj for obj in ohlcv_objects if obj.timestamp > latest_timestamp]
                if not new_ohlcv_objects:
                    logger.info(f"No new data to store for {crypto_id} in range {start_date} to {end_date}")
                    end_time = datetime.now()
                    collection_result.update({
                        'success': True,
                        'records_collected': 0,
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds()
                    })
                    return collection_result
                
                logger.info(f"Filtered {len(ohlcv_objects) - len(new_ohlcv_objects)} existing records for {crypto_id}")
                ohlcv_objects = new_ohlcv_objects
            
            # Convert OHLCV objects to database format
            db_records = self._convert_ohlcv_to_database_format(ohlcv_objects, crypto_id)
            
            # Store the data in database
            inserted_count = self.database.insert_crypto_data(db_records)
            
            # Update successful result
            end_time = datetime.now()
            collection_result.update({
                'success': True,
                'records_collected': inserted_count,
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            })
            
            # Log structured metrics for individual crypto collection
            self._log_structured_metrics('crypto_collection_range_complete', {
                'crypto_id': crypto_id,
                'success': True,
                'records_collected': inserted_count,
                'duration_seconds': collection_result['duration_seconds'],
                'date_range': collection_result['date_range']
            })
            
            logger.info(f"Successfully collected and stored {inserted_count} new OHLCV records for {crypto_id} in range {start_date} to {end_date}")
            return collection_result
            
        except Exception as e:
            end_time = datetime.now()
            collection_result.update({
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds(),
                'error': str(e)
            })
            
            # Log structured metrics for failed collection
            self._log_structured_metrics('crypto_collection_range_failed', {
                'crypto_id': crypto_id,
                'success': False,
                'error': str(e),
                'duration_seconds': collection_result['duration_seconds'],
                'date_range': collection_result['date_range']
            })
            
            logger.error(f"Failed to collect data for {crypto_id} in range {start_date} to {end_date}: {e}")
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
                        error_details = self._categorize_error(e)
                        
                        if attempt < max_retries_per_crypto and error_details == 'rate_limit':
                            logger.warning(f"Attempt {attempt + 1} failed for {crypto.name}: {e}, retrying...")
                            results['retries_used'] += 1
                            continue
                        else:
                            crypto_result['error'] = str(e)
                            crypto_result['error_details'] = {
                                'category': error_details,
                                'recoverable': error_details != 'validation' and error_details != 'storage',
                                'retry_recommended': error_details != 'validation' and error_details != 'storage'
                            }
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
                'error_details': {
                    'category': 'initialization',
                    'recoverable': False,
                    'retry_recommended': False
                }
            })
            return results 
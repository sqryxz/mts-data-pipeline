import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..api.fred_client import FREDClient
from ..data.macro_models import MacroIndicatorRecord
from ..data.storage import CSVStorage
from ..utils.exceptions import FREDAPIError, MacroDataError
from config.macro_settings import MACRO_INDICATORS

class MacroDataCollector:
    """Service for collecting macro economic indicators"""
    
    def __init__(self):
        """Initialize the macro data collector"""
        self.fred_client = FREDClient()
        self.storage = CSVStorage()
        self.logger = logging.getLogger(__name__)
    
    def _log_structured_metrics(self, event_type: str, data: Dict) -> None:
        """
        Log structured metrics in JSON format for monitoring and analysis.
        
        Args:
            event_type: Type of event being logged
            data: Metrics data to log
        """
        metrics = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **data
        }
        self.logger.info(f"METRICS: {json.dumps(metrics)}")
    
    def collect_indicator(self, indicator_key: str, days: int = 30) -> List[MacroIndicatorRecord]:
        """
        Collect single macro indicator data and save to CSV.
        
        Args:
            indicator_key: Macro indicator key (e.g., "VIX", "DXY")  
            days: Number of days of data to collect (default: 30)
            
        Returns:
            List of MacroIndicatorRecord objects collected
            
        Raises:
            MacroDataError: If indicator configuration not found
            FREDAPIError: If API request fails
        """
        # Log collection start
        collection_start_time = datetime.now()
        self.logger.info(f"Starting collection for indicator: {indicator_key}")
        self._log_structured_metrics('macro_collection_start', {
            'indicator': indicator_key,
            'days_requested': days
        })
        
        # Validate indicator key
        if indicator_key not in MACRO_INDICATORS:
            self._log_structured_metrics('macro_collection_error', {
                'indicator': indicator_key,
                'error_type': 'invalid_indicator',
                'error_message': f"Unknown indicator key: {indicator_key}"
            })
            raise MacroDataError(f"Unknown indicator key: {indicator_key}", indicator=indicator_key)
        
        indicator_config = MACRO_INDICATORS[indicator_key]
        series_id = indicator_config['fred_series_id']
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            self.logger.info(f"Fetching {indicator_key} data from {start_date_str} to {end_date_str}")
            
            # Log API request start
            api_start_time = datetime.now()
            self._log_structured_metrics('fred_api_request_start', {
                'indicator': indicator_key,
                'series_id': series_id,
                'start_date': start_date_str,
                'end_date': end_date_str
            })
            
            # Fetch data from FRED API
            api_data = self.fred_client.get_series_data(series_id, start_date_str, end_date_str)
            
            # Log API request completion
            api_duration = (datetime.now() - api_start_time).total_seconds()
            self._log_structured_metrics('fred_api_request_complete', {
                'indicator': indicator_key,
                'series_id': series_id,
                'duration_seconds': round(api_duration, 3),
                'records_returned': len(api_data) if api_data else 0
            })
            
            if not api_data:
                self.logger.warning(f"No data returned from FRED API for {indicator_key}")
                return []
            
            # Convert to MacroIndicatorRecord objects
            records = []
            for data_point in api_data:
                # Parse date
                date = datetime.strptime(data_point['date'], '%Y-%m-%d')
                
                record = MacroIndicatorRecord(
                    date=date,
                    value=data_point['value'],  # May be None for missing values
                    series_id=series_id,
                    indicator_name=indicator_config['name'],
                    units=indicator_config['units']
                )
                records.append(record)
            
            self.logger.info(f"Converted {len(records)} data points to MacroIndicatorRecord objects")
            
            # Save to CSV
            self.storage.save_macro_indicator_data(indicator_key, records)
            
            # Count non-None values for logging
            valid_values = sum(1 for r in records if r.value is not None)
            missing_values = len(records) - valid_values
            
            # Calculate collection duration
            collection_duration = (datetime.now() - collection_start_time).total_seconds()
            
            # Log successful completion with comprehensive metrics
            self._log_structured_metrics('macro_collection_complete', {
                'indicator': indicator_key,
                'series_id': series_id,
                'success': True,
                'duration_seconds': round(collection_duration, 3),
                'records_collected': len(records),
                'valid_values': valid_values,
                'missing_values': missing_values,
                'missing_percentage': round((missing_values / len(records)) * 100, 1) if len(records) > 0 else 0,
                'date_range_start': start_date_str,
                'date_range_end': end_date_str,
                'days_requested': days
            })
            
            self.logger.info(f"Successfully collected {indicator_key}: {valid_values} valid values, {missing_values} missing values")
            
            return records
            
        except FREDAPIError as e:
            # Log API-specific error
            collection_duration = (datetime.now() - collection_start_time).total_seconds()
            self._log_structured_metrics('macro_collection_complete', {
                'indicator': indicator_key,
                'series_id': series_id,
                'success': False,
                'duration_seconds': round(collection_duration, 3),
                'error_type': 'fred_api_error',
                'error_message': str(e),
                'error_code': getattr(e, 'status_code', None)
            })
            self.logger.error(f"FRED API error collecting {indicator_key}: {e}")
            raise
        except Exception as e:
            # Log unexpected error
            collection_duration = (datetime.now() - collection_start_time).total_seconds()
            self._log_structured_metrics('macro_collection_complete', {
                'indicator': indicator_key,
                'series_id': series_id if 'series_id' in locals() else None,
                'success': False,
                'duration_seconds': round(collection_duration, 3),
                'error_type': 'unexpected_error',
                'error_message': str(e)
            })
            self.logger.error(f"Unexpected error collecting {indicator_key}: {e}")
            raise MacroDataError(f"Failed to collect {indicator_key}: {str(e)}", indicator=indicator_key)
    
    def collect_all_indicators(self, days: int = 30) -> Dict[str, List[MacroIndicatorRecord]]:
        """
        Collect all configured macro indicators.
        
        Args:
            days: Number of days of data to collect (default: 30)
            
        Returns:
            Dictionary mapping indicator keys to lists of MacroIndicatorRecord objects
        """
        # Log batch collection start
        batch_start_time = datetime.now()
        self.logger.info(f"Starting collection for all indicators ({len(MACRO_INDICATORS)} total)")
        self._log_structured_metrics('macro_batch_collection_start', {
            'total_indicators': len(MACRO_INDICATORS),
            'indicators': list(MACRO_INDICATORS.keys()),
            'days_requested': days
        })
        
        results = {}
        success_count = 0
        error_count = 0
        
        for indicator_key in MACRO_INDICATORS.keys():
            try:
                self.logger.info(f"Collecting {indicator_key}...")
                records = self.collect_indicator(indicator_key, days)
                results[indicator_key] = records
                success_count += 1
                
                # Log summary for this indicator
                valid_values = sum(1 for r in records if r.value is not None)
                self.logger.info(f"✅ {indicator_key}: {len(records)} records ({valid_values} valid, {len(records) - valid_values} missing)")
                
            except Exception as e:
                error_count += 1
                results[indicator_key] = []  # Empty list for failed indicators
                self.logger.error(f"❌ Failed to collect {indicator_key}: {str(e)}")
        
        # Calculate batch metrics
        batch_duration = (datetime.now() - batch_start_time).total_seconds()
        total_records = sum(len(records) for records in results.values())
        total_valid_records = sum(sum(1 for r in records if r.value is not None) for records in results.values())
        total_missing_records = total_records - total_valid_records
        
        # Log comprehensive batch completion metrics
        self._log_structured_metrics('macro_batch_collection_complete', {
            'total_indicators': len(MACRO_INDICATORS),
            'successful_indicators': success_count,
            'failed_indicators': error_count,
            'success_rate': round((success_count / len(MACRO_INDICATORS)) * 100, 1),
            'duration_seconds': round(batch_duration, 3),
            'total_records': total_records,
            'valid_records': total_valid_records,
            'missing_records': total_missing_records,
            'missing_percentage': round((total_missing_records / total_records) * 100, 1) if total_records > 0 else 0,
            'successful_indicators_list': [k for k, v in results.items() if v],
            'failed_indicators_list': [k for k, v in results.items() if not v],
            'days_requested': days
        })
        
        # Log overall summary
        self.logger.info(f"Collection complete: {success_count} successful, {error_count} failed, {total_records} total records")
        
        return results 
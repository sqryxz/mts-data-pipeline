import os
import requests
from typing import Dict, Optional
from src.utils.exceptions import FREDAPIError, APIConnectionError, APITimeoutError
from src.utils.retry import retry_with_backoff

class FREDClient:
    """St Louis Federal Reserve Economic Data API client"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FRED API client.
        
        Args:
            api_key: FRED API key, if not provided will use FRED_API_KEY env var
        """
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        if not self.api_key:
            raise FREDAPIError("FRED API key not provided. Set FRED_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.session = requests.Session()
        self.timeout = 30
    
    @retry_with_backoff(max_retries=3, base_delay=1.0, backoff_factor=2.0)
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """
        Make HTTP request to FRED API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            FREDAPIError: If API returns error response
            APIConnectionError: If connection fails
            APITimeoutError: If request times out
        """
        # Add API key and format to all requests
        request_params = {
            'api_key': self.api_key,
            'file_type': 'json',
            **params
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=request_params, timeout=self.timeout)
            
            # Check for HTTP errors
            if response.status_code != 200:
                raise FREDAPIError(
                    f"FRED API returned status code {response.status_code}: {response.text}",
                    status_code=response.status_code
                )
            
            # Parse JSON response
            data = response.json()
            
            # Check for FRED API errors in response
            if 'error_code' in data:
                raise FREDAPIError(
                    f"FRED API error: {data.get('error_message', 'Unknown error')}",
                    status_code=data.get('error_code')
                )
            
            return data
        
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Failed to connect to FRED API: {str(e)}")
        
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"FRED API request timed out after {self.timeout} seconds")
        
        except requests.exceptions.RequestException as e:
            raise FREDAPIError(f"FRED API request failed: {str(e)}")
    
    def get_series_data(self, series_id: str, start_date: str, end_date: str) -> list:
        """
        Fetch time series data for a specific FRED series.
        
        Args:
            series_id: FRED series identifier (e.g., 'VIXCLS')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of dictionaries containing date and value data
            
        Raises:
            FREDAPIError: If API request fails or series not found
        """
        params = {
            'series_id': series_id,
            'observation_start': start_date,
            'observation_end': end_date
        }
        
        try:
            response_data = self._make_request('series/observations', params)
            
            # Extract observations from response
            if 'observations' not in response_data:
                raise FREDAPIError(f"No observations found in FRED response for series {series_id}")
            
            observations = response_data['observations']
            
            # Parse and format data
            parsed_data = []
            for obs in observations:
                # Handle missing values (various formats)
                value = None
                raw_value = obs.get('value')
                
                # Check for missing data indicators
                if raw_value is not None and raw_value not in ['.', '', 'NA', 'N/A', '#N/A']:
                    try:
                        value = float(raw_value)
                    except (ValueError, TypeError):
                        # If can't convert to float, treat as missing
                        value = None
                
                parsed_data.append({
                    'date': obs['date'],
                    'value': value,
                    'series_id': series_id
                })
            
            return parsed_data
            
        except FREDAPIError:
            # Re-raise FRED API errors
            raise
        except Exception as e:
            raise FREDAPIError(f"Failed to parse FRED series data for {series_id}: {str(e)}", series_id=series_id) 
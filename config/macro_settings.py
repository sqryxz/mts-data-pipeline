# Macro indicators configuration
FRED_API_CONFIG = {
    'base_url': 'https://api.stlouisfed.org/fred',
    'api_key_env': 'FRED_API_KEY',  # Environment variable
    'timeout': 30,
    'max_retries': 3,
    'rate_limit_per_day': 120000,  # FRED API limit
    'rate_limit_per_hour': 1000
}

MACRO_INDICATORS = {
    'VIX': {
        'fred_series_id': 'VIXCLS',
        'name': 'CBOE Volatility Index',
        'frequency': 'daily',
        'units': 'Index',
        'file_prefix': 'vix'
    },
    'DXY': {
        'fred_series_id': 'DTWEXBGS',  # Trade Weighted U.S. Dollar Index
        'name': 'US Dollar Index',
        'frequency': 'daily', 
        'units': 'Index (Jan 1997=100)',
        'file_prefix': 'dxy'
    },
    'TREASURY_10Y': {
        'fred_series_id': 'DGS10',
        'name': '10-Year Treasury Constant Maturity Rate',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'treasury_10y'
    },
    'FED_FUNDS_RATE': {
        'fred_series_id': 'DFF',
        'name': 'Federal Funds Effective Rate',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'fed_funds_rate'
    }
}

MACRO_COLLECTION_CONFIG = {
    'collection_interval_hours': 24,  # Daily collection
    'historical_days_default': 30,
    'data_retention_years': 10,
    'missing_data_tolerance_days': 5,  # Allow 5 days of missing data
    'weekend_data_handling': 'forward_fill',  # Forward fill weekend gaps
    'holiday_data_handling': 'interpolate'
} 
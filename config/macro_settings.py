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
    # Support both simplified keys and FRED series IDs for compatibility
    'VIX': {
        'fred_series_id': 'VIXCLS',
        'name': 'CBOE Volatility Index',
        'frequency': 'daily',
        'units': 'Index',
        'file_prefix': 'vix'
    },
    'VIXCLS': {
        'fred_series_id': 'VIXCLS',
        'name': 'CBOE Volatility Index',
        'frequency': 'daily',
        'units': 'Index',
        'file_prefix': 'vixcls'
    },
    'DXY': {
        'fred_series_id': 'DTWEXBGS',  # Trade Weighted U.S. Dollar Index
        'name': 'US Dollar Index',
        'frequency': 'daily', 
        'units': 'Index (Jan 1997=100)',
        'file_prefix': 'dxy'
    },
    'DTWEXBGS': {
        'fred_series_id': 'DTWEXBGS',
        'name': 'Trade Weighted U.S. Dollar Index (Broad)',
        'frequency': 'daily',
        'units': 'Index (Jan 1997=100)',
        'file_prefix': 'dtwexbgs'
    },
    'TREASURY_10Y': {
        'fred_series_id': 'DGS10',
        'name': '10-Year Treasury Constant Maturity Rate',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'treasury_10y'
    },
    'DGS10': {
        'fred_series_id': 'DGS10',
        'name': '10-Year Treasury Constant Maturity Rate',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'dgs10'
    },
    'FED_FUNDS_RATE': {
        'fred_series_id': 'DFF',
        'name': 'Federal Funds Effective Rate',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'fed_funds_rate'
    },
    'DFF': {
        'fred_series_id': 'DFF',
        'name': 'Federal Funds Effective Rate',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'dff'
    },
    'DEXUSEU': {
        'fred_series_id': 'DEXUSEU',
        'name': 'US/Euro Foreign Exchange Rate',
        'frequency': 'daily',
        'units': 'US Dollars to One Euro',
        'file_prefix': 'dexuseu'
    },
    'DEXCHUS': {
        'fred_series_id': 'DEXCHUS',
        'name': 'China/US Foreign Exchange Rate',
        'frequency': 'daily',
        'units': 'Chinese Yuan to One US Dollar',
        'file_prefix': 'dexchus'
    },
    'BAMLH0A0HYM2': {
        'fred_series_id': 'BAMLH0A0HYM2',
        'name': 'ICE BofA US High Yield Index Option-Adjusted Spread',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'bamlh0a0hym2'
    },
    'RRPONTSYD': {
        'fred_series_id': 'RRPONTSYD',
        'name': 'Overnight Reverse Repurchase Agreements',
        'frequency': 'daily',
        'units': 'Billions of US Dollars',
        'file_prefix': 'rrpontsyd'
    },
    'SOFR': {
        'fred_series_id': 'SOFR',
        'name': 'Secured Overnight Financing Rate',
        'frequency': 'daily',
        'units': 'Percent',
        'file_prefix': 'sofr'
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
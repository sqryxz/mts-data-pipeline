"""
Macro Analytics Service

Service layer for macro indicator analytics that coordinates between
the calculator, repository, and external APIs.
"""

import json
import logging
import copy
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

# Import components
try:
    from analytics.macro.calculator import MacroCalculator
    from analytics.storage.analytics_repository import AnalyticsRepository
except ImportError:
    # Fallback for when running as module
    from ..analytics.macro.calculator import MacroCalculator
    from ..analytics.storage.analytics_repository import AnalyticsRepository


class MacroAnalyticsService:
    """
    Service layer for macro indicator analytics.
    
    This service coordinates between the calculator, repository, and external APIs
    to provide a unified interface for macro indicator analysis.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the macro analytics service.
        
        Args:
            config_path: Path to configuration JSON file (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_configuration(config_path)
        
        # Initialize components
        self.repository = None
        self.calculator = None
        
        # Initialize components based on configuration
        self._initialize_components()
        
        self.logger.info("MacroAnalyticsService initialized successfully")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration without mutation.
        
        Returns:
            Dict with default configuration settings
        """
        return {
            'database': {
                'path': 'data/crypto_data.db',
                'type': 'sqlite',
                'connection_pool_size': 5,
                'timeout': 30
            },
            'analytics': {
                'default_timeframes': ['1h', '4h', '1d', '1w', '1m'],
                'default_metrics': ['roc', 'z_score'],
                'lookback_periods': {
                    '1h': 24,
                    '4h': 168,
                    '1d': 30,
                    '1w': 52,
                    '1m': 12
                },
                'interpolation': True,
                'value_column': 'value',
                'calculation_settings': {
                    'roc': {
                        'min_periods': 2,
                        'allow_negative': True
                    },
                    'z_score': {
                        'min_periods': 10,
                        'rolling_window': 30
                    }
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/macro_analytics.log',
                'max_size': '10MB',
                'backup_count': 5
            },
            'indicators': {
                'supported': ['VIX', 'DGS10', 'DTWEXBGS', 'DFF'],
                'default': 'VIX',
                'aliases': {
                    'VIX': 'CBOE Volatility Index',
                    'DGS10': '10-Year Treasury Constant Maturity Rate',
                    'DTWEXBGS': 'Trade Weighted U.S. Dollar Index',
                    'DFF': 'Federal Funds Effective Rate'
                }
            },
            'api': {
                'rate_limit': {
                    'requests_per_minute': 60,
                    'requests_per_hour': 1000
                },
                'cors': {
                    'allowed_origins': ['*'],
                    'allowed_methods': ['GET', 'POST'],
                    'allowed_headers': ['*']
                },
                'security': {
                    'enable_authentication': False,
                    'enable_rate_limiting': True,
                    'max_request_size': '10MB'
                }
            },
            'cache': {
                'enabled': True,
                'ttl_seconds': 300,
                'max_size': 1000
            },
            'monitoring': {
                'enable_metrics': True,
                'metrics_interval': 60,
                'health_check_interval': 30
            },
            'development': {
                'debug_mode': False,
                'test_database_path': 'data/test_crypto_data.db',
                'log_level': 'DEBUG'
            }
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if configuration is valid
        """
        required_sections = ['database', 'analytics', 'indicators']
        if not all(section in config for section in required_sections):
            return False
        
        # Validate database section
        if 'database' in config:
            db_config = config['database']
            if not isinstance(db_config, dict) or 'path' not in db_config:
                return False
        
        # Validate analytics section
        if 'analytics' in config:
            analytics_config = config['analytics']
            if not isinstance(analytics_config, dict):
                return False
            
            required_analytics = ['default_timeframes', 'lookback_periods']
            if not all(key in analytics_config for key in required_analytics):
                return False
        
        # Validate indicators section
        if 'indicators' in config:
            indicators_config = config['indicators']
            if not isinstance(indicators_config, dict) or 'supported' not in indicators_config:
                return False
        
        return True
    
    def _load_configuration(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from JSON file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dict with configuration settings
        """
        # Start with a deep copy of default config to prevent mutation
        default_config = copy.deepcopy(self._get_default_config())
        
        if config_path and Path(config_path).exists():
            try:
                # Validate config path to prevent path traversal
                config_path = Path(config_path).resolve()
                if not str(config_path).startswith(str(Path.cwd())):
                    raise ValueError("Configuration path outside current directory")
                
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                
                # Validate file configuration
                if not self._validate_config(file_config):
                    self.logger.error(f"Invalid configuration structure in {config_path}")
                    self.logger.info("Using default configuration")
                else:
                    # Merge file config with defaults (creates new dict)
                    merged_config = self._merge_config(default_config, file_config)
                    self.logger.info(f"Loaded configuration from {config_path}")
                    return merged_config
                
            except Exception as e:
                self.logger.error(f"Failed to load configuration from {config_path}: {e}")
                self.logger.info("Using default configuration")
        else:
            if config_path:
                self.logger.warning(f"Configuration file not found: {config_path}")
            self.logger.info("Using default configuration")
        
        return default_config
    
    def _merge_config(self, default_config: Dict[str, Any], file_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge file configuration with defaults (creates new dict).
        
        Args:
            default_config: Default configuration dict
            file_config: File configuration dict
            
        Returns:
            Dict: Merged configuration (new dict, doesn't mutate inputs)
        """
        # Create a deep copy to prevent mutation
        merged = copy.deepcopy(default_config)
        
        for key, value in file_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_config(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _validate_dependencies(self) -> bool:
        """
        Validate that required dependencies are available.
        
        Returns:
            bool: True if all dependencies are available
        """
        try:
            # Test imports
            from analytics.macro.calculator import MacroCalculator
            from analytics.storage.analytics_repository import AnalyticsRepository
            return True
        except ImportError as e:
            self.logger.error(f"Missing required dependencies: {e}")
            return False
    
    def _initialize_components(self) -> None:
        """
        Initialize repository and calculator components.
        """
        try:
            # Validate dependencies first
            if not self._validate_dependencies():
                raise RuntimeError("Required dependencies not available")
            
            # Validate database path
            db_path = self.config['database']['path']
            db_dir = Path(db_path).parent
            if not db_dir.exists():
                self.logger.info(f"Creating database directory: {db_dir}")
                db_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize repository
            self.repository = AnalyticsRepository(db_path)
            self.logger.info(f"Initialized repository with database: {db_path}")
            
            # Initialize calculator
            self.calculator = MacroCalculator(repository=self.repository)
            self.logger.info("Initialized calculator with repository")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _sanitize_input(self, value: Any) -> Optional[str]:
        """
        Sanitize input values.
        
        Args:
            value: Input value to sanitize
            
        Returns:
            Optional[str]: Sanitized string or None if invalid
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            sanitized = value.strip()
            return sanitized if sanitized else None
        
        return str(value).strip()
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dict with current configuration
        """
        return copy.deepcopy(self.config)
    
    def get_supported_indicators(self) -> List[str]:
        """
        Get list of supported indicators.
        
        Returns:
            List of supported indicator names
        """
        return self.config['indicators']['supported'].copy()
    
    def get_default_timeframes(self) -> List[str]:
        """
        Get default timeframes for analysis.
        
        Returns:
            List of default timeframe strings
        """
        return self.config['analytics']['default_timeframes'].copy()
    
    def get_lookback_period(self, timeframe: str) -> int:
        """
        Get lookback period for a specific timeframe.
        
        Args:
            timeframe: Timeframe string
            
        Returns:
            Lookback period in periods
        """
        lookback_periods = self.config['analytics']['lookback_periods']
        return lookback_periods.get(timeframe, 30)  # Default to 30
    
    def validate_indicator(self, indicator: str) -> bool:
        """
        Validate that an indicator is supported.
        
        Args:
            indicator: Indicator name to validate
            
        Returns:
            bool: True if indicator is supported
        """
        # Sanitize input
        sanitized = self._sanitize_input(indicator)
        if sanitized is None:
            return False
        
        supported_indicators = self.get_supported_indicators()
        return sanitized.upper() in [i.upper() for i in supported_indicators]
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate that a timeframe is supported.
        
        Args:
            timeframe: Timeframe to validate
            
        Returns:
            bool: True if timeframe is supported
        """
        # Sanitize input
        sanitized = self._sanitize_input(timeframe)
        if sanitized is None:
            return False
        
        if self.calculator is None:
            return False
        
        return self.calculator.validate_timeframe(sanitized)
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the service and its components.
        
        Returns:
            Dict with service information
        """
        return {
            'service_type': 'MacroAnalyticsService',
            'repository_available': self.repository is not None,
            'calculator_available': self.calculator is not None,
            'supported_indicators': self.get_supported_indicators(),
            'default_timeframes': self.get_default_timeframes(),
            'configuration_loaded': bool(self.config),
            'initialized_at': datetime.now().isoformat()
        }
    
    def analyze_indicator(self, 
                         indicator: str, 
                         timeframes: Optional[List[str]] = None,
                         metrics: Optional[List[str]] = None,
                         **kwargs) -> Optional[Dict[str, Any]]:
        """
        Analyze an indicator across multiple timeframes.
        
        Args:
            indicator: Indicator name to analyze
            timeframes: List of timeframes to analyze (defaults to config)
            metrics: List of metrics to calculate (defaults to config)
            **kwargs: Additional parameters for calculations
            
        Returns:
            Optional[Dict]: Analysis results or None if error
        """
        # Sanitize and validate indicator
        sanitized_indicator = self._sanitize_input(indicator)
        if sanitized_indicator is None:
            self.logger.error("Invalid indicator: None or empty")
            return None
        
        if not self.validate_indicator(sanitized_indicator):
            self.logger.error(f"Unsupported indicator: {sanitized_indicator}")
            return None
        
        # Use default timeframes if none provided
        if timeframes is None:
            timeframes = self.get_default_timeframes()
        
        # Validate timeframes
        invalid_timeframes = []
        for tf in timeframes:
            if not self.validate_timeframe(tf):
                invalid_timeframes.append(tf)
        
        if invalid_timeframes:
            self.logger.error(f"Invalid timeframes: {invalid_timeframes}")
            return None
        
        try:
            # Perform analysis using calculator
            if self.calculator is None:
                self.logger.error("Calculator not available")
                return None
            
            # Get calculation settings and pass to calculator
            analytics_config = self.get_analytics_config()
            calculation_settings = analytics_config.get('calculation_settings', {})
            
            # Add calculation settings to kwargs
            calculator_kwargs = kwargs.copy()
            calculator_kwargs.update({
                'calculation_settings': calculation_settings,
                'analytics_config': analytics_config
            })
            
            result = self.calculator.calculate_metrics(
                sanitized_indicator, timeframes, **calculator_kwargs
            )
            
            if result is not None:
                # Add service metadata
                result['service_info'] = {
                    'analysis_time': datetime.now().isoformat(),
                    'requested_timeframes': timeframes,
                    'requested_metrics': metrics,  # Note: Currently logged but not used
                    'indicator': sanitized_indicator,
                    'indicator_alias': self.get_indicator_alias(sanitized_indicator),
                    'calculation_settings_used': calculation_settings,
                    'config_version': '1.0'
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {sanitized_indicator}: {e}")
            return None
    
    def _save_results(self, results: Dict[str, Any]) -> bool:
        """
        Save analysis results to database.
        
        Args:
            results: Analysis results to save
            
        Returns:
            bool: True if save successful
        """
        try:
            if self.repository is None:
                self.logger.error("Repository not available for saving results")
                return False
            
            # Convert results to database format
            # This would be implemented based on the repository interface
            # For now, we'll log the intent
            self.logger.info(f"Saving results for {results.get('indicator', 'unknown')}")
            
            # TODO: Implement actual save logic when repository interface is defined
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            return False
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the service's capabilities and status.
        
        Returns:
            Dict with service summary
        """
        return {
            'service_info': self.get_service_info(),
            'calculator_summary': self.calculator.get_calculation_summary() if self.calculator else None,
            'configuration': {
                'database_path': self.config['database']['path'],
                'default_timeframes': self.config['analytics']['default_timeframes'],
                'supported_indicators': self.config['indicators']['supported']
            },
            'status': 'ready' if self.calculator and self.repository else 'error'
        }
    
    def get_calculation_settings(self, metric: str) -> Dict[str, Any]:
        """
        Get calculation settings for a specific metric.
        
        Args:
            metric: Metric name ('roc' or 'z_score')
            
        Returns:
            Dict with calculation settings for the metric
        """
        analytics_config = self.config.get('analytics', {})
        calculation_settings = analytics_config.get('calculation_settings', {})
        return calculation_settings.get(metric, {})
    
    def get_analytics_config(self) -> Dict[str, Any]:
        """
        Get analytics configuration.
        
        Returns:
            Dict with analytics configuration
        """
        return self.config.get('analytics', {}).copy()
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API configuration.
        
        Returns:
            Dict with API configuration
        """
        return self.config.get('api', {}).copy()
    
    def get_cache_config(self) -> Dict[str, Any]:
        """
        Get cache configuration.
        
        Returns:
            Dict with cache configuration
        """
        return self.config.get('cache', {}).copy()
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """
        Get monitoring configuration.
        
        Returns:
            Dict with monitoring configuration
        """
        return self.config.get('monitoring', {}).copy()
    
    def is_debug_mode(self) -> bool:
        """
        Check if debug mode is enabled.
        
        Returns:
            bool: True if debug mode is enabled
        """
        dev_config = self.config.get('development', {})
        return dev_config.get('debug_mode', False)
    
    def get_test_database_path(self) -> str:
        """
        Get test database path.
        
        Returns:
            str: Test database path
        """
        dev_config = self.config.get('development', {})
        return dev_config.get('test_database_path', 'data/test_crypto_data.db')
    
    def get_indicator_alias(self, indicator: str) -> str:
        """
        Get the alias/description for an indicator.
        
        Args:
            indicator: Indicator name
            
        Returns:
            str: Indicator alias/description
        """
        indicators_config = self.config.get('indicators', {})
        aliases = indicators_config.get('aliases', {})
        return aliases.get(indicator, indicator)
    
    def get_all_indicators_with_aliases(self) -> Dict[str, str]:
        """
        Get all indicators with their aliases.
        
        Returns:
            Dict mapping indicator names to aliases
        """
        indicators_config = self.config.get('indicators', {})
        aliases = indicators_config.get('aliases', {})
        supported = indicators_config.get('supported', [])
        
        result = {}
        for indicator in supported:
            result[indicator] = aliases.get(indicator, indicator)
        
        return result
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        try:
            if hasattr(self.repository, 'close'):
                self.repository.close()
                self.logger.info("Repository connection closed")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")


# Example usage
if __name__ == "__main__":
    # Create service with default configuration
    service = MacroAnalyticsService()
    
    # Get service info
    info = service.get_service_info()
    print(f"Service Info: {info}")
    
    # Get supported indicators
    indicators = service.get_supported_indicators()
    print(f"Supported Indicators: {indicators}")
    
    # Get default timeframes
    timeframes = service.get_default_timeframes()
    print(f"Default Timeframes: {timeframes}")
    
    print("=== Service initialization completed ===") 
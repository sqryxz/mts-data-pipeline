from config.settings import Config

# Initialize configuration instance
_config = Config()

# Export Binance configuration from centralized settings
BINANCE_CONFIG = _config.get_binance_config() 
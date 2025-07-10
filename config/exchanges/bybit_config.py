from config.settings import Config

# Initialize configuration instance
_config = Config()

# Export Bybit configuration from centralized settings
BYBIT_CONFIG = _config.get_bybit_config() 
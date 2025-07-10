from config.settings import Config

# Initialize configuration instance
_config = Config()

# Export order book configuration from centralized settings
ORDERBOOK_CONFIG = _config.get_orderbook_config() 
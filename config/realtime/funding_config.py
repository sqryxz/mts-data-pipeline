from config.settings import Config

# Initialize configuration instance
_config = Config()

# Export funding configuration from centralized settings
FUNDING_CONFIG = _config.get_funding_config() 
from config.settings import Config


def test_config_loads_from_environment():
    """Test that Config class loads configuration values."""
    config = Config()
    assert config.COINGECKO_BASE_URL is not None
    assert config.REQUEST_TIMEOUT is not None


def test_config_defaults():
    """Test that Config class has default values."""
    config = Config()
    assert config.COINGECKO_BASE_URL == 'https://api.coingecko.com/api/v3'
    assert config.REQUEST_TIMEOUT == 30 
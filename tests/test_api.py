import pytest
from unittest.mock import patch, Mock
from src.api.coingecko_client import CoinGeckoClient


def test_coingecko_client_initialization():
    """Test that CoinGeckoClient initializes correctly."""
    client = CoinGeckoClient()
    assert client.base_url == 'https://api.coingecko.com/api/v3'
    assert client.timeout == 30


@patch('src.api.coingecko_client.requests.get')
def test_ping_success(mock_get):
    """Test successful ping response."""
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {"gecko_says": "(V3) To the Moon!"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    client = CoinGeckoClient()
    response = client.ping()
    
    assert response["gecko_says"] == "(V3) To the Moon!"
    mock_get.assert_called_once_with(
        "https://api.coingecko.com/api/v3/ping", 
        timeout=30
    )


@patch('src.api.coingecko_client.requests.get')
def test_ping_network_error(mock_get):
    """Test ping with network error."""
    import requests
    # Mock network error
    mock_get.side_effect = requests.exceptions.RequestException("Network error")
    
    client = CoinGeckoClient()
    
    with pytest.raises(Exception) as exc_info:
        client.ping()
    
    assert "API request failed" in str(exc_info.value)


@patch('src.api.coingecko_client.requests.get')
def test_get_top_cryptos_success(mock_get):
    """Test successful get_top_cryptos response."""
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
        {"id": "tether", "symbol": "usdt", "name": "Tether"}
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    client = CoinGeckoClient()
    data = client.get_top_cryptos(3)
    
    assert len(data) == 3
    assert "bitcoin" in [c["id"] for c in data]
    assert "ethereum" in [c["id"] for c in data]
    
    # Verify API call parameters
    mock_get.assert_called_once_with(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 3,
            'page': 1,
            'sparkline': 'false'
        },
        timeout=30
    )


@patch('src.api.coingecko_client.requests.get')
def test_get_top_cryptos_api_error(mock_get):
    """Test get_top_cryptos with API error."""
    import requests
    # Mock API error
    mock_get.side_effect = requests.exceptions.RequestException("Rate limit exceeded")
    
    client = CoinGeckoClient()
    
    with pytest.raises(Exception) as exc_info:
        client.get_top_cryptos(3)
    
    assert "API request failed" in str(exc_info.value)


@patch('src.api.coingecko_client.requests.get')
def test_get_ohlc_data_success(mock_get):
    """Test successful get_ohlc_data response."""
    # Mock successful OHLC response (timestamp, open, high, low, close)
    mock_response = Mock()
    mock_response.json.return_value = [
        [1640995200000, 47000.0, 48000.0, 46500.0, 47500.0],
        [1641081600000, 47500.0, 48500.0, 47000.0, 48000.0]
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    client = CoinGeckoClient()
    data = client.get_ohlc_data("bitcoin", days=1)
    
    assert len(data) > 0
    assert len(data[0]) == 5
    assert data[0][0] == 1640995200000  # timestamp
    assert data[0][1] == 47000.0  # open
    
    # Verify API call parameters
    mock_get.assert_called_once_with(
        "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc",
        params={
            'vs_currency': 'usd',
            'days': 1
        },
        timeout=30
    )


@patch('src.api.coingecko_client.requests.get')
def test_get_ohlc_data_missing_data(mock_get):
    """Test get_ohlc_data with empty response."""
    # Mock empty response
    mock_response = Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    client = CoinGeckoClient()
    data = client.get_ohlc_data("nonexistent-coin", days=1)
    
    assert len(data) == 0


@patch('src.api.coingecko_client.requests.get')
def test_get_ohlc_data_api_error(mock_get):
    """Test get_ohlc_data with API error."""
    import requests
    # Mock API error
    mock_get.side_effect = requests.exceptions.RequestException("Invalid coin ID")
    
    client = CoinGeckoClient()
    
    with pytest.raises(Exception) as exc_info:
        client.get_ohlc_data("invalid-coin", days=1)
    
    assert "API request failed" in str(exc_info.value) 
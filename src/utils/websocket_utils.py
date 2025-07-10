import asyncio
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> None:
    """Exponential backoff delay"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    await asyncio.sleep(delay)

def validate_websocket_message(message: Dict[str, Any], required_fields: list) -> bool:
    """Validate WebSocket message contains required fields"""
    return all(field in message for field in required_fields)

def parse_websocket_message(raw_message: str) -> Optional[Dict[str, Any]]:
    """Parse raw WebSocket message to dictionary"""
    try:
        return json.loads(raw_message)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse WebSocket message: {e}")
        return None

def format_symbol(symbol: str, exchange: str) -> str:
    """Format symbol for specific exchange"""
    if exchange.lower() == 'binance':
        return symbol.lower()
    elif exchange.lower() == 'bybit':
        return symbol.upper()
    return symbol 
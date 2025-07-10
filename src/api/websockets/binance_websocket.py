import asyncio
import websockets
import json
import logging
from typing import List, Dict, Any, Callable, Optional
from src.api.websockets.base_websocket import BaseWebSocket
from src.utils.websocket_utils import exponential_backoff, parse_websocket_message
from config.exchanges.binance_config import BINANCE_CONFIG

logger = logging.getLogger(__name__)

class BinanceWebSocket(BaseWebSocket):
    def __init__(self, message_handler: Optional[Callable] = None):
        super().__init__(BINANCE_CONFIG['websocket_url'])
        self.message_handler = message_handler
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    async def connect(self) -> None:
        """Connect to Binance WebSocket"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("Connected to Binance WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from Binance WebSocket")
    
    async def subscribe(self, channels: List[str]) -> None:
        """Subscribe to channels"""
        if not self.is_connected:
            raise Exception("WebSocket not connected")
            
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": channels,
            "id": 1
        }
        
        await self.websocket.send(json.dumps(subscribe_msg))
        self.subscriptions.extend(channels)
        logger.info(f"Subscribed to channels: {channels}")
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message"""
        try:
            if self.message_handler:
                await self.message_handler(message)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def listen(self) -> None:
        """Listen for messages"""
        try:
            async for message in self.websocket:
                parsed_message = parse_websocket_message(message)
                if parsed_message:
                    await self.handle_message(parsed_message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
            await self.reconnect()
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
            await self.reconnect()
    
    async def reconnect(self) -> None:
        """Reconnect with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return
            
        self.reconnect_attempts += 1
        await exponential_backoff(self.reconnect_attempts)
        
        try:
            await self.connect()
            if self.subscriptions:
                await self.subscribe(self.subscriptions)
        except Exception as e:
            logger.error(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
            await self.reconnect() 
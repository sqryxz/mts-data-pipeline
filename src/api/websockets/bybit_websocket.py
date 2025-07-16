import asyncio
import websockets
import json
import logging
import time
from typing import List, Dict, Any, Callable, Optional
from src.api.websockets.base_websocket import BaseWebSocket
from src.utils.websocket_utils import exponential_backoff, parse_websocket_message
from config.exchanges.bybit_config import BYBIT_CONFIG
from src.services.collector import RollingVolatilityCalculator
import sqlite3

logger = logging.getLogger(__name__)

class BybitWebSocket(BaseWebSocket):
    def __init__(self, message_handler: Optional[Callable] = None):
        super().__init__(BYBIT_CONFIG['websocket_url'])
        self.message_handler = message_handler
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.req_id = 1  # Request ID for Bybit API
        # --- Add rolling volatility calculators for BTCUSDT and ETHUSDT ---
        self.btc_vol_calc = RollingVolatilityCalculator(window_size=15)
        self.eth_vol_calc = RollingVolatilityCalculator(window_size=15)
        
    async def connect(self) -> None:
        """Connect to Bybit WebSocket"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("Connected to Bybit WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to Bybit WebSocket: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from Bybit WebSocket")
    
    async def subscribe(self, channels: List[str]) -> None:
        """Subscribe to channels using Bybit WebSocket v5 format"""
        if not self.is_connected:
            raise Exception("WebSocket not connected")
            
        # Bybit v5 WebSocket subscription format
        subscribe_msg = {
            "op": "subscribe",
            "args": channels,
            "req_id": str(self.req_id)
        }
        
        await self.websocket.send(json.dumps(subscribe_msg))
        self.subscriptions.extend(channels)
        self.req_id += 1
        logger.info(f"Subscribed to Bybit channels: {channels}")
    
    async def unsubscribe(self, channels: List[str]) -> None:
        """Unsubscribe from channels using Bybit WebSocket v5 format"""
        if not self.is_connected:
            raise Exception("WebSocket not connected")
            
        unsubscribe_msg = {
            "op": "unsubscribe",
            "args": channels,
            "req_id": str(self.req_id)
        }
        
        await self.websocket.send(json.dumps(unsubscribe_msg))
        # Remove from subscriptions
        for channel in channels:
            if channel in self.subscriptions:
                self.subscriptions.remove(channel)
        self.req_id += 1
        logger.info(f"Unsubscribed from Bybit channels: {channels}")
    
    async def ping(self) -> None:
        """Send ping to maintain connection"""
        if not self.is_connected:
            return
            
        ping_msg = {
            "op": "ping",
            "req_id": str(self.req_id)
        }
        
        await self.websocket.send(json.dumps(ping_msg))
        self.req_id += 1
        logger.debug("Sent ping to Bybit WebSocket")
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message from Bybit WebSocket"""
        try:
            # Handle different message types
            if 'op' in message:
                op = message.get('op')
                if op == 'subscribe':
                    if message.get('success'):
                        logger.info(f"Successfully subscribed to: {message.get('args', [])}")
                    else:
                        logger.error(f"Subscription failed: {message.get('ret_msg', 'Unknown error')}")
                elif op == 'unsubscribe':
                    if message.get('success'):
                        logger.info(f"Successfully unsubscribed from: {message.get('args', [])}")
                    else:
                        logger.error(f"Unsubscription failed: {message.get('ret_msg', 'Unknown error')}")
                elif op == 'pong':
                    logger.debug("Received pong from Bybit WebSocket")
                elif op == 'ping':
                    logger.debug("Received ping from Bybit WebSocket")
                    # Optionally, respond with pong if Bybit expects it:
                    # await self.websocket.send(json.dumps({"op": "pong", "req_id": str(self.req_id)}))
                    # self.req_id += 1
                else:
                    logger.debug(f"Ignoring unknown operation: {op}")
            
            # --- Real-time kline handler for rolling volatility ---
            elif 'topic' in message and 'data' in message:
                topic = message['topic']
                data = message['data']
                # Example topic: kline.1.BTCUSDT
                if topic.startswith('kline.1.') and isinstance(data, list) and len(data) > 0:
                    kline = data[-1]  # Use the latest kline
                    symbol = topic.split('.')[-1]
                    close_price = float(kline['close']) if isinstance(kline, dict) and 'close' in kline else None
                    if close_price is not None:
                        if symbol == 'BTCUSDT':
                            vol = self.btc_vol_calc.update(close_price)
                            if vol is not None:
                                ts = int(kline['start']) if 'start' in kline else int(time.time())
                                conn = sqlite3.connect('data/crypto_data.db')
                                c = conn.cursor()
                                c.execute('''
                                    INSERT INTO crypto_volatility (symbol, timestamp, window_minutes, volatility)
                                    VALUES (?, ?, ?, ?)
                                ''', ('BTCUSDT_BYBIT', ts, 15, vol))
                                conn.commit()
                                conn.close()
                        elif symbol == 'ETHUSDT':
                            vol = self.eth_vol_calc.update(close_price)
                            if vol is not None:
                                ts = int(kline['start']) if 'start' in kline else int(time.time())
                                conn = sqlite3.connect('data/crypto_data.db')
                                c = conn.cursor()
                                c.execute('''
                                    INSERT INTO crypto_volatility (symbol, timestamp, window_minutes, volatility)
                                    VALUES (?, ?, ?, ?)
                                ''', ('ETHUSDT_BYBIT', ts, 15, vol))
                                conn.commit()
                                conn.close()
                # This is actual market data
                if self.message_handler:
                    await self.message_handler(message)
            
            # Handle connection-related messages
            elif 'ret_msg' in message:
                logger.info(f"Bybit WebSocket message: {message.get('ret_msg')}")
            
            else:
                # Unknown message format
                logger.debug(f"Received unknown message format: {message}")
                
        except Exception as e:
            logger.error(f"Error handling Bybit message: {e}")
    
    async def listen(self) -> None:
        """Listen for messages with periodic ping"""
        try:
            # Start ping task
            ping_task = asyncio.create_task(self._ping_loop())
            
            try:
                async for message in self.websocket:
                    parsed_message = parse_websocket_message(message)
                    if parsed_message:
                        await self.handle_message(parsed_message)
            finally:
                ping_task.cancel()
                try:
                    await ping_task
                except asyncio.CancelledError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Bybit WebSocket connection closed")
            self.is_connected = False
            await self.reconnect()
        except Exception as e:
            logger.error(f"Error in Bybit WebSocket listener: {e}")
            await self.reconnect()
    
    async def _ping_loop(self) -> None:
        """Send periodic pings to maintain connection"""
        try:
            while self.is_connected:
                await asyncio.sleep(20)  # Ping every 20 seconds
                if self.is_connected:
                    await self.ping()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in ping loop: {e}")
    
    async def reconnect(self) -> None:
        """Reconnect with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached for Bybit WebSocket")
            return
            
        self.reconnect_attempts += 1
        await exponential_backoff(self.reconnect_attempts)
        
        try:
            await self.connect()
            if self.subscriptions:
                await self.subscribe(self.subscriptions)
        except Exception as e:
            logger.error(f"Bybit reconnection attempt {self.reconnect_attempts} failed: {e}")
            await self.reconnect()
    
    def create_orderbook_channel(self, symbol: str, depth: int = 25) -> str:
        """Create order book channel name for symbol"""
        # Bybit v5 order book channel format
        return f"orderbook.{depth}.{symbol.upper()}"
    
    def create_ticker_channel(self, symbol: str) -> str:
        """Create ticker channel name for symbol"""
        return f"tickers.{symbol.upper()}"
    
    def create_trade_channel(self, symbol: str) -> str:
        """Create trade channel name for symbol"""
        return f"publicTrade.{symbol.upper()}"
    
    def create_kline_channel(self, symbol: str, interval: str = "1") -> str:
        """Create kline channel name for symbol"""
        return f"kline.{interval}.{symbol.upper()}" 
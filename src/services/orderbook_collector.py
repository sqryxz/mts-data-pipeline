import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from src.api.binance_client import BinanceClient
from src.api.websockets.binance_websocket import BinanceWebSocket
from src.realtime.orderbook_processor import OrderBookProcessor
from src.services.spread_calculator import SpreadCalculator
from src.data.redis_helper import RedisHelper
from src.data.realtime_storage import RealtimeStorage
from config.realtime.orderbook_config import ORDERBOOK_CONFIG

logger = logging.getLogger(__name__)

class OrderBookCollector:
    def __init__(self, storage: Optional[RealtimeStorage] = None):
        self.binance_client = BinanceClient()
        self.processor = OrderBookProcessor()
        self.spread_calculator = SpreadCalculator()
        self.redis_helper = RedisHelper()
        # Add RealtimeStorage for persistent data
        self.storage = storage if storage else RealtimeStorage()
        self.websocket_clients = {}
        self.is_running = False
        
    async def start_collection(self, symbols: List[str]) -> None:
        """Start order book collection for symbols"""
        try:
            # Connect to Redis
            if not self.redis_helper.connect():
                raise Exception("Failed to connect to Redis")
            
            self.is_running = True
            
            # Start WebSocket collection for each symbol
            tasks = []
            for symbol in symbols:
                task = asyncio.create_task(self._collect_symbol_orderbook(symbol))
                tasks.append(task)
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Failed to start order book collection: {e}")
            self.is_running = False
    
    async def _collect_symbol_orderbook(self, symbol: str) -> None:
        """Collect order book data for a specific symbol"""
        try:
            # Create WebSocket client for this symbol
            websocket = BinanceWebSocket(message_handler=self._handle_orderbook_message)
            
            # Connect and subscribe
            await websocket.connect()
            
            # Subscribe to order book stream
            stream_name = f"{symbol.lower()}@depth{ORDERBOOK_CONFIG['depth_levels']}@{ORDERBOOK_CONFIG['update_frequency']}ms"
            await websocket.subscribe([stream_name])
            
            # Store websocket reference
            self.websocket_clients[symbol] = websocket
            
            # Listen for messages
            await websocket.listen()
            
        except Exception as e:
            logger.error(f"Failed to collect order book for {symbol}: {e}")
    
    async def _handle_orderbook_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming order book message"""
        try:
            # Extract symbol from stream name
            stream = message.get('stream', '')
            if '@depth' not in stream:
                return
                
            symbol = stream.split('@')[0].upper()
            data = message.get('data', {})
            
            if not data:
                return
            
            # Process order book data
            orderbook = self.processor.process_binance_orderbook(data, symbol)
            
            if orderbook and self.processor.validate_orderbook(orderbook):
                # Calculate spread
                spread = self.spread_calculator.calculate_spread(orderbook)
                
                if spread:
                    # Store in Redis for real-time access
                    redis_key = f"orderbook:{orderbook.exchange}:{orderbook.symbol}"
                    orderbook_data = {
                        'exchange': orderbook.exchange,
                        'symbol': orderbook.symbol,
                        'timestamp': orderbook.timestamp,
                        'best_bid': orderbook.get_best_bid().price if orderbook.get_best_bid() else None,
                        'best_ask': orderbook.get_best_ask().price if orderbook.get_best_ask() else None,
                        'spread_absolute': spread.spread_absolute,
                        'spread_percentage': spread.spread_percentage,
                        'mid_price': spread.mid_price
                    }
                    
                    self.redis_helper.set_json(redis_key, orderbook_data, ttl=ORDERBOOK_CONFIG['storage']['redis_ttl'])
                    
                    # Store in database for persistence
                    try:
                        self.storage.store_orderbook_snapshot(orderbook, csv_backup=ORDERBOOK_CONFIG['storage']['csv_backup'])
                        self.storage.store_spread(spread, csv_backup=ORDERBOOK_CONFIG['storage']['csv_backup'])
                    except Exception as storage_error:
                        logger.error(f"Failed to store order book data persistently: {storage_error}")
                        # Continue processing - Redis storage succeeded
                    
                    logger.debug(f"Stored order book data for {symbol}: spread={spread.spread_percentage:.4f}%")
            
        except Exception as e:
            logger.error(f"Error handling order book message: {e}")
    
    async def stop_collection(self) -> None:
        """Stop order book collection"""
        try:
            self.is_running = False
            
            # Close all websocket connections
            for symbol, websocket in self.websocket_clients.items():
                try:
                    await websocket.disconnect()
                    logger.info(f"Disconnected WebSocket for {symbol}")
                except Exception as e:
                    logger.error(f"Error disconnecting WebSocket for {symbol}: {e}")
            
            self.websocket_clients.clear()
            logger.info("Order book collection stopped")
            
        except Exception as e:
            logger.error(f"Error stopping order book collection: {e}")
    
    def get_latest_orderbook(self, exchange: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest order book data from Redis"""
        try:
            redis_key = f"orderbook:{exchange}:{symbol}"
            return self.redis_helper.get_json(redis_key)
        except Exception as e:
            logger.error(f"Error retrieving order book from Redis: {e}")
            return None 
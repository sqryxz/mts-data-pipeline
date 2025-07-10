import logging
from typing import Dict, Any, List, Optional
from src.data.realtime_models import OrderBookSnapshot, OrderBookLevel
import time

logger = logging.getLogger(__name__)

class OrderBookProcessor:
    def __init__(self):
        self.last_update_id = {}
        
    def process_binance_orderbook(self, data: Dict[str, Any], symbol: str) -> Optional[OrderBookSnapshot]:
        """Process Binance order book data"""
        try:
            # Extract bids and asks
            bids_data = data.get('bids', [])
            asks_data = data.get('asks', [])
            
            # Convert to OrderBookLevel objects
            bids = []
            for i, (price, quantity) in enumerate(bids_data[:10]):  # Top 10 levels
                bids.append(OrderBookLevel(
                    price=float(price),
                    quantity=float(quantity),
                    level=i
                ))
            
            asks = []
            for i, (price, quantity) in enumerate(asks_data[:10]):  # Top 10 levels
                asks.append(OrderBookLevel(
                    price=float(price),
                    quantity=float(quantity),
                    level=i
                ))
            
            # Create snapshot
            snapshot = OrderBookSnapshot(
                exchange='binance',
                symbol=symbol,
                timestamp=int(time.time() * 1000),  # Current timestamp in ms
                bids=bids,
                asks=asks
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to process Binance order book for {symbol}: {e}")
            return None
    
    def process_bybit_orderbook(self, data: Dict[str, Any], symbol: str) -> Optional[OrderBookSnapshot]:
        """Process Bybit order book data from WebSocket"""
        try:
            # Bybit WebSocket data structure
            if 'topic' in data and 'data' in data:
                orderbook_data = data['data']
                timestamp = data.get('ts', int(time.time() * 1000))
                
                # Extract bids and asks from Bybit format
                bids_data = orderbook_data.get('b', [])  # 'b' for bids
                asks_data = orderbook_data.get('a', [])  # 'a' for asks
                
                # Convert to OrderBookLevel objects
                bids = []
                for i, bid_item in enumerate(bids_data[:10]):  # Top 10 levels
                    if len(bid_item) >= 2:
                        bids.append(OrderBookLevel(
                            price=float(bid_item[0]),
                            quantity=float(bid_item[1]),
                            level=i
                        ))
                
                asks = []
                for i, ask_item in enumerate(asks_data[:10]):  # Top 10 levels
                    if len(ask_item) >= 2:
                        asks.append(OrderBookLevel(
                            price=float(ask_item[0]),
                            quantity=float(ask_item[1]),
                            level=i
                        ))
                
                # Create snapshot
                snapshot = OrderBookSnapshot(
                    exchange='bybit',
                    symbol=symbol,
                    timestamp=timestamp,
                    bids=bids,
                    asks=asks
                )
                
                return snapshot
            
            # Handle REST API response format
            elif 'b' in data and 'a' in data:
                # Direct REST API format
                bids_data = data.get('b', [])
                asks_data = data.get('a', [])
                timestamp = data.get('ts', int(time.time() * 1000))
                
                # Convert to OrderBookLevel objects
                bids = []
                for i, bid_item in enumerate(bids_data[:10]):
                    if len(bid_item) >= 2:
                        bids.append(OrderBookLevel(
                            price=float(bid_item[0]),
                            quantity=float(bid_item[1]),
                            level=i
                        ))
                
                asks = []
                for i, ask_item in enumerate(asks_data[:10]):
                    if len(ask_item) >= 2:
                        asks.append(OrderBookLevel(
                            price=float(ask_item[0]),
                            quantity=float(ask_item[1]),
                            level=i
                        ))
                
                # Create snapshot
                snapshot = OrderBookSnapshot(
                    exchange='bybit',
                    symbol=symbol,
                    timestamp=timestamp,
                    bids=bids,
                    asks=asks
                )
                
                return snapshot
            
            else:
                logger.warning(f"Unknown Bybit order book format: {list(data.keys())}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to process Bybit order book for {symbol}: {e}")
            return None
    
    def process_orderbook(self, data: Dict[str, Any], symbol: str, exchange: str) -> Optional[OrderBookSnapshot]:
        """Process order book data for any supported exchange"""
        if exchange.lower() == 'binance':
            return self.process_binance_orderbook(data, symbol)
        elif exchange.lower() == 'bybit':
            return self.process_bybit_orderbook(data, symbol)
        else:
            logger.error(f"Unsupported exchange: {exchange}")
            return None
    
    def validate_orderbook(self, snapshot: OrderBookSnapshot) -> bool:
        """Validate order book data"""
        try:
            # Check if we have data
            if not snapshot.bids or not snapshot.asks:
                return False
            
            # Check if best bid < best ask (no crossed market)
            best_bid = snapshot.get_best_bid()
            best_ask = snapshot.get_best_ask()
            
            if best_bid and best_ask:
                if best_bid.price >= best_ask.price:
                    logger.warning(f"Crossed market detected: bid={best_bid.price}, ask={best_ask.price}")
                    return False
            
            # Check for reasonable prices (basic sanity check)
            for bid in snapshot.bids:
                if bid.price <= 0 or bid.quantity <= 0:
                    return False
                    
            for ask in snapshot.asks:
                if ask.price <= 0 or ask.quantity <= 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating order book: {e}")
            return False 
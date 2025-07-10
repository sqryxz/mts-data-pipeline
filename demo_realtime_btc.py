#!/usr/bin/env python3
"""
Demo script for real-time BTC order book and funding rate collection.
This script collects current BTC market data from Binance and outputs a JSON snippet.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our pipeline components
from src.api.binance_client import BinanceClient
from src.services.funding_collector import FundingCollector
from src.realtime.orderbook_processor import OrderBookProcessor
from src.data.realtime_storage import RealtimeStorage
from config.settings import Config


class RealtimeBTCDemo:
    """
    Demo class for collecting real-time BTC orderbook and funding rate data.
    """
    
    def __init__(self):
        self.config = Config()
        self.binance_client = BinanceClient()
        self.orderbook_processor = OrderBookProcessor()
        self.storage = RealtimeStorage()
        self.funding_collector = FundingCollector(storage=self.storage)
        
        # Symbol to collect
        self.symbol = "BTCUSDT"
        
        logger.info("RealtimeBTCDemo initialized")
    
    async def collect_orderbook_data(self) -> Optional[Dict[str, Any]]:
        """
        Collect current BTC orderbook data from Binance.
        
        Returns:
            Dictionary with orderbook data or None if failed
        """
        try:
            logger.info(f"Collecting order book data for {self.symbol}...")
            
            # Get order book data from Binance REST API
            raw_orderbook = self.binance_client.get_order_book(self.symbol, limit=10)
            
            if not raw_orderbook:
                logger.error("Failed to get order book data from Binance")
                return None
            
            # Process the order book data
            orderbook_snapshot = self.orderbook_processor.process_binance_orderbook(raw_orderbook, self.symbol)
            
            if not orderbook_snapshot:
                logger.error("Failed to process order book data")
                return None
            
            # Format for JSON output
            orderbook_data = {
                "exchange": orderbook_snapshot.exchange,
                "symbol": orderbook_snapshot.symbol,
                "timestamp": orderbook_snapshot.timestamp,
                "timestamp_iso": datetime.fromtimestamp(orderbook_snapshot.timestamp / 1000, tz=timezone.utc).isoformat(),
                "bids": [
                    {
                        "level": bid.level,
                        "price": bid.price,
                        "quantity": bid.quantity
                    }
                    for bid in orderbook_snapshot.bids[:5]  # At least 5 levels
                ],
                "asks": [
                    {
                        "level": ask.level,
                        "price": ask.price,
                        "quantity": ask.quantity
                    }
                    for ask in orderbook_snapshot.asks[:5]  # At least 5 levels
                ],
                "best_bid": orderbook_snapshot.get_best_bid().price if orderbook_snapshot.get_best_bid() else None,
                "best_ask": orderbook_snapshot.get_best_ask().price if orderbook_snapshot.get_best_ask() else None,
                "spread": (orderbook_snapshot.get_best_ask().price - orderbook_snapshot.get_best_bid().price) if orderbook_snapshot.get_best_ask() and orderbook_snapshot.get_best_bid() else None
            }
            
            logger.info(f"Successfully collected order book data: {len(orderbook_data['bids'])} bids, {len(orderbook_data['asks'])} asks")
            return orderbook_data
            
        except Exception as e:
            logger.error(f"Error collecting order book data: {e}")
            return None
    
    async def collect_funding_rate_data(self) -> Optional[Dict[str, Any]]:
        """
        Collect current BTC funding rate data from Binance.
        
        Returns:
            Dictionary with funding rate data or None if failed
        """
        try:
            logger.info(f"Collecting funding rate data for {self.symbol}...")
            
            # Get funding rate data using the funding collector
            funding_rate = await self.funding_collector.collect_single_funding_rate(self.symbol)
            
            if not funding_rate:
                logger.error("Failed to collect funding rate data")
                return None
            
            # Format for JSON output
            funding_data = {
                "exchange": funding_rate.exchange,
                "symbol": funding_rate.symbol,
                "timestamp": funding_rate.timestamp,
                "timestamp_iso": datetime.fromtimestamp(funding_rate.timestamp / 1000, tz=timezone.utc).isoformat(),
                "funding_rate": funding_rate.funding_rate,
                "funding_rate_percentage": funding_rate.funding_rate * 100,
                "predicted_rate": funding_rate.predicted_rate,
                "next_funding_time": funding_rate.funding_time,
                "next_funding_time_iso": datetime.fromtimestamp(funding_rate.funding_time / 1000, tz=timezone.utc).isoformat() if funding_rate.funding_time else None
            }
            
            logger.info(f"Successfully collected funding rate: {funding_rate.funding_rate:.6f} ({funding_rate.funding_rate * 100:.4f}%)")
            return funding_data
            
        except Exception as e:
            logger.error(f"Error collecting funding rate data: {e}")
            return None
    
    async def generate_btc_market_snapshot(self) -> Dict[str, Any]:
        """
        Generate a complete BTC market snapshot with orderbook and funding rate data.
        
        Returns:
            Dictionary with complete market data
        """
        logger.info("Generating BTC market snapshot...")
        
        # Collect both orderbook and funding rate data
        orderbook_data = await self.collect_orderbook_data()
        funding_data = await self.collect_funding_rate_data()
        
        # Create market snapshot
        market_snapshot = {
            "collection_timestamp": int(time.time() * 1000),
            "collection_timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "symbol": self.symbol,
            "market_data": {
                "orderbook": orderbook_data,
                "funding_rate": funding_data
            },
            "status": {
                "orderbook_available": orderbook_data is not None,
                "funding_rate_available": funding_data is not None,
                "complete": orderbook_data is not None and funding_data is not None
            }
        }
        
        return market_snapshot
    
    def format_json_output(self, data: Dict[str, Any]) -> str:
        """
        Format the data as pretty JSON string.
        
        Args:
            data: Dictionary to format
            
        Returns:
            Pretty-formatted JSON string
        """
        return json.dumps(data, indent=2, default=str)


async def main():
    """Main function to run the demo"""
    print("=" * 80)
    print("MTS Real-Time BTC Market Data Demo")
    print("=" * 80)
    print()
    
    # Generate filename first
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"btc_market_snapshot_{timestamp_str}.json"
    
    try:
        # Initialize demo
        demo = RealtimeBTCDemo()
        
        # Generate market snapshot
        market_snapshot = await demo.generate_btc_market_snapshot()
        
        # Output JSON snippet
        json_output = demo.format_json_output(market_snapshot)
        
        # Save JSON to file
        
        with open(json_filename, 'w') as f:
            f.write(json_output)
        
        print("BTC Market Snapshot JSON:")
        print("-" * 40)
        print(json_output)
        print("-" * 40)
        print(f"\n📄 JSON saved to: {json_filename}")
        
        # Summary
        print("\nSummary:")
        if market_snapshot["status"]["complete"]:
            orderbook = market_snapshot["market_data"]["orderbook"]
            funding = market_snapshot["market_data"]["funding_rate"]
            
            print(f"Symbol: {orderbook['symbol']}")
            print(f"Exchange: {orderbook['exchange']}")
            print(f"Best Bid: ${orderbook['best_bid']:,.2f}")
            print(f"Best Ask: ${orderbook['best_ask']:,.2f}")
            print(f"Spread: ${orderbook['spread']:.2f}")
            print(f"Funding Rate: {funding['funding_rate_percentage']:.4f}%")
            print(f"Bid/Ask Levels: {len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks")
            print(f"JSON File: {json_filename}")
        else:
            print("⚠️  Incomplete data collection")
            if not market_snapshot["status"]["orderbook_available"]:
                print("   - Order book data failed")
            if not market_snapshot["status"]["funding_rate_available"]:
                print("   - Funding rate data failed")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the demo
    exit_code = asyncio.run(main())
    exit(exit_code) 
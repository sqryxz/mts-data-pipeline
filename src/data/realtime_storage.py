"""
Real-time data storage helper for order book, spread, and funding rate data.
Provides unified interface for storing real-time market data with both SQLite and CSV backup.
"""

import csv
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Set, Optional
from .db_connection import DatabaseConnection
from .realtime_models import OrderBookSnapshot, BidAskSpread, FundingRate
import time


class RealtimeStorage:
    """
    Real-time data storage handler for order book, spread, and funding rate data.
    Supports both SQLite database and CSV backup storage.
    """
    
    def __init__(self, db_path: Optional[str] = None, csv_dir: str = "data/realtime"):
        """
        Initialize the RealtimeStorage helper.
        
        Args:
            db_path: Optional path to SQLite database file
            csv_dir: Directory for CSV backup files
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up database connection
        self.db_connection = DatabaseConnection(db_path) if db_path else DatabaseConnection()
        self.db_path = self.db_connection.db_path
        
        # Set up CSV directory
        self.csv_dir = csv_dir
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(os.path.join(self.csv_dir, "orderbooks"), exist_ok=True)
        os.makedirs(os.path.join(self.csv_dir, "spreads"), exist_ok=True)
        os.makedirs(os.path.join(self.csv_dir, "funding"), exist_ok=True)
        
        # Initialize database tables
        self._initialize_realtime_tables()
        
        self.logger.info(f"RealtimeStorage initialized with database: {self.db_path}")
    
    def _initialize_realtime_tables(self) -> None:
        """Initialize real-time tables using enhanced schema."""
        try:
            # Read enhanced schema
            schema_path = os.path.join(os.path.dirname(__file__), "enhanced_schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                with self.db_connection.get_connection() as conn:
                    conn.executescript(schema_sql)
                    conn.commit()
                
                self.logger.debug("Real-time database tables initialized successfully")
            else:
                self.logger.warning("Enhanced schema file not found, skipping table initialization")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize real-time tables: {e}")
            raise
    
    def store_orderbook_snapshot(self, orderbook: OrderBookSnapshot, csv_backup: bool = True) -> int:
        """
        Store order book snapshot to database and optionally CSV.
        
        Args:
            orderbook: OrderBookSnapshot object to store
            csv_backup: Whether to also save to CSV backup
            
        Returns:
            int: Number of order book levels stored
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        if not orderbook.bids and not orderbook.asks:
            self.logger.debug("Empty order book snapshot, skipping storage")
            return 0
        
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = """
                    INSERT OR REPLACE INTO order_book 
                    (exchange, symbol, timestamp, side, level, price, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                inserted_count = 0
                
                # Insert bid levels
                for bid in orderbook.bids:
                    cursor.execute(insert_sql, (
                        orderbook.exchange,
                        orderbook.symbol,
                        orderbook.timestamp,
                        'bid',
                        bid.level,
                        bid.price,
                        bid.quantity
                    ))
                    inserted_count += 1
                
                # Insert ask levels
                for ask in orderbook.asks:
                    cursor.execute(insert_sql, (
                        orderbook.exchange,
                        orderbook.symbol,
                        orderbook.timestamp,
                        'ask',
                        ask.level,
                        ask.price,
                        ask.quantity
                    ))
                    inserted_count += 1
                
                conn.commit()
                
                self.logger.debug(f"Stored {inserted_count} order book levels for {orderbook.symbol}")
                
                # CSV backup if requested
                if csv_backup:
                    self._save_orderbook_csv(orderbook)
                
                return inserted_count
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store order book snapshot: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error storing order book: {e}")
            raise
    
    def store_bid_ask_spread(self, spread: BidAskSpread, csv_backup: bool = True) -> bool:
        """
        Store bid-ask spread data to database and optionally CSV.
        
        Args:
            spread: BidAskSpread object to store
            csv_backup: Whether to also save to CSV backup
            
        Returns:
            bool: True if stored successfully, False otherwise
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = """
                    INSERT OR REPLACE INTO bid_ask_spreads 
                    (exchange, symbol, timestamp, bid_price, ask_price, 
                     spread_absolute, spread_percentage, mid_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_sql, (
                    spread.exchange,
                    spread.symbol,
                    spread.timestamp,
                    spread.bid_price,
                    spread.ask_price,
                    spread.spread_absolute,
                    spread.spread_percentage,
                    spread.mid_price
                ))
                
                conn.commit()
                
                self.logger.debug(f"Stored spread data for {spread.symbol}: {spread.spread_percentage:.4f}%")
                
                # CSV backup if requested
                if csv_backup:
                    self._save_spread_csv(spread)
                
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store spread data: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error storing spread: {e}")
            raise
    
    def store_funding_rate(self, funding_rate: FundingRate, csv_backup: bool = True) -> bool:
        """
        Store funding rate data to database and optionally CSV.
        
        Args:
            funding_rate: FundingRate object to store
            csv_backup: Whether to also save to CSV backup
            
        Returns:
            bool: True if stored successfully, False otherwise
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = """
                    INSERT OR REPLACE INTO funding_rates 
                    (exchange, symbol, timestamp, funding_rate, predicted_rate, funding_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_sql, (
                    funding_rate.exchange,
                    funding_rate.symbol,
                    funding_rate.timestamp,
                    funding_rate.funding_rate,
                    funding_rate.predicted_rate,
                    funding_rate.funding_time
                ))
                
                conn.commit()
                
                self.logger.debug(f"Stored funding rate for {funding_rate.symbol}: {funding_rate.funding_rate:.6f}")
                
                # CSV backup if requested
                if csv_backup:
                    self._save_funding_csv(funding_rate)
                
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store funding rate: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error storing funding rate: {e}")
            raise
    
    def batch_store_orderbooks(self, orderbooks: List[OrderBookSnapshot], csv_backup: bool = True) -> int:
        """
        Store multiple order book snapshots in batch for better performance.
        
        Args:
            orderbooks: List of OrderBookSnapshot objects to store
            csv_backup: Whether to also save to CSV backup
            
        Returns:
            int: Total number of order book levels stored
        """
        if not orderbooks:
            return 0
        
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = """
                    INSERT OR REPLACE INTO order_book 
                    (exchange, symbol, timestamp, side, level, price, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                batch_data = []
                for orderbook in orderbooks:
                    # Add bid levels
                    for bid in orderbook.bids:
                        batch_data.append((
                            orderbook.exchange, orderbook.symbol, orderbook.timestamp,
                            'bid', bid.level, bid.price, bid.quantity
                        ))
                    
                    # Add ask levels
                    for ask in orderbook.asks:
                        batch_data.append((
                            orderbook.exchange, orderbook.symbol, orderbook.timestamp,
                            'ask', ask.level, ask.price, ask.quantity
                        ))
                
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
                
                stored_count = len(batch_data)
                self.logger.debug(f"Batch stored {stored_count} order book levels from {len(orderbooks)} snapshots")
                
                # CSV backup if requested
                if csv_backup:
                    for orderbook in orderbooks:
                        self._save_orderbook_csv(orderbook)
                
                return stored_count
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to batch store order books: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in batch storage: {e}")
            raise
    
    def batch_store_spreads(self, spreads: List[BidAskSpread], csv_backup: bool = True) -> int:
        """
        Store multiple spread records in batch for better performance.
        
        Args:
            spreads: List of BidAskSpread objects to store
            csv_backup: Whether to also save to CSV backup
            
        Returns:
            int: Number of spread records stored
        """
        if not spreads:
            return 0
        
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = """
                    INSERT OR REPLACE INTO bid_ask_spreads 
                    (exchange, symbol, timestamp, bid_price, ask_price, 
                     spread_absolute, spread_percentage, mid_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                batch_data = []
                for spread in spreads:
                    batch_data.append((
                        spread.exchange, spread.symbol, spread.timestamp,
                        spread.bid_price, spread.ask_price, spread.spread_absolute,
                        spread.spread_percentage, spread.mid_price
                    ))
                
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
                
                self.logger.debug(f"Batch stored {len(spreads)} spread records")
                
                # CSV backup if requested
                if csv_backup:
                    for spread in spreads:
                        self._save_spread_csv(spread)
                
                return len(spreads)
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to batch store spreads: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in batch spread storage: {e}")
            raise
    
    def get_latest_orderbook(self, exchange: str, symbol: str) -> Optional[OrderBookSnapshot]:
        """
        Retrieve the latest order book snapshot from database.
        
        Args:
            exchange: Exchange name (e.g., 'binance')
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            OrderBookSnapshot if found, None otherwise
        """
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get latest timestamp
                cursor.execute("""
                    SELECT MAX(timestamp) FROM order_book 
                    WHERE exchange = ? AND symbol = ?
                """, (exchange, symbol))
                
                result = cursor.fetchone()
                if not result or not result[0]:
                    return None
                
                latest_timestamp = result[0]
                
                # Get all levels for latest timestamp
                cursor.execute("""
                    SELECT side, level, price, quantity 
                    FROM order_book 
                    WHERE exchange = ? AND symbol = ? AND timestamp = ?
                    ORDER BY side, level
                """, (exchange, symbol, latest_timestamp))
                
                rows = cursor.fetchall()
                if not rows:
                    return None
                
                # Separate bids and asks
                from .realtime_models import OrderBookLevel
                bids = []
                asks = []
                
                for row in rows:
                    side, level, price, quantity = row
                    order_level = OrderBookLevel(price=price, quantity=quantity, level=level)
                    
                    if side == 'bid':
                        bids.append(order_level)
                    else:
                        asks.append(order_level)
                
                return OrderBookSnapshot(
                    exchange=exchange,
                    symbol=symbol,
                    timestamp=latest_timestamp,
                    bids=bids,
                    asks=asks
                )
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve latest order book: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving order book: {e}")
            return None
    
    def get_latest_spread(self, exchange: str, symbol: str) -> Optional[BidAskSpread]:
        """
        Retrieve the latest spread data from database.
        
        Args:
            exchange: Exchange name (e.g., 'binance')
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            BidAskSpread if found, None otherwise
        """
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT timestamp, bid_price, ask_price, spread_absolute, 
                           spread_percentage, mid_price
                    FROM bid_ask_spreads 
                    WHERE exchange = ? AND symbol = ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (exchange, symbol))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                timestamp, bid_price, ask_price, spread_absolute, spread_percentage, mid_price = row
                
                return BidAskSpread(
                    exchange=exchange,
                    symbol=symbol,
                    timestamp=timestamp,
                    bid_price=bid_price,
                    ask_price=ask_price,
                    spread_absolute=spread_absolute,
                    spread_percentage=spread_percentage,
                    mid_price=mid_price
                )
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve latest spread: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving spread: {e}")
            return None
    
    def _save_orderbook_csv(self, orderbook: OrderBookSnapshot) -> None:
        """Save order book snapshot to CSV backup."""
        try:
            # Create filename based on exchange and symbol
            date_str = datetime.fromtimestamp(orderbook.timestamp / 1000).strftime('%Y%m%d')
            filename = f"{orderbook.exchange}_{orderbook.symbol}_orderbook_{date_str}.csv"
            filepath = os.path.join(self.csv_dir, "orderbooks", filename)
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(filepath)
            
            with open(filepath, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header if file is new
                if not file_exists:
                    writer.writerow(['timestamp', 'side', 'level', 'price', 'quantity'])
                
                # Write bid levels
                for bid in orderbook.bids:
                    writer.writerow([orderbook.timestamp, 'bid', bid.level, bid.price, bid.quantity])
                
                # Write ask levels
                for ask in orderbook.asks:
                    writer.writerow([orderbook.timestamp, 'ask', ask.level, ask.price, ask.quantity])
                    
        except Exception as e:
            self.logger.error(f"Failed to save order book CSV: {e}")
    
    def _save_spread_csv(self, spread: BidAskSpread) -> None:
        """Save spread data to CSV backup."""
        try:
            # Create filename based on exchange and symbol
            date_str = datetime.fromtimestamp(spread.timestamp / 1000).strftime('%Y%m%d')
            filename = f"{spread.exchange}_{spread.symbol}_spreads_{date_str}.csv"
            filepath = os.path.join(self.csv_dir, "spreads", filename)
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(filepath)
            
            with open(filepath, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header if file is new
                if not file_exists:
                    writer.writerow(['timestamp', 'bid_price', 'ask_price', 'spread_absolute', 
                                   'spread_percentage', 'mid_price'])
                
                writer.writerow([
                    spread.timestamp, spread.bid_price, spread.ask_price,
                    spread.spread_absolute, spread.spread_percentage, spread.mid_price
                ])
                    
        except Exception as e:
            self.logger.error(f"Failed to save spread CSV: {e}")
    
    def _save_funding_csv(self, funding_rate: FundingRate) -> None:
        """Save funding rate data to CSV backup."""
        try:
            # Create filename based on exchange and symbol
            date_str = datetime.fromtimestamp(funding_rate.timestamp / 1000).strftime('%Y%m%d')
            filename = f"{funding_rate.exchange}_{funding_rate.symbol}_funding_{date_str}.csv"
            filepath = os.path.join(self.csv_dir, "funding", filename)
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(filepath)
            
            with open(filepath, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header if file is new
                if not file_exists:
                    writer.writerow(['timestamp', 'funding_rate', 'predicted_rate', 'funding_time'])
                
                writer.writerow([
                    funding_rate.timestamp, funding_rate.funding_rate,
                    funding_rate.predicted_rate, funding_rate.funding_time
                ])
                    
        except Exception as e:
            self.logger.error(f"Failed to save funding rate CSV: {e}")
    
    def get_realtime_health_status(self) -> Dict:
        """
        Get health status of real-time data storage.
        
        Returns:
            Dict containing health metrics
        """
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Count records in each table
                cursor.execute("SELECT COUNT(*) FROM order_book")
                orderbook_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM bid_ask_spreads")
                spreads_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM funding_rates")
                funding_count = cursor.fetchone()[0]
                
                # Get latest timestamps
                cursor.execute("SELECT MAX(timestamp) FROM order_book")
                latest_orderbook = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(timestamp) FROM bid_ask_spreads")
                latest_spread = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(timestamp) FROM funding_rates")
                latest_funding = cursor.fetchone()[0]
                
                return {
                    'status': 'healthy',
                    'database_path': self.db_path,
                    'csv_directory': self.csv_dir,
                    'record_counts': {
                        'order_book_levels': orderbook_count,
                        'spread_records': spreads_count,
                        'funding_records': funding_count
                    },
                    'latest_timestamps': {
                        'order_book': latest_orderbook,
                        'spreads': latest_spread,
                        'funding': latest_funding
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_path': self.db_path,
                'csv_directory': self.csv_dir
            } 
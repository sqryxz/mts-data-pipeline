"""
Funding rate collector for perpetual futures contracts.
Collects funding rates from exchanges and stores them for analysis and arbitrage detection.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.api.binance_client import BinanceClient
from src.data.realtime_storage import RealtimeStorage
from src.data.realtime_models import FundingRate
from config.realtime.funding_config import FUNDING_CONFIG


logger = logging.getLogger(__name__)


class FundingCollector:
    """
    Funding rate collector for perpetual futures contracts.
    Collects funding rates from exchanges at regular intervals and stores them for analysis.
    """
    
    def __init__(self, storage: Optional[RealtimeStorage] = None):
        """
        Initialize the FundingCollector.
        
        Args:
            storage: Optional RealtimeStorage instance. Creates new one if None.
        """
        self.binance_client = BinanceClient()
        self.storage = storage if storage else RealtimeStorage()
        self.is_running = False
        self.collection_task = None
        
        # Cache for tracking rate changes
        self.last_rates = {}
        
        logger.info("FundingCollector initialized")
    
    async def start_collection(self, symbols: Optional[List[str]] = None, 
                             interval: Optional[int] = None) -> None:
        """
        Start automated funding rate collection.
        
        Args:
            symbols: List of symbols to collect. Uses config default if None.
            interval: Collection interval in seconds. Uses config default if None.
        """
        if self.is_running:
            logger.warning("Funding collection is already running")
            return
        
        symbols = symbols or FUNDING_CONFIG['symbols']
        interval = interval or FUNDING_CONFIG['collection_interval']
        
        self.is_running = True
        logger.info(f"Starting funding rate collection for {symbols} every {interval}s")
        
        try:
            self.collection_task = asyncio.create_task(
                self._collection_loop(symbols, interval)
            )
            await self.collection_task
        except asyncio.CancelledError:
            logger.info("Funding rate collection was cancelled")
        except Exception as e:
            logger.error(f"Error in funding rate collection: {e}")
        finally:
            self.is_running = False
    
    async def stop_collection(self) -> None:
        """Stop automated funding rate collection."""
        if not self.is_running:
            logger.debug("Funding collection is not running")
            return
        
        self.is_running = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped funding rate collection")
    
    async def _collection_loop(self, symbols: List[str], interval: int) -> None:
        """Main collection loop."""
        while self.is_running:
            try:
                # Collect funding rates for all symbols
                await self.collect_funding_rates(symbols)
                
                # Wait for next collection
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                # Continue after error, but wait a bit
                await asyncio.sleep(min(interval, 60))
    
    async def collect_funding_rates(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Collect funding rates for specified symbols.
        
        Args:
            symbols: List of trading symbols to collect
            
        Returns:
            Dict mapping symbols to success status
        """
        results = {}
        funding_rates = []
        
        for symbol in symbols:
            try:
                funding_rate = await self._collect_symbol_funding_rate(symbol)
                if funding_rate:
                    funding_rates.append(funding_rate)
                    results[symbol] = True
                    logger.debug(f"Collected funding rate for {symbol}: {funding_rate.funding_rate:.6f}")
                else:
                    results[symbol] = False
                    logger.warning(f"Failed to collect funding rate for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error collecting funding rate for {symbol}: {e}")
                results[symbol] = False
        
        # Store collected rates in batch if we have any
        if funding_rates:
            try:
                await self._store_funding_rates(funding_rates)
                logger.info(f"Successfully stored {len(funding_rates)} funding rates")
            except Exception as e:
                logger.error(f"Failed to store funding rates: {e}")
        
        return results
    
    async def _collect_symbol_funding_rate(self, symbol: str) -> Optional[FundingRate]:
        """
        Collect funding rate for a specific symbol from Binance.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            FundingRate object if successful, None otherwise
        """
        try:
            # Get funding rate data from Binance
            data = self.binance_client.get_funding_rate(symbol)
            
            if not data:
                logger.warning(f"No funding rate data returned for {symbol}")
                return None
            
            # Process the funding rate data
            funding_rate = self._process_binance_funding_data(data, symbol)
            
            # Update cache and check for significant changes
            if funding_rate:
                self._update_rate_cache(symbol, funding_rate)
            
            return funding_rate
            
        except Exception as e:
            logger.error(f"Failed to collect funding rate for {symbol}: {e}")
            return None
    
    def _process_binance_funding_data(self, data: Dict[str, Any], symbol: str) -> Optional[FundingRate]:
        """
        Process raw Binance funding rate data into FundingRate object.
        
        Args:
            data: Raw data from Binance API
            symbol: Trading symbol
            
        Returns:
            FundingRate object if processing successful, None otherwise
        """
        try:
            # Extract funding rate information
            funding_rate = float(data.get('lastFundingRate', 0))
            funding_time = int(data.get('nextFundingTime', 0))
            
            # Binance doesn't provide predicted rate directly, use current rate as approximation
            predicted_rate = funding_rate
            
            # Create timestamp for current collection
            timestamp = int(time.time() * 1000)
            
            return FundingRate(
                exchange='binance',
                symbol=symbol,
                timestamp=timestamp,
                funding_rate=funding_rate,
                predicted_rate=predicted_rate,
                funding_time=funding_time
            )
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to process funding data for {symbol}: {e}")
            logger.debug(f"Raw data: {data}")
            return None
    
    def _update_rate_cache(self, symbol: str, funding_rate: FundingRate) -> None:
        """
        Update the rate cache and log significant changes.
        
        Args:
            symbol: Trading symbol
            funding_rate: New funding rate data
        """
        cache_key = f"{funding_rate.exchange}_{symbol}"
        last_rate = self.last_rates.get(cache_key)
        
        if last_rate:
            rate_change = abs(funding_rate.funding_rate - last_rate.funding_rate)
            change_percentage = (rate_change / abs(last_rate.funding_rate)) * 100 if last_rate.funding_rate != 0 else 0
            
            # Log significant changes (> 10% change or > 0.01% absolute)
            if change_percentage > 10 or rate_change > 0.0001:
                logger.info(f"Significant funding rate change for {symbol}: "
                          f"{last_rate.funding_rate:.6f} -> {funding_rate.funding_rate:.6f} "
                          f"({change_percentage:.1f}% change)")
        
        self.last_rates[cache_key] = funding_rate
    
    async def _store_funding_rates(self, funding_rates: List[FundingRate]) -> None:
        """
        Store funding rates using RealtimeStorage.
        
        Args:
            funding_rates: List of FundingRate objects to store
        """
        try:
            # Use batch storage if we have multiple rates
            if len(funding_rates) == 1:
                self.storage.store_funding_rate(
                    funding_rates[0], 
                    csv_backup=FUNDING_CONFIG['storage']['csv_backup']
                )
            else:
                # Store individually since we don't have batch method for funding rates yet
                for funding_rate in funding_rates:
                    self.storage.store_funding_rate(
                        funding_rate, 
                        csv_backup=FUNDING_CONFIG['storage']['csv_backup']
                    )
                    
        except Exception as e:
            logger.error(f"Failed to store funding rates: {e}")
            raise
    
    def get_latest_funding_rate(self, exchange: str, symbol: str) -> Optional[FundingRate]:
        """
        Get the latest funding rate for a symbol from storage.
        
        Args:
            exchange: Exchange name (e.g., 'binance')
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            Latest FundingRate if found, None otherwise
        """
        try:
            # Use storage to get latest rate
            # Note: This would need to be implemented in RealtimeStorage
            # For now, return from cache
            cache_key = f"{exchange}_{symbol}"
            return self.last_rates.get(cache_key)
            
        except Exception as e:
            logger.error(f"Failed to get latest funding rate for {symbol}: {e}")
            return None
    
    def get_funding_rate_history(self, exchange: str, symbol: str, 
                                hours: int = 24) -> List[FundingRate]:
        """
        Get funding rate history for a symbol.
        
        Args:
            exchange: Exchange name
            symbol: Trading symbol
            hours: Number of hours of history to retrieve
            
        Returns:
            List of FundingRate objects (empty if none found)
        """
        try:
            # This would need to be implemented in RealtimeStorage
            # For now, return empty list
            logger.warning("Funding rate history retrieval not yet implemented")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get funding rate history for {symbol}: {e}")
            return []
    
    def detect_arbitrage_opportunities(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Detect funding rate arbitrage opportunities between exchanges.
        
        Args:
            symbols: List of symbols to check for arbitrage
            
        Returns:
            List of arbitrage opportunity dictionaries
        """
        opportunities = []
        min_rate_diff = FUNDING_CONFIG['arbitrage_thresholds']['min_rate_diff']
        min_profit_bps = FUNDING_CONFIG['arbitrage_thresholds']['min_profit_bps']
        
        try:
            # For now, this is a placeholder since we only have Binance
            # In the future, this would compare rates across multiple exchanges
            logger.debug("Arbitrage detection requires multiple exchanges")
            
            for symbol in symbols:
                binance_rate = self.get_latest_funding_rate('binance', symbol)
                
                if binance_rate:
                    # Placeholder for cross-exchange arbitrage
                    # Would compare with other exchanges when available
                    pass
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error detecting arbitrage opportunities: {e}")
            return []
    
    async def collect_single_funding_rate(self, symbol: str) -> Optional[FundingRate]:
        """
        Collect funding rate for a single symbol (one-time collection).
        
        Args:
            symbol: Trading symbol to collect
            
        Returns:
            FundingRate if successful, None otherwise
        """
        try:
            funding_rate = await self._collect_symbol_funding_rate(symbol)
            
            if funding_rate:
                # Store immediately
                await self._store_funding_rates([funding_rate])
                logger.info(f"Collected and stored funding rate for {symbol}: {funding_rate.funding_rate:.6f}")
            
            return funding_rate
            
        except Exception as e:
            logger.error(f"Failed to collect single funding rate for {symbol}: {e}")
            return None
    
    def get_collection_status(self) -> Dict[str, Any]:
        """
        Get the current status of the funding rate collector.
        
        Returns:
            Dictionary with status information
        """
        return {
            'is_running': self.is_running,
            'configured_symbols': FUNDING_CONFIG['symbols'],
            'collection_interval': FUNDING_CONFIG['collection_interval'],
            'cached_rates_count': len(self.last_rates),
            'cached_symbols': list(set(key.split('_')[1] for key in self.last_rates.keys())),
            'last_collection_times': {
                key.split('_')[1]: rate.timestamp 
                for key, rate in self.last_rates.items()
            }
        }
    
    def calculate_funding_cost(self, funding_rate: float, position_size: float, 
                             hours: int = 8) -> float:
        """
        Calculate the funding cost for a position.
        
        Args:
            funding_rate: Current funding rate (as decimal)
            position_size: Position size in base currency
            hours: Funding interval in hours (default 8 for most exchanges)
            
        Returns:
            Funding cost (positive = pay, negative = receive)
        """
        try:
            # Funding is typically charged every 8 hours
            funding_periods_per_day = 24 / hours
            daily_rate = funding_rate * funding_periods_per_day
            
            # Cost = position_size * funding_rate
            funding_cost = position_size * funding_rate
            
            return funding_cost
            
        except Exception as e:
            logger.error(f"Error calculating funding cost: {e}")
            return 0.0 
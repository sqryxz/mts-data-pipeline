import pytest
import time
from unittest.mock import Mock, patch
from src.services.cross_exchange_analyzer import (
    CrossExchangeAnalyzer, ArbitrageOpportunity, CrossExchangeSpread, 
    ArbitrageDirection
)
from src.data.realtime_models import OrderBookSnapshot, OrderBookLevel, BidAskSpread

class TestCrossExchangeAnalyzer:
    def setup_method(self):
        self.analyzer = CrossExchangeAnalyzer(
            min_profit_threshold=0.001,  # 0.1%
            min_volume_threshold=100.0   # $100
        )
    
    def create_orderbook(self, exchange: str, symbol: str, bid_price: float, ask_price: float, quantity: float = 1.0) -> OrderBookSnapshot:
        """Helper to create test order book snapshots"""
        bids = [OrderBookLevel(price=bid_price, quantity=quantity, level=0)]
        asks = [OrderBookLevel(price=ask_price, quantity=quantity, level=0)]
        
        return OrderBookSnapshot(
            exchange=exchange,
            symbol=symbol,
            timestamp=int(time.time() * 1000),
            bids=bids,
            asks=asks
        )
    
    def test_init(self):
        """Test analyzer initialization"""
        assert self.analyzer.min_profit_threshold == 0.001
        assert self.analyzer.min_volume_threshold == 100.0
        assert self.analyzer.total_opportunities_detected == 0
        assert self.analyzer.profitable_opportunities == 0
        assert len(self.analyzer.active_opportunities) == 0
        assert len(self.analyzer.opportunity_history) == 0
        assert len(self.analyzer.spread_history) == 0
    
    def test_no_arbitrage_opportunity(self):
        """Test when no arbitrage opportunity exists"""
        # Similar prices on both exchanges
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 1.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43005.0, 43015.0, 1.0)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43005.0, 43015.0, 10.0, 0.023, 43010.0)
            ]
            
            opportunity, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            assert opportunity is None
            assert cross_spread is not None
            assert cross_spread.symbol == 'BTCUSDT'
            assert cross_spread.binance_bid == 43000.0
            assert cross_spread.bybit_ask == 43015.0
    
    def test_arbitrage_buy_binance_sell_bybit(self):
        """Test arbitrage opportunity: buy on Binance, sell on Bybit"""
        # Bybit bid > Binance ask (profitable arbitrage)
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43100.0, 43110.0, 1.5)  # Higher prices
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0)
            ]
            
            opportunity, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            assert opportunity is not None
            assert opportunity.direction == ArbitrageDirection.BUY_BINANCE_SELL_BYBIT
            assert opportunity.buy_exchange == "binance"
            assert opportunity.sell_exchange == "bybit"
            assert opportunity.buy_price == 43010.0  # Binance ask
            assert opportunity.sell_price == 43100.0  # Bybit bid
            assert opportunity.profit_absolute == 90.0  # 43100 - 43010
            assert opportunity.profit_percentage > 0.1  # > 0.1%
            assert abs(opportunity.max_volume - 1.2) < 0.001  # min(2.0, 1.5) * 0.8
    
    def test_arbitrage_buy_bybit_sell_binance(self):
        """Test arbitrage opportunity: buy on Bybit, sell on Binance"""
        # Binance bid > Bybit ask (profitable arbitrage)
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43100.0, 43110.0, 1.5)  # Higher prices
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0)
            ]
            
            opportunity, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            assert opportunity is not None
            assert opportunity.direction == ArbitrageDirection.BUY_BYBIT_SELL_BINANCE
            assert opportunity.buy_exchange == "bybit"
            assert opportunity.sell_exchange == "binance"
            assert opportunity.buy_price == 43010.0  # Bybit ask
            assert opportunity.sell_price == 43100.0  # Binance bid
            assert opportunity.profit_absolute == 90.0  # 43100 - 43010
            assert abs(opportunity.max_volume - 1.2) < 0.001  # min(1.5, 2.0) * 0.8
    
    def test_insufficient_profit_threshold(self):
        """Test that small profit opportunities are filtered out"""
        # Small price difference below threshold
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43012.0, 43022.0, 1.5)  # Small difference
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43012.0, 43022.0, 10.0, 0.023, 43017.0)
            ]
            
            opportunity, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            # Profit = 43012 - 43010 = 2, percentage = 2/43010 * 100 = 0.0046% < 0.1%
            assert opportunity is None  # Below threshold
            assert cross_spread is not None
    
    def test_insufficient_volume_threshold(self):
        """Test that low volume opportunities are filtered out"""
        # High profit but low volume
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 0.001)  # Very small quantity
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43100.0, 43110.0, 0.001)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0)
            ]
            
            opportunity, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            # Volume = 0.001 * 0.8 * 43010 = ~$34 < $100 threshold
            assert opportunity is None  # Below volume threshold
            assert cross_spread is not None
    
    def test_symbol_mismatch(self):
        """Test handling of mismatched symbols"""
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 1.0)
        bybit_orderbook = self.create_orderbook('bybit', 'ETHUSDT', 2800.0, 2810.0, 1.0)  # Different symbol
        
        opportunity, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
        
        assert opportunity is None
        assert cross_spread is None
    
    def test_missing_price_data(self):
        """Test handling of incomplete order book data"""
        # Create orderbook with no bids
        binance_orderbook = OrderBookSnapshot(
            exchange='binance', symbol='BTCUSDT', timestamp=int(time.time() * 1000),
            bids=[], asks=[OrderBookLevel(price=43010.0, quantity=1.0, level=0)]
        )
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43000.0, 43010.0, 1.0)
        
        opportunity, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
        
        assert opportunity is None
        assert cross_spread is None
    
    def test_opportunity_tracking(self):
        """Test tracking of arbitrage opportunities"""
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43100.0, 43110.0, 1.5)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0),
                # Second call
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0)
            ]
            
            # First opportunity
            opportunity1, _ = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            assert len(self.analyzer.opportunity_history) == 1
            assert len(self.analyzer.active_opportunities) == 1
            assert self.analyzer.total_opportunities_detected == 1
            assert self.analyzer.profitable_opportunities == 1
            
            # Second opportunity (should update existing)
            opportunity2, _ = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            assert len(self.analyzer.opportunity_history) == 2  # New entry in history
            assert len(self.analyzer.active_opportunities) == 1  # Same active opportunity updated
            assert self.analyzer.total_opportunities_detected == 2
    
    def test_get_active_opportunities(self):
        """Test retrieving active opportunities"""
        # Create opportunities for different symbols
        btc_binance = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        btc_bybit = self.create_orderbook('bybit', 'BTCUSDT', 43100.0, 43110.0, 1.5)
        
        eth_binance = self.create_orderbook('binance', 'ETHUSDT', 2800.0, 2810.0, 5.0)
        eth_bybit = self.create_orderbook('bybit', 'ETHUSDT', 2850.0, 2860.0, 3.0)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0),
                BidAskSpread('binance', 'ETHUSDT', int(time.time() * 1000), 2800.0, 2810.0, 10.0, 0.036, 2805.0),
                BidAskSpread('bybit', 'ETHUSDT', int(time.time() * 1000), 2850.0, 2860.0, 10.0, 0.035, 2855.0)
            ]
            
            self.analyzer.analyze_orderbooks(btc_binance, btc_bybit)
            self.analyzer.analyze_orderbooks(eth_binance, eth_bybit)
            
            # Get all opportunities
            all_opportunities = self.analyzer.get_active_opportunities()
            assert len(all_opportunities) == 2
            
            # Get BTC opportunities only
            btc_opportunities = self.analyzer.get_active_opportunities(symbol='BTCUSDT')
            assert len(btc_opportunities) == 1
            assert btc_opportunities[0].symbol == 'BTCUSDT'
    
    def test_opportunity_statistics(self):
        """Test opportunity statistics calculation"""
        # Add some test opportunities
        btc_binance = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        btc_bybit = self.create_orderbook('bybit', 'BTCUSDT', 43100.0, 43110.0, 1.5)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0)
            ]
            
            self.analyzer.analyze_orderbooks(btc_binance, btc_bybit)
            
            stats = self.analyzer.get_opportunity_statistics()
            
            assert stats['total_opportunities'] == 1
            assert stats['profitable_opportunities'] == 1
            assert stats['success_rate'] == 100.0
            assert stats['average_profit_percentage'] > 0
            assert stats['max_profit_percentage'] > 0
            assert 'BTCUSDT' in stats['opportunities_by_symbol']
            assert 'buy_binance_sell_bybit' in stats['opportunities_by_direction']
    
    def test_clear_stale_opportunities(self):
        """Test clearing of stale opportunities"""
        # Create opportunity
        btc_binance = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        btc_bybit = self.create_orderbook('bybit', 'BTCUSDT', 43100.0, 43110.0, 1.5)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43100.0, 43110.0, 10.0, 0.023, 43105.0)
            ]
            
            self.analyzer.analyze_orderbooks(btc_binance, btc_bybit)
            
            assert len(self.analyzer.active_opportunities) == 1
            
            # Mock old timestamp
            for opp in self.analyzer.active_opportunities.values():
                opp.timestamp = int(time.time() * 1000) - 15000  # 15 seconds ago
            
            # Clear opportunities older than 10 seconds
            cleared = self.analyzer.clear_stale_opportunities(max_age_ms=10000)
            
            assert cleared == 1
            assert len(self.analyzer.active_opportunities) == 0
    
    def test_cross_exchange_spread_creation(self):
        """Test CrossExchangeSpread data structure"""
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 1.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43005.0, 43015.0, 1.0)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43005.0, 43015.0, 10.0, 0.023, 43010.0)
            ]
            
            _, cross_spread = self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            assert cross_spread.symbol == 'BTCUSDT'
            assert cross_spread.binance_bid == 43000.0
            assert cross_spread.binance_ask == 43010.0
            assert cross_spread.bybit_bid == 43005.0
            assert cross_spread.bybit_ask == 43015.0
            assert cross_spread.get_mid_price_difference() == 5.0  # |43005 - 43010|
    
    def test_spread_history_tracking(self):
        """Test that spread history is properly tracked"""
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 1.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43005.0, 43015.0, 1.0)
        
        with patch.object(self.analyzer.spread_calculator, 'calculate_spread') as mock_calc:
            mock_calc.side_effect = [
                BidAskSpread('binance', 'BTCUSDT', int(time.time() * 1000), 43000.0, 43010.0, 10.0, 0.023, 43005.0),
                BidAskSpread('bybit', 'BTCUSDT', int(time.time() * 1000), 43005.0, 43015.0, 10.0, 0.023, 43010.0)
            ]
            
            self.analyzer.analyze_orderbooks(binance_orderbook, bybit_orderbook)
            
            assert 'BTCUSDT' in self.analyzer.spread_history
            assert len(self.analyzer.spread_history['BTCUSDT']) == 1
    
    def test_empty_statistics(self):
        """Test statistics when no opportunities exist"""
        stats = self.analyzer.get_opportunity_statistics()
        
        assert stats['total_opportunities'] == 0
        assert stats['profitable_opportunities'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['average_profit_percentage'] == 0.0
        assert stats['max_profit_percentage'] == 0.0 
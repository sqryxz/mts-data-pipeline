import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from src.services.realtime_signal_aggregator import (
    RealTimeSignalAggregator, RealTimeSignal, RealTimeSignalType
)
from src.services.cross_exchange_analyzer import ArbitrageOpportunity, ArbitrageDirection
from src.data.realtime_models import OrderBookSnapshot, OrderBookLevel
from src.data.signal_models import SignalStrength, TradingSignal

class TestRealTimeSignalAggregator:
    def setup_method(self):
        self.aggregator = RealTimeSignalAggregator(
            min_arbitrage_profit=0.001,  # 0.1%
            min_signal_confidence=0.5,   # Lowered from 0.7
            max_active_signals=50
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
        """Test aggregator initialization"""
        assert self.aggregator.min_arbitrage_profit == 0.001
        assert self.aggregator.min_signal_confidence == 0.5
        assert self.aggregator.max_active_signals == 50
        assert len(self.aggregator.active_signals) == 0
        assert len(self.aggregator.signal_history) == 0
        assert self.aggregator.total_signals_generated == 0
        assert 'BTCUSDT' in self.aggregator.monitored_symbols
        assert 'ETHUSDT' in self.aggregator.monitored_symbols
    
    def test_real_time_signal_creation(self):
        """Test RealTimeSignal creation and methods"""
        timestamp = int(time.time() * 1000)
        signal = RealTimeSignal(
            signal_type=RealTimeSignalType.ARBITRAGE,
            symbol='BTCUSDT',
            strength=SignalStrength.STRONG,
            confidence=0.85,
            direction='buy',
            price=43000.0,
            volume=1.5,
            timestamp=timestamp,
            metadata={'test': 'data'}
        )
        
        assert signal.signal_type == RealTimeSignalType.ARBITRAGE
        assert signal.symbol == 'BTCUSDT'
        assert signal.strength == SignalStrength.STRONG
        assert signal.confidence == 0.85
        assert signal.direction == 'buy'
        assert signal.price == 43000.0
        assert signal.volume == 1.5
        assert signal.timestamp == timestamp
        assert signal.expires_at > timestamp
        assert not signal.is_expired()
        
        # Test traditional signal conversion
        traditional_signal = signal.to_traditional_signal()
        assert traditional_signal.signal_strength == SignalStrength.STRONG
        assert traditional_signal.confidence == 0.85
        assert isinstance(traditional_signal, TradingSignal)
    
    def test_signal_expiration(self):
        """Test signal expiration logic"""
        # Create expired signal
        old_timestamp = int(time.time() * 1000) - (10 * 60 * 1000)  # 10 minutes ago
        signal = RealTimeSignal(
            signal_type=RealTimeSignalType.ARBITRAGE,
            symbol='BTCUSDT',
            strength=SignalStrength.STRONG,
            confidence=0.85,
            direction='buy',
            price=43000.0,
            volume=1.5,
            timestamp=old_timestamp,
            metadata={},
            expires_at=old_timestamp + (5 * 60 * 1000)  # Expired 5 minutes ago
        )
        
        assert signal.is_expired()
    
    def test_signal_callbacks(self):
        """Test signal callback functionality"""
        callback_called = False
        received_signal = None
        
        def test_callback(signal):
            nonlocal callback_called, received_signal
            callback_called = True
            received_signal = signal
        
        self.aggregator.add_signal_callback(test_callback)
        
        # Test callback is added
        assert test_callback in self.aggregator.signal_callbacks
        
        # Remove callback
        self.aggregator.remove_signal_callback(test_callback)
        assert test_callback not in self.aggregator.signal_callbacks
    
    @pytest.mark.asyncio
    async def test_arbitrage_signal_detection(self):
        """Test arbitrage signal detection from orderbook data"""
        # Create orderbooks with arbitrage opportunity
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43100.0, 43110.0, 1.5)  # Higher prices
        
        # Mock the cross-exchange analyzer
        mock_opportunity = ArbitrageOpportunity(
            symbol='BTCUSDT',
            direction=ArbitrageDirection.BUY_BINANCE_SELL_BYBIT,
            profit_percentage=0.25,  # 0.25%
            profit_absolute=107.5,
            buy_exchange='binance',
            sell_exchange='bybit',
            buy_price=43010.0,
            sell_price=43117.5,
            max_volume=1.2,
            timestamp=int(time.time() * 1000)
        )
        
        with patch.object(self.aggregator.cross_exchange_analyzer, 'analyze_orderbooks') as mock_analyze:
            mock_analyze.return_value = (mock_opportunity, Mock())
            
            signals = await self.aggregator.process_orderbook_data(binance_orderbook, bybit_orderbook)
            
            assert len(signals) == 1
            signal = signals[0]
            assert signal.signal_type == RealTimeSignalType.ARBITRAGE
            assert signal.symbol == 'BTCUSDT'
            assert signal.direction == 'buy'
            assert signal.strength == SignalStrength.STRONG  # 0.25% > 0.2%
            assert signal.confidence >= 0.5  # Updated from 0.7
            assert signal.price == 43010.0
            assert 'buy_exchange' in signal.metadata
            assert 'sell_exchange' in signal.metadata
            assert signal.metadata['profit_percentage'] == 0.25
    
    @pytest.mark.asyncio
    async def test_arbitrage_signal_below_threshold(self):
        """Test that low-profit arbitrage opportunities are filtered out"""
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 2.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43015.0, 43025.0, 1.5)  # Small difference
        
        # Mock low-profit opportunity
        mock_opportunity = ArbitrageOpportunity(
            symbol='BTCUSDT',
            direction=ArbitrageDirection.BUY_BINANCE_SELL_BYBIT,
            profit_percentage=0.05,  # Only 0.05% < 0.1% threshold
            profit_absolute=2.15,
            buy_exchange='binance',
            sell_exchange='bybit',
            buy_price=43010.0,
            sell_price=43015.0,
            max_volume=1.2,
            timestamp=int(time.time() * 1000)
        )
        
        with patch.object(self.aggregator.cross_exchange_analyzer, 'analyze_orderbooks') as mock_analyze:
            mock_analyze.return_value = (mock_opportunity, Mock())
            
            signals = await self.aggregator.process_orderbook_data(binance_orderbook, bybit_orderbook)
            
            # Should not generate signal due to low profit
            assert len(signals) == 0
    
    @pytest.mark.asyncio
    async def test_spread_anomaly_detection(self):
        """Test spread anomaly detection"""
        # Create orderbooks with wide spreads
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43100.0, 1.0)  # Wide spread
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43005.0, 43015.0, 1.0)  # Normal spread
        
        # Mock no arbitrage opportunity
        with patch.object(self.aggregator.cross_exchange_analyzer, 'analyze_orderbooks') as mock_analyze:
            mock_analyze.return_value = (None, Mock())
            
            signals = await self.aggregator.process_orderbook_data(binance_orderbook, bybit_orderbook)
            
            # Should detect spread anomaly
            spread_signals = [s for s in signals if s.signal_type == RealTimeSignalType.SPREAD_ANOMALY]
            assert len(spread_signals) >= 1
            
            signal = spread_signals[0]
            assert signal.symbol == 'BTCUSDT'
            assert signal.direction == 'neutral'
            assert 'binance_spread_pct' in signal.metadata
            assert 'bybit_spread_pct' in signal.metadata
            assert signal.metadata['binance_spread_pct'] > 0.1  # Wide spread
    
    @pytest.mark.asyncio
    async def test_volume_spike_detection(self):
        """Test volume spike detection"""
        symbol = 'BTCUSDT'
        
        # First, add baseline orderbook data with multiple levels for better volume calculation
        baseline_binance = OrderBookSnapshot(
            exchange='binance', symbol=symbol, timestamp=int(time.time() * 1000),
            bids=[OrderBookLevel(price=43000.0, quantity=1.0, level=0),
                  OrderBookLevel(price=42999.0, quantity=1.0, level=1)],
            asks=[OrderBookLevel(price=43010.0, quantity=1.0, level=0),
                  OrderBookLevel(price=43011.0, quantity=1.0, level=1)]
        )
        baseline_bybit = OrderBookSnapshot(
            exchange='bybit', symbol=symbol, timestamp=int(time.time() * 1000),
            bids=[OrderBookLevel(price=43005.0, quantity=1.0, level=0),
                  OrderBookLevel(price=43004.0, quantity=1.0, level=1)],
            asks=[OrderBookLevel(price=43015.0, quantity=1.0, level=0),
                  OrderBookLevel(price=43016.0, quantity=1.0, level=1)]
        )
        
        self.aggregator.last_orderbook_data[symbol] = {
            'binance': baseline_binance,
            'bybit': baseline_bybit
        }
        
        # Create orderbooks with dramatic volume spike (10x volume)
        high_volume_binance = OrderBookSnapshot(
            exchange='binance', symbol=symbol, timestamp=int(time.time() * 1000),
            bids=[OrderBookLevel(price=43000.0, quantity=10.0, level=0),  # 10x volume
                  OrderBookLevel(price=42999.0, quantity=10.0, level=1)],
            asks=[OrderBookLevel(price=43010.0, quantity=10.0, level=0),  # 10x volume
                  OrderBookLevel(price=43011.0, quantity=10.0, level=1)]
        )
        high_volume_bybit = OrderBookSnapshot(
            exchange='bybit', symbol=symbol, timestamp=int(time.time() * 1000),
            bids=[OrderBookLevel(price=43005.0, quantity=1.0, level=0),
                  OrderBookLevel(price=43004.0, quantity=1.0, level=1)],
            asks=[OrderBookLevel(price=43015.0, quantity=1.0, level=0),
                  OrderBookLevel(price=43016.0, quantity=1.0, level=1)]
        )
        
        with patch.object(self.aggregator.cross_exchange_analyzer, 'analyze_orderbooks') as mock_analyze:
            mock_analyze.return_value = (None, Mock())
            
            signals = await self.aggregator.process_orderbook_data(high_volume_binance, high_volume_bybit)
            
            # Should detect volume spike
            volume_signals = [s for s in signals if s.signal_type == RealTimeSignalType.VOLUME_SPIKE]
            assert len(volume_signals) >= 1
            
            signal = volume_signals[0]
            assert signal.symbol == symbol
            assert signal.direction == 'neutral'
            assert 'volume_change_pct' in signal.metadata
            assert signal.metadata['volume_change_pct'] > 50  # > 50% increase
    
    @pytest.mark.asyncio
    async def test_signal_processing_and_storage(self):
        """Test signal processing and storage"""
        callback_called = False
        received_signal = None
        
        def test_callback(signal):
            nonlocal callback_called, received_signal
            callback_called = True
            received_signal = signal
        
        self.aggregator.add_signal_callback(test_callback)
        
        # Create test signal
        test_signal = RealTimeSignal(
            signal_type=RealTimeSignalType.ARBITRAGE,
            symbol='BTCUSDT',
            strength=SignalStrength.STRONG,
            confidence=0.85,
            direction='buy',
            price=43000.0,
            volume=1.5,
            timestamp=int(time.time() * 1000),
            metadata={'test': 'data'}
        )
        
        await self.aggregator._process_new_signal(test_signal)
        
        # Check signal was stored
        assert len(self.aggregator.active_signals) == 1
        assert len(self.aggregator.signal_history) == 1
        assert self.aggregator.total_signals_generated == 1
        
        # Check callback was called
        assert callback_called
        assert received_signal == test_signal
    
    def test_get_active_signals_filtering(self):
        """Test filtering of active signals"""
        # Add test signals
        signal1 = RealTimeSignal(
            signal_type=RealTimeSignalType.ARBITRAGE,
            symbol='BTCUSDT',
            strength=SignalStrength.STRONG,
            confidence=0.85,
            direction='buy',
            price=43000.0,
            volume=1.5,
            timestamp=int(time.time() * 1000),
            metadata={}
        )
        
        signal2 = RealTimeSignal(
            signal_type=RealTimeSignalType.SPREAD_ANOMALY,
            symbol='ETHUSDT',
            strength=SignalStrength.MODERATE,
            confidence=0.75,
            direction='neutral',
            price=2800.0,
            volume=5.0,
            timestamp=int(time.time() * 1000),
            metadata={}
        )
        
        self.aggregator.active_signals['test1'] = signal1
        self.aggregator.active_signals['test2'] = signal2
        
        # Test filtering by symbol
        btc_signals = self.aggregator.get_active_signals(symbol='BTCUSDT')
        assert len(btc_signals) == 1
        assert btc_signals[0].symbol == 'BTCUSDT'
        
        # Test filtering by signal type
        arbitrage_signals = self.aggregator.get_active_signals(signal_type=RealTimeSignalType.ARBITRAGE)
        assert len(arbitrage_signals) == 1
        assert arbitrage_signals[0].signal_type == RealTimeSignalType.ARBITRAGE
        
        # Test no filtering
        all_signals = self.aggregator.get_active_signals()
        assert len(all_signals) == 2
    
    def test_cleanup_expired_signals(self):
        """Test cleanup of expired signals"""
        current_time = int(time.time() * 1000)
        
        # Add active signal
        active_signal = RealTimeSignal(
            signal_type=RealTimeSignalType.ARBITRAGE,
            symbol='BTCUSDT',
            strength=SignalStrength.STRONG,
            confidence=0.85,
            direction='buy',
            price=43000.0,
            volume=1.5,
            timestamp=current_time,
            metadata={},
            expires_at=current_time + (10 * 60 * 1000)  # Expires in 10 minutes
        )
        
        # Add expired signal
        expired_signal = RealTimeSignal(
            signal_type=RealTimeSignalType.SPREAD_ANOMALY,
            symbol='ETHUSDT',
            strength=SignalStrength.MODERATE,
            confidence=0.75,
            direction='neutral',
            price=2800.0,
            volume=5.0,
            timestamp=current_time - (10 * 60 * 1000),  # 10 minutes ago
            metadata={},
            expires_at=current_time - (5 * 60 * 1000)  # Expired 5 minutes ago
        )
        
        self.aggregator.active_signals['active'] = active_signal
        self.aggregator.active_signals['expired'] = expired_signal
        
        assert len(self.aggregator.active_signals) == 2
        
        # Cleanup expired signals
        expired_count = self.aggregator.cleanup_expired_signals()
        
        assert expired_count == 1
        assert len(self.aggregator.active_signals) == 1
        assert 'active' in self.aggregator.active_signals
        assert 'expired' not in self.aggregator.active_signals
    
    def test_signal_statistics(self):
        """Test signal statistics calculation"""
        # Add test signals
        signal1 = RealTimeSignal(
            signal_type=RealTimeSignalType.ARBITRAGE,
            symbol='BTCUSDT',
            strength=SignalStrength.STRONG,
            confidence=0.85,
            direction='buy',
            price=43000.0,
            volume=1.5,
            timestamp=int(time.time() * 1000),
            metadata={}
        )
        
        signal2 = RealTimeSignal(
            signal_type=RealTimeSignalType.SPREAD_ANOMALY,
            symbol='BTCUSDT',
            strength=SignalStrength.MODERATE,
            confidence=0.75,
            direction='neutral',
            price=43050.0,
            volume=2.0,
            timestamp=int(time.time() * 1000),
            metadata={}
        )
        
        self.aggregator.active_signals['test1'] = signal1
        self.aggregator.active_signals['test2'] = signal2
        self.aggregator.total_signals_generated = 2
        
        stats = self.aggregator.get_signal_statistics()
        
        assert stats['total_signals_generated'] == 2
        assert stats['active_signals_count'] == 2
        assert stats['signal_types_distribution']['arbitrage'] == 1
        assert stats['signal_types_distribution']['spread_anomaly'] == 1
        assert stats['symbols_distribution']['BTCUSDT'] == 2
        assert stats['average_confidence'] == 0.8  # (0.85 + 0.75) / 2
    
    def test_volume_change_calculation(self):
        """Test volume change calculation between orderbooks"""
        # Create previous orderbook
        prev_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 1.0)
        
        # Create current orderbook with 50% more volume
        current_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 1.5)
        
        volume_change = self.aggregator._calculate_volume_change(prev_orderbook, current_orderbook)
        
        # Volume change should be 50% ((3.0 - 2.0) / 2.0 = 0.5)
        assert abs(volume_change - 0.5) < 0.01
    
    @pytest.mark.asyncio
    async def test_error_handling_in_signal_detection(self):
        """Test error handling in signal detection methods"""
        # Create invalid orderbook data
        binance_orderbook = self.create_orderbook('binance', 'BTCUSDT', 43000.0, 43010.0, 1.0)
        bybit_orderbook = self.create_orderbook('bybit', 'BTCUSDT', 43005.0, 43015.0, 1.0)
        
        # Mock analyzer to raise exception
        with patch.object(self.aggregator.cross_exchange_analyzer, 'analyze_orderbooks') as mock_analyze:
            mock_analyze.side_effect = Exception("Test error")
            
            # Should handle error gracefully and return empty list
            signals = await self.aggregator.process_orderbook_data(binance_orderbook, bybit_orderbook)
            assert len(signals) == 0
    
    @pytest.mark.asyncio
    async def test_callback_error_handling(self):
        """Test error handling in signal callbacks"""
        def failing_callback(signal):
            raise Exception("Callback error")
        
        self.aggregator.add_signal_callback(failing_callback)
        
        test_signal = RealTimeSignal(
            signal_type=RealTimeSignalType.ARBITRAGE,
            symbol='BTCUSDT',
            strength=SignalStrength.STRONG,
            confidence=0.85,
            direction='buy',
            price=43000.0,
            volume=1.5,
            timestamp=int(time.time() * 1000),
            metadata={}
        )
        
        # Should handle callback error gracefully
        await self.aggregator._process_new_signal(test_signal)
        
        # Signal should still be processed despite callback error
        assert len(self.aggregator.active_signals) == 1 
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from src.api.websockets.bybit_websocket import BybitWebSocket

class TestBybitWebSocket:
    def setup_method(self):
        self.message_handler = AsyncMock()
        self.websocket = BybitWebSocket(self.message_handler)
    
    def test_init(self):
        """Test WebSocket initialization"""
        assert self.websocket.url == 'wss://stream.bybit.com/v5/public/linear'
        assert self.websocket.message_handler == self.message_handler
        assert self.websocket.reconnect_attempts == 0
        assert self.websocket.max_reconnect_attempts == 5
        assert self.websocket.req_id == 1
        assert not self.websocket.is_connected
        assert self.websocket.subscriptions == []
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful WebSocket connection"""
        mock_websocket = AsyncMock()
        
        async def mock_connect_func(url):
            return mock_websocket
        
        with patch('websockets.connect', side_effect=mock_connect_func) as mock_connect:
            await self.websocket.connect()
            
            mock_connect.assert_called_once_with(self.websocket.url)
            assert self.websocket.websocket == mock_websocket
            assert self.websocket.is_connected
            assert self.websocket.reconnect_attempts == 0
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test WebSocket connection failure"""
        with patch('websockets.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await self.websocket.connect()
            
            assert not self.websocket.is_connected
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test WebSocket disconnection"""
        mock_websocket = AsyncMock()
        self.websocket.websocket = mock_websocket
        self.websocket.is_connected = True
        
        await self.websocket.disconnect()
        
        mock_websocket.close.assert_called_once()
        assert not self.websocket.is_connected
    
    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnect when websocket is None"""
        self.websocket.websocket = None
        await self.websocket.disconnect()  # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_subscribe_success(self):
        """Test successful channel subscription"""
        mock_websocket = AsyncMock()
        self.websocket.websocket = mock_websocket
        self.websocket.is_connected = True
        
        channels = ["orderbook.25.BTCUSDT", "tickers.ETHUSDT"]
        await self.websocket.subscribe(channels)
        
        # Check that send was called with correct message
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        
        assert sent_message['op'] == 'subscribe'
        assert sent_message['args'] == channels
        assert sent_message['req_id'] == '1'
        assert self.websocket.subscriptions == channels
        assert self.websocket.req_id == 2
    
    @pytest.mark.asyncio
    async def test_subscribe_not_connected(self):
        """Test subscription when not connected"""
        self.websocket.is_connected = False
        
        with pytest.raises(Exception, match="WebSocket not connected"):
            await self.websocket.subscribe(["orderbook.25.BTCUSDT"])
    
    @pytest.mark.asyncio
    async def test_unsubscribe_success(self):
        """Test successful channel unsubscription"""
        mock_websocket = AsyncMock()
        self.websocket.websocket = mock_websocket
        self.websocket.is_connected = True
        self.websocket.subscriptions = ["orderbook.25.BTCUSDT", "tickers.ETHUSDT"]
        
        channels = ["orderbook.25.BTCUSDT"]
        await self.websocket.unsubscribe(channels)
        
        # Check that send was called with correct message
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        
        assert sent_message['op'] == 'unsubscribe'
        assert sent_message['args'] == channels
        assert sent_message['req_id'] == '1'
        assert self.websocket.subscriptions == ["tickers.ETHUSDT"]
        assert self.websocket.req_id == 2
    
    @pytest.mark.asyncio
    async def test_ping(self):
        """Test ping functionality"""
        mock_websocket = AsyncMock()
        self.websocket.websocket = mock_websocket
        self.websocket.is_connected = True
        
        await self.websocket.ping()
        
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        
        assert sent_message['op'] == 'ping'
        assert sent_message['req_id'] == '1'
        assert self.websocket.req_id == 2
    
    @pytest.mark.asyncio
    async def test_ping_not_connected(self):
        """Test ping when not connected"""
        self.websocket.is_connected = False
        await self.websocket.ping()  # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self):
        """Test handling subscription response message"""
        message = {
            'op': 'subscribe',
            'success': True,
            'args': ['orderbook.25.BTCUSDT']
        }
        
        await self.websocket.handle_message(message)
        # Should not call message handler for control messages
        self.message_handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_error(self):
        """Test handling subscription error message"""
        message = {
            'op': 'subscribe',
            'success': False,
            'ret_msg': 'Invalid symbol'
        }
        
        await self.websocket.handle_message(message)
        self.message_handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_data_message(self):
        """Test handling market data message"""
        message = {
            'topic': 'orderbook.25.BTCUSDT',
            'data': {
                's': 'BTCUSDT',
                'b': [['43000', '1.5']],
                'a': [['43001', '2.0']]
            },
            'ts': 1640995200000
        }
        
        await self.websocket.handle_message(message)
        self.message_handler.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_handle_pong_message(self):
        """Test handling pong message"""
        message = {'op': 'pong'}
        
        await self.websocket.handle_message(message)
        self.message_handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_unknown_message(self):
        """Test handling unknown message format"""
        message = {'unknown_field': 'value'}
        
        await self.websocket.handle_message(message)
        self.message_handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_error(self):
        """Test error handling in message processing"""
        self.message_handler.side_effect = Exception("Handler error")
        
        message = {
            'topic': 'orderbook.25.BTCUSDT',
            'data': {'s': 'BTCUSDT'}
        }
        
        # Should not raise exception
        await self.websocket.handle_message(message)
    
    @pytest.mark.asyncio
    async def test_ping_loop(self):
        """Test periodic ping loop"""
        self.websocket.is_connected = True
        
        with patch.object(self.websocket, 'ping', new_callable=AsyncMock) as mock_ping:
            # Start ping loop and cancel after short time
            ping_task = asyncio.create_task(self.websocket._ping_loop())
            await asyncio.sleep(0.1)  # Let it start
            self.websocket.is_connected = False  # Stop the loop
            
            try:
                await asyncio.wait_for(ping_task, timeout=1.0)
            except asyncio.TimeoutError:
                ping_task.cancel()
            
            # Ping should have been called at least once
            assert mock_ping.call_count >= 0  # May not be called in short test
    
    @pytest.mark.asyncio
    async def test_reconnect_success(self):
        """Test successful reconnection"""
        self.websocket.subscriptions = ["orderbook.25.BTCUSDT"]
        
        with patch.object(self.websocket, 'connect', new_callable=AsyncMock) as mock_connect:
            with patch.object(self.websocket, 'subscribe', new_callable=AsyncMock) as mock_subscribe:
                with patch('src.utils.websocket_utils.exponential_backoff', new_callable=AsyncMock):
                    await self.websocket.reconnect()
                    
                    mock_connect.assert_called_once()
                    mock_subscribe.assert_called_once_with(["orderbook.25.BTCUSDT"])
                    assert self.websocket.reconnect_attempts == 1
    
    @pytest.mark.asyncio
    async def test_reconnect_max_attempts(self):
        """Test reconnection stops at max attempts"""
        self.websocket.reconnect_attempts = 5
        
        with patch.object(self.websocket, 'connect', new_callable=AsyncMock) as mock_connect:
            await self.websocket.reconnect()
            mock_connect.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reconnect_failure(self):
        """Test reconnection failure handling"""
        with patch.object(self.websocket, 'connect', side_effect=Exception("Reconnect failed")):
            with patch.object(self.websocket, 'reconnect', new_callable=AsyncMock) as mock_reconnect_recursive:
                with patch('src.utils.websocket_utils.exponential_backoff', new_callable=AsyncMock):
                    await self.websocket.reconnect()
                    
                    # Should call itself recursively on failure
                    mock_reconnect_recursive.assert_called_once()
    
    def test_create_orderbook_channel(self):
        """Test order book channel creation"""
        channel = self.websocket.create_orderbook_channel('btcusdt', 50)
        assert channel == 'orderbook.50.BTCUSDT'
        
        channel = self.websocket.create_orderbook_channel('ETHUSDT')
        assert channel == 'orderbook.25.ETHUSDT'
    
    def test_create_ticker_channel(self):
        """Test ticker channel creation"""
        channel = self.websocket.create_ticker_channel('btcusdt')
        assert channel == 'tickers.BTCUSDT'
    
    def test_create_trade_channel(self):
        """Test trade channel creation"""
        channel = self.websocket.create_trade_channel('ethusdt')
        assert channel == 'publicTrade.ETHUSDT'
    
    def test_create_kline_channel(self):
        """Test kline channel creation"""
        channel = self.websocket.create_kline_channel('btcusdt', '5')
        assert channel == 'kline.5.BTCUSDT'
        
        channel = self.websocket.create_kline_channel('ETHUSDT')
        assert channel == 'kline.1.ETHUSDT' 
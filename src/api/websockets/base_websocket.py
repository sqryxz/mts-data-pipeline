from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class BaseWebSocket(ABC):
    def __init__(self, url: str):
        self.url = url
        self.websocket = None
        self.is_connected = False
        self.subscriptions: List[str] = []
        
    @abstractmethod
    async def connect(self) -> None:
        """Establish WebSocket connection"""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        pass
        
    @abstractmethod
    async def subscribe(self, channels: List[str]) -> None:
        """Subscribe to WebSocket channels"""
        pass
        
    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Process incoming WebSocket message"""
        pass
        
    @abstractmethod
    async def reconnect(self) -> None:
        """Reconnect with exponential backoff"""
        pass 
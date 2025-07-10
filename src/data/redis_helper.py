import redis
import json
import logging
from typing import Any, Optional, Dict
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisHelper:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        
    def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self.client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            self.client.ping()
            logger.info("Connected to Redis successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    def set_json(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set JSON value in Redis"""
        try:
            json_str = json.dumps(value)
            if ttl:
                return self.client.setex(key, ttl, json_str)
            else:
                return self.client.set(key, json_str)
        except Exception as e:
            logger.error(f"Failed to set Redis key {key}: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value from Redis"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get Redis key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Failed to delete Redis key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check Redis key {key}: {e}")
            return False 
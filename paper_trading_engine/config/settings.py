"""
Configuration management for Paper Trading Engine
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration class for Paper Trading Engine"""
    
    # Portfolio Settings
    INITIAL_CAPITAL: float = 10000.0  # Starting with 10k USDT
    POSITION_SIZE_PCT: float = 0.02   # 2% position sizing
    
    # MTS Integration
    MTS_ALERT_PATH: str = "./data/alerts"  # Directory to monitor for MTS alerts
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/trading_engine.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Storage Settings
    PORTFOLIO_STATE_FILE: str = "./data/portfolio_state.json"
    TRADE_HISTORY_FILE: str = "./data/trade_history.json"
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        
        return cls(
            INITIAL_CAPITAL=float(os.getenv('INITIAL_CAPITAL', '10000.0')),
            POSITION_SIZE_PCT=float(os.getenv('POSITION_SIZE_PCT', '0.02')),
            MTS_ALERT_PATH=os.getenv('MTS_ALERT_PATH', './data/alerts'),
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO'),
            LOG_FILE=os.getenv('LOG_FILE', './logs/trading_engine.log'),
            LOG_FORMAT=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            PORTFOLIO_STATE_FILE=os.getenv('PORTFOLIO_STATE_FILE', './data/portfolio_state.json'),
            TRADE_HISTORY_FILE=os.getenv('TRADE_HISTORY_FILE', './data/trade_history.json'),
        )
    
    def validate(self) -> bool:
        """Validate configuration values"""
        
        if self.INITIAL_CAPITAL <= 0:
            raise ValueError("INITIAL_CAPITAL must be positive")
            
        if not (0 < self.POSITION_SIZE_PCT <= 1.0):
            raise ValueError("POSITION_SIZE_PCT must be between 0 and 1")
            
        if self.LOG_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError("Invalid LOG_LEVEL")
            
        return True
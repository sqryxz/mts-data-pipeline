"""
Logging configuration for Paper Trading Engine
"""

import logging
import logging.handlers
import os
from typing import Optional
from pathlib import Path

from config.settings import Config


def setup_logging(config: Config) -> logging.Logger:
    """
    Set up structured logging with file and console output
    
    Args:
        config: Configuration object
        
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path(config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('paper_trading_engine')
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a child logger for specific components
    
    Args:
        name: Component name for the logger
        
    Returns:
        Child logger instance
    """
    
    if name:
        return logging.getLogger(f'paper_trading_engine.{name}')
    else:
        return logging.getLogger('paper_trading_engine')
import logging
import os


def setup_logging():
    """Configure basic file logging to logs/app.log"""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    return logging.getLogger()  # Return root logger


# Initialize logger when module is imported
logger = setup_logging() 
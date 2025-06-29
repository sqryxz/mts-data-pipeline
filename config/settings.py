import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class that loads settings from environment variables."""
    
    def __init__(self):
        self.COINGECKO_BASE_URL = os.getenv('COINGECKO_BASE_URL', 'https://api.coingecko.com/api/v3')
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30')) 
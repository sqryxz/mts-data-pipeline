from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
from src.data.signal_models import TradingSignal


class SignalStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, config_path: str):
        """Initialize strategy with configuration file"""
        self.config = self.load_config(config_path)
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load strategy configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    @abstractmethod
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market conditions and return analysis results"""
        raise NotImplementedError("Subclasses must implement analyze method")
        
    @abstractmethod  
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """Generate trading signals from analysis"""
        raise NotImplementedError("Subclasses must implement generate_signals method")
        
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters for logging/optimization"""
        raise NotImplementedError("Subclasses must implement get_parameters method") 
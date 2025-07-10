import os
import importlib.util
import inspect
import sys
from typing import Dict, Type
from .base_strategy import SignalStrategy


class StrategyRegistry:
    """Registry for dynamically loading and managing trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, Type[SignalStrategy]] = {}
    
    def register_strategy(self, name: str, strategy_class: Type[SignalStrategy]):
        """Register a strategy class manually"""
        if not issubclass(strategy_class, SignalStrategy):
            raise ValueError(f"Strategy class must inherit from SignalStrategy")
        # Normalize strategy name for consistent lookup
        normalized_name = name.lower().replace('_', '').replace('-', '')
        self.strategies[normalized_name] = strategy_class
    
    def load_strategies_from_directory(self, directory_path: str):
        """Dynamically load all strategies from directory"""
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Strategy directory not found: {directory_path}")
        
        # Add the directory to sys.path temporarily to resolve imports
        abs_dir_path = os.path.abspath(directory_path)
        parent_dir = os.path.dirname(abs_dir_path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        try:
            for filename in os.listdir(directory_path):
                if filename.endswith('.py') and not filename.startswith('__') and filename != 'base_strategy.py':
                    module_name = filename[:-3]  # Remove .py extension
                    file_path = os.path.join(directory_path, filename)
                    
                    # Load module dynamically
                    spec = importlib.util.spec_from_file_location(f"strategies.{module_name}", file_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        
                        # Make SignalStrategy available in the module's namespace
                        module.SignalStrategy = SignalStrategy
                        
                        spec.loader.exec_module(module)
                        
                        # Find strategy classes in module
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if (issubclass(obj, SignalStrategy) and 
                                obj != SignalStrategy and 
                                not inspect.isabstract(obj)):
                                strategy_name = obj.__name__.lower().replace('strategy', '').replace('_', '')
                                self.strategies[strategy_name] = obj
        finally:
            # Remove the directory from sys.path
            if parent_dir in sys.path:
                sys.path.remove(parent_dir)
    
    def get_strategy(self, name: str, config_path: str) -> SignalStrategy:
        """Instantiate and return strategy instance"""
        strategy_name = name.lower().replace('_', '').replace('-', '')
        
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy '{name}' not found in registry. Available: {list(self.strategies.keys())}")
        
        strategy_class = self.strategies[strategy_name]
        return strategy_class(config_path)
    
    def list_strategies(self) -> Dict[str, Type[SignalStrategy]]:
        """Return all registered strategies"""
        return self.strategies.copy() 
import unittest
import tempfile
import os
from typing import Dict, Any, List
from src.signals.strategies.strategy_registry import StrategyRegistry
from src.signals.strategies.base_strategy import SignalStrategy


class DummyStrategy(SignalStrategy):
    """Test strategy for registry testing"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"test": "analysis"}
    
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[Any]:
        return [{"signal": "test"}]
    
    def get_parameters(self) -> Dict[str, Any]:
        return {"test_param": "value"}


class TestStrategyRegistry(unittest.TestCase):
    
    def setUp(self):
        self.registry = StrategyRegistry()
        
        # Create temporary config file for testing
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.write('{"name": "test_strategy", "test_param": "value"}')
        self.temp_config.close()
    
    def tearDown(self):
        # Clean up temporary file
        os.unlink(self.temp_config.name)
    
    def test_register_strategy(self):
        """Test manual strategy registration"""
        self.registry.register_strategy("test", DummyStrategy)
        
        # Verify strategy is registered
        self.assertIn("test", self.registry.strategies)
        self.assertEqual(self.registry.strategies["test"], DummyStrategy)
    
    def test_get_strategy(self):
        """Test strategy instantiation"""
        self.registry.register_strategy("test", DummyStrategy)
        
        # Get strategy instance
        strategy_instance = self.registry.get_strategy("test", self.temp_config.name)
        
        # Verify instance is correct type
        self.assertIsInstance(strategy_instance, DummyStrategy)
        self.assertIsInstance(strategy_instance, SignalStrategy)
        
        # Verify config was loaded
        self.assertEqual(strategy_instance.config["name"], "test_strategy")
    
    def test_strategy_not_found(self):
        """Test error when strategy not found"""
        with self.assertRaises(ValueError) as context:
            self.registry.get_strategy("nonexistent", self.temp_config.name)
        
        self.assertIn("Strategy 'nonexistent' not found in registry", str(context.exception))
    
    def test_invalid_strategy_class(self):
        """Test error when registering invalid strategy class"""
        class InvalidStrategy:
            pass
        
        with self.assertRaises(ValueError) as context:
            self.registry.register_strategy("invalid", InvalidStrategy)
        
        self.assertIn("Strategy class must inherit from SignalStrategy", str(context.exception))
    
    def test_list_strategies(self):
        """Test listing all strategies"""
        self.registry.register_strategy("test1", DummyStrategy)
        self.registry.register_strategy("test2", DummyStrategy)
        
        strategies = self.registry.list_strategies()
        
        self.assertEqual(len(strategies), 2)
        self.assertIn("test1", strategies)
        self.assertIn("test2", strategies)
    
    def test_load_strategies_from_directory_nonexistent(self):
        """Test error when directory doesn't exist"""
        with self.assertRaises(FileNotFoundError):
            self.registry.load_strategies_from_directory("/nonexistent/path")


if __name__ == '__main__':
    unittest.main() 
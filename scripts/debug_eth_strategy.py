#!/usr/bin/env python3
"""
Debug ETHTopBottomStrategy
Test script to debug why ETHTopBottomStrategy is not being loaded.
"""

import sys
import os
import inspect

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.signals.strategies.base_strategy import SignalStrategy
from src.signals.strategies.eth_tops_bottoms_strategy import ETHTopBottomStrategy

def test_eth_strategy():
    """Test the ETHTopBottomStrategy class."""
    print("🔍 Testing ETHTopBottomStrategy")
    print("=" * 50)
    
    try:
        # Check if class exists
        print(f"✅ Class exists: {ETHTopBottomStrategy}")
        
        # Check inheritance
        is_subclass = issubclass(ETHTopBottomStrategy, SignalStrategy)
        print(f"✅ Inherits from SignalStrategy: {is_subclass}")
        
        # Check if it's abstract
        is_abstract = inspect.isabstract(ETHTopBottomStrategy)
        print(f"✅ Is abstract: {is_abstract}")
        
        # Check class name
        class_name = ETHTopBottomStrategy.__name__
        print(f"✅ Class name: {class_name}")
        
        # Check normalized name
        normalized_name = class_name.lower().replace('strategy', '').replace('_', '')
        print(f"✅ Normalized name: {normalized_name}")
        
        # Try to instantiate
        try:
            config_path = "config/strategies/eth_tops_bottoms.json"
            strategy = ETHTopBottomStrategy(config_path)
            print(f"✅ Successfully instantiated strategy")
            
            # Check required methods
            has_analyze = hasattr(strategy, 'analyze')
            has_generate_signals = hasattr(strategy, 'generate_signals')
            has_get_parameters = hasattr(strategy, 'get_parameters')
            
            print(f"✅ Has analyze method: {has_analyze}")
            print(f"✅ Has generate_signals method: {has_generate_signals}")
            print(f"✅ Has get_parameters method: {has_get_parameters}")
            
        except Exception as e:
            print(f"❌ Failed to instantiate: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ETHTopBottomStrategy: {e}")
        return False

def test_strategy_registry_loading():
    """Test strategy registry loading specifically for ETH strategy."""
    print("\n🔧 Testing Strategy Registry Loading")
    print("=" * 50)
    
    try:
        from src.signals.strategies.strategy_registry import StrategyRegistry
        
        registry = StrategyRegistry()
        
        # Load strategies from directory
        strategies_dir = "src/signals/strategies"
        print(f"📁 Loading strategies from: {strategies_dir}")
        registry.load_strategies_from_directory(strategies_dir)
        
        # List available strategies
        strategies = registry.list_strategies()
        print(f"\n📊 Available strategies: {list(strategies.keys())}")
        
        for name, strategy_class in strategies.items():
            print(f"   ✅ {name}: {strategy_class.__name__}")
        
        # Check specifically for ethtopbottom
        if 'ethtopbottom' in strategies:
            print(f"✅ ETHTopBottom strategy found in registry")
        else:
            print(f"❌ ETHTopBottom strategy NOT found in registry")
            
            # Try to register manually
            print("🔧 Attempting manual registration...")
            registry.register_strategy('ethtopbottom', ETHTopBottomStrategy)
            
            strategies = registry.list_strategies()
            if 'ethtopbottom' in strategies:
                print(f"✅ Manual registration successful")
            else:
                print(f"❌ Manual registration failed")
        
        return strategies
        
    except Exception as e:
        print(f"❌ Error testing strategy registry: {e}")
        return None

def main():
    """Run all tests."""
    print("🚀 ETHTopBottomStrategy Debug Suite")
    print("=" * 60)
    
    # Test ETH strategy class
    success = test_eth_strategy()
    
    if success:
        print(f"\n✅ ETHTopBottomStrategy class test passed.")
    else:
        print(f"\n❌ ETHTopBottomStrategy class test failed.")
        return
    
    # Test strategy registry loading
    strategies = test_strategy_registry_loading()
    
    if strategies and 'ethtopbottom' in strategies:
        print(f"\n✅ Strategy registry test passed. ETHTopBottom strategy is available.")
    else:
        print(f"\n❌ Strategy registry test failed. ETHTopBottom strategy is not available.")

if __name__ == "__main__":
    main()

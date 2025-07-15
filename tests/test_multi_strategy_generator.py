"""
Tests for Task 9 Multi-Strategy Signal Generator.
Tests orchestration of multiple strategies and signal aggregation.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.services.multi_strategy_generator import MultiStrategyGenerator, create_default_multi_strategy_generator
from src.data.signal_models import TradingSignal, SignalType, SignalStrength
from src.utils.exceptions import ConfigurationError, DataProcessingError


class TestMultiStrategyGenerator:
    """Test suite for Task 9 Multi-Strategy Signal Generator."""
    
    @pytest.fixture
    def strategy_configs(self):
        """Valid strategy configurations for testing."""
        return {
            "VIX_Correlation_Strategy": {
                "config_path": "config/strategies/vix_correlation.json"
            },
            "Mean_Reversion_Strategy": {
                "config_path": "config/strategies/mean_reversion.json"
            }
        }
    
    @pytest.fixture
    def aggregator_config(self):
        """Valid aggregator configuration for testing."""
        return {
            "strategy_weights": {
                "VIX_Correlation_Strategy": 0.6,
                "Mean_Reversion_Strategy": 0.4
            },
            "aggregation_config": {
                "conflict_resolution": "weighted_average",
                "min_confidence_threshold": 0.1,
                "max_position_size": 0.05
            }
        }
    
    def test_init_valid_configuration(self, strategy_configs, aggregator_config):
        """Test initialization with valid configuration - Task 9 core requirement."""
        with patch('src.services.multi_strategy_generator.StrategyRegistry') as mock_registry_class, \
             patch('src.services.multi_strategy_generator.SignalAggregator') as mock_aggregator_class, \
             patch('src.services.multi_strategy_generator.CryptoDatabase') as mock_db_class:
            
            # Setup mocks
            mock_registry = Mock()
            mock_registry_class.return_value = mock_registry
            
            mock_aggregator = Mock()
            mock_aggregator_class.return_value = mock_aggregator
            
            mock_db = Mock()
            mock_db_class.return_value = mock_db
            
            # Mock strategy loading
            mock_strategy1 = Mock()
            mock_strategy1.get_parameters.return_value = {'assets': ['bitcoin', 'ethereum']}
            mock_strategy2 = Mock()
            mock_strategy2.get_parameters.return_value = {'assets': ['bitcoin', 'binancecoin']}
            
            mock_registry.get_strategy.side_effect = [mock_strategy1, mock_strategy2]
            
            # Create generator
            generator = MultiStrategyGenerator(strategy_configs, aggregator_config)
            
            # Verify initialization
            assert generator.strategy_configs == strategy_configs
            assert generator.aggregator_config == aggregator_config
            assert len(generator.strategies) == 2
            
            # Verify registry was loaded
            mock_registry.load_strategies_from_directory.assert_called_once_with("src/signals/strategies")
            
            # Verify aggregator was created with correct weights
            mock_aggregator_class.assert_called_once_with(
                aggregator_config['strategy_weights'],
                aggregator_config['aggregation_config']
            )
    
    def test_init_invalid_configuration(self):
        """Test initialization with invalid configurations."""
        
        # Test empty strategy configs
        with pytest.raises(ConfigurationError, match="Strategy configurations cannot be empty"):
            MultiStrategyGenerator({}, {"strategy_weights": {"test": 0.5}})
        
        # Test missing strategy weights
        with pytest.raises(ConfigurationError, match="Aggregator config must include 'strategy_weights'"):
            MultiStrategyGenerator({"test": {}}, {})
    
    @patch('src.services.multi_strategy_generator.StrategyRegistry')
    @patch('src.services.multi_strategy_generator.SignalAggregator')
    @patch('src.services.multi_strategy_generator.CryptoDatabase')
    def test_generate_aggregated_signals_success(self, mock_db_class, mock_aggregator_class, mock_registry_class,
                                                 strategy_configs, aggregator_config):
        """Test successful signal generation and aggregation - Task 9 core requirement."""
        
        # Setup mocks
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        
        mock_aggregator = Mock()
        mock_aggregator_class.return_value = mock_aggregator
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        # Sample signals for testing
        vix_signals = [
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=datetime.now().timestamp(),
                price=50000.0,
                strategy_name="VIX_Correlation_Strategy",
                signal_strength=SignalStrength.STRONG,
                confidence=0.8,
                position_size=0.03
            )
        ]
        
        mean_reversion_signals = [
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.SHORT,
                timestamp=datetime.now().timestamp(),
                price=50100.0,
                strategy_name="Mean_Reversion_Strategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.6,
                position_size=0.025
            )
        ]
        
        # Mock strategy loading
        mock_strategy1 = Mock()
        mock_strategy1.get_parameters.return_value = {'assets': ['bitcoin', 'ethereum']}
        mock_strategy1.analyze.return_value = {'analysis': 'data1'}
        mock_strategy1.generate_signals.return_value = vix_signals
        
        mock_strategy2 = Mock()
        mock_strategy2.get_parameters.return_value = {'assets': ['bitcoin', 'binancecoin']}
        mock_strategy2.analyze.return_value = {'analysis': 'data2'}
        mock_strategy2.generate_signals.return_value = mean_reversion_signals
        
        mock_registry.get_strategy.side_effect = [mock_strategy1, mock_strategy2]
        
        # Mock market data
        mock_market_data = {'vix_data': [], 'crypto_data': {}}
        mock_db.get_strategy_market_data.return_value = mock_market_data
        
        # Mock aggregated signals
        aggregated_signals = [
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=datetime.now().timestamp(),
                price=50050.0,
                strategy_name="Aggregated_Signal",
                signal_strength=SignalStrength.STRONG,
                confidence=0.75,
                position_size=0.028
            )
        ]
        mock_aggregator.aggregate_signals.return_value = aggregated_signals
        
        # Create generator and generate signals
        generator = MultiStrategyGenerator(strategy_configs, aggregator_config)
        result = generator.generate_aggregated_signals(days=30)
        
        # Verify results
        assert len(result) == 1
        assert result[0].asset == "bitcoin"
        assert result[0].signal_type == SignalType.LONG
        
        # Verify market data was requested for all unique assets
        mock_db.get_strategy_market_data.assert_called_once()
        args, kwargs = mock_db.get_strategy_market_data.call_args
        assert set(args[0]) == {'bitcoin', 'ethereum', 'binancecoin'}  # All unique assets
        assert args[1] == 30  # Days parameter
        
        # Verify strategies were called
        mock_strategy1.analyze.assert_called_once_with(mock_market_data)
        mock_strategy1.generate_signals.assert_called_once()
        mock_strategy2.analyze.assert_called_once_with(mock_market_data)
        mock_strategy2.generate_signals.assert_called_once()
        
        # Verify aggregation was performed
        mock_aggregator.aggregate_signals.assert_called_once()
    
    @patch('src.services.multi_strategy_generator.StrategyRegistry')
    @patch('src.services.multi_strategy_generator.SignalAggregator')
    @patch('src.services.multi_strategy_generator.CryptoDatabase')
    def test_get_strategy_performance_summary(self, mock_db_class, mock_aggregator_class, mock_registry_class,
                                              strategy_configs, aggregator_config):
        """Test strategy performance summary generation."""
        
        # Setup mocks
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        
        mock_aggregator = Mock()
        mock_aggregator_class.return_value = mock_aggregator
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        # Mock strategy loading
        mock_strategy1 = Mock()
        mock_strategy1.get_parameters.return_value = {'assets': ['bitcoin']}
        mock_strategy2 = Mock()
        mock_strategy2.get_parameters.return_value = {'assets': ['ethereum']}
        mock_registry.get_strategy.side_effect = [mock_strategy1, mock_strategy2]
        
        # Create generator
        generator = MultiStrategyGenerator(strategy_configs, aggregator_config)
        
        # Test with sample signals
        test_signals = [
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=datetime.now().timestamp(),
                price=50000.0,
                strategy_name="VIX_Correlation_Strategy",
                signal_strength=SignalStrength.STRONG,
                confidence=0.8,
                position_size=0.03
            ),
            TradingSignal(
                asset="ethereum",
                signal_type=SignalType.SHORT,
                timestamp=datetime.now().timestamp(),
                price=3000.0,
                strategy_name="Mean_Reversion_Strategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.6,
                position_size=0.02
            )
        ]
        
        summary = generator.get_strategy_performance_summary(test_signals)
        
        # Verify summary structure
        assert summary['total_signals'] == 2
        assert summary['signal_types']['LONG'] == 1
        assert summary['signal_types']['SHORT'] == 1
        assert summary['assets']['bitcoin'] == 1
        assert summary['assets']['ethereum'] == 1
        
        # Verify confidence statistics
        assert summary['confidence_stats']['mean'] == 0.7
        assert summary['confidence_stats']['min'] == 0.6
        assert summary['confidence_stats']['max'] == 0.8
        assert summary['confidence_stats']['high_confidence_count'] == 1
        
        # Verify strategy distribution
        assert summary['strategy_distribution']['VIX_Correlation_Strategy'] == 1
        assert summary['strategy_distribution']['Mean_Reversion_Strategy'] == 1
    
    def test_create_default_multi_strategy_generator(self):
        """Test creation of default multi-strategy generator."""
        
        with patch('src.services.multi_strategy_generator.StrategyRegistry') as mock_registry_class, \
             patch('src.services.multi_strategy_generator.SignalAggregator') as mock_aggregator_class, \
             patch('src.services.multi_strategy_generator.CryptoDatabase') as mock_db_class:
            
            # Setup mocks
            mock_registry = Mock()
            mock_registry_class.return_value = mock_registry
            
            mock_aggregator = Mock()
            mock_aggregator_class.return_value = mock_aggregator
            
            mock_db = Mock()
            mock_db_class.return_value = mock_db
            
            # Mock strategy loading
            mock_strategy1 = Mock()
            mock_strategy1.get_parameters.return_value = {'assets': ['bitcoin']}
            mock_strategy2 = Mock()
            mock_strategy2.get_parameters.return_value = {'assets': ['ethereum']}
            mock_registry.get_strategy.side_effect = [mock_strategy1, mock_strategy2]
            
            # Create default generator
            generator = create_default_multi_strategy_generator()
            
            # Verify default configuration
            assert "VIX_Correlation_Strategy" in generator.strategy_configs
            assert "Mean_Reversion_Strategy" in generator.strategy_configs
            assert generator.strategy_configs["VIX_Correlation_Strategy"]["config_path"] == "config/strategies/vix_correlation.json"
            assert generator.strategy_configs["Mean_Reversion_Strategy"]["config_path"] == "config/strategies/mean_reversion.json"
            
            # Verify aggregator config
            assert generator.aggregator_config["strategy_weights"]["VIX_Correlation_Strategy"] == 0.6
            assert generator.aggregator_config["strategy_weights"]["Mean_Reversion_Strategy"] == 0.4
            assert generator.aggregator_config["aggregation_config"]["conflict_resolution"] == "weighted_average"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

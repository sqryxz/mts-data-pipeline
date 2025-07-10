"""
Tests for Signal Aggregator functionality.
Tests weighted combination, conflict resolution, and deduplication.
"""

import pytest
import logging
from datetime import datetime
from typing import Dict, List

from src.signals.signal_aggregator import SignalAggregator
from src.data.signal_models import TradingSignal, SignalType, SignalStrength


class TestSignalAggregator:
    """Test suite for SignalAggregator class."""
    
    @pytest.fixture
    def sample_strategy_weights(self):
        """Sample strategy weights for testing."""
        return {
            "VIX_Correlation_Strategy": 0.6,
            "Mean_Reversion_Strategy": 0.4
        }
    
    @pytest.fixture
    def aggregator(self, sample_strategy_weights):
        """Create a SignalAggregator instance for testing."""
        return SignalAggregator(sample_strategy_weights)
    
    @pytest.fixture
    def mock_vix_signal_long(self):
        """Mock VIX correlation strategy signal - LONG."""
        return TradingSignal(
            asset="bitcoin",
            signal_type=SignalType.LONG,
            timestamp=datetime.now().timestamp(),
            price=50000.0,
            strategy_name="VIX_Correlation_Strategy",
            signal_strength=SignalStrength.STRONG,
            confidence=0.8,
            position_size=0.03,
            stop_loss=47500.0,
            take_profit=55000.0,
            max_risk=0.05,
            analysis_data={
                'vix_correlation': -0.7,
                'timeframe_analysis': {
                    '7d': -0.65,
                    '14d': -0.72,
                    '30d': -0.68
                }
            }
        )
    
    @pytest.fixture
    def mock_mean_reversion_signal_long(self):
        """Mock mean reversion strategy signal - LONG."""
        return TradingSignal(
            asset="bitcoin",
            signal_type=SignalType.LONG,
            timestamp=datetime.now().timestamp(),
            price=49800.0,
            strategy_name="Mean_Reversion_Strategy",
            signal_strength=SignalStrength.MODERATE,
            confidence=0.7,
            position_size=0.025,
            stop_loss=47300.0,
            take_profit=54800.0,
            max_risk=0.05,
            analysis_data={
                'vix_level': 28.5,
                'crypto_drawdown': 0.12,
                'rsi': 25.3
            }
        )
    
    @pytest.fixture
    def mock_vix_signal_short(self):
        """Mock VIX correlation strategy signal - SHORT."""
        return TradingSignal(
            asset="bitcoin",
            signal_type=SignalType.SHORT,
            timestamp=datetime.now().timestamp(),
            price=50000.0,
            strategy_name="VIX_Correlation_Strategy",
            signal_strength=SignalStrength.MODERATE,
            confidence=0.6,
            position_size=0.02,
            stop_loss=52500.0,
            take_profit=47500.0,
            max_risk=0.05,
            analysis_data={
                'vix_correlation': 0.65,
                'timeframe_analysis': {
                    '7d': 0.62,
                    '14d': 0.68
                }
            }
        )
    
    def test_init_with_valid_weights(self, sample_strategy_weights):
        """Test SignalAggregator initialization with valid weights."""
        aggregator = SignalAggregator(sample_strategy_weights)
        
        # Weights should be normalized to sum to 1.0
        assert abs(sum(aggregator.strategy_weights.values()) - 1.0) < 1e-6
        assert aggregator.strategy_weights["VIX_Correlation_Strategy"] == 0.6
        assert aggregator.strategy_weights["Mean_Reversion_Strategy"] == 0.4
        
        # Default config should be set
        assert aggregator.config['conflict_resolution'] == 'weighted_average'
        assert aggregator.config['max_position_size'] == 0.10
    
    def test_init_with_invalid_weights(self):
        """Test SignalAggregator initialization with invalid weights."""
        with pytest.raises(ValueError, match="Strategy weights must sum to a positive value"):
            SignalAggregator({"strategy1": 0, "strategy2": 0})
        
        with pytest.raises(ValueError, match="Strategy weights must sum to a positive value"):
            SignalAggregator({"strategy1": -0.5, "strategy2": -0.3})
    
    def test_init_with_custom_config(self, sample_strategy_weights):
        """Test SignalAggregator initialization with custom configuration."""
        custom_config = {
            'conflict_resolution': 'strongest_wins',
            'max_position_size': 0.05,
            'require_majority_agreement': True
        }
        
        aggregator = SignalAggregator(sample_strategy_weights, custom_config)
        
        assert aggregator.config['conflict_resolution'] == 'strongest_wins'
        assert aggregator.config['max_position_size'] == 0.05
        assert aggregator.config['require_majority_agreement'] is True
        # Should keep default for unspecified values
        assert aggregator.config['min_confidence_threshold'] == 0.1
    
    def test_aggregate_agreeing_signals(self, aggregator, mock_vix_signal_long, mock_mean_reversion_signal_long):
        """Test aggregation when both strategies agree (both LONG)."""
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],
            "Mean_Reversion_Strategy": [mock_mean_reversion_signal_long]
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        assert len(aggregated) == 1
        signal = aggregated[0]
        
        # Should be LONG since both strategies agree
        assert signal.signal_type == SignalType.LONG
        assert signal.asset == "bitcoin"
        assert signal.strategy_name == "Aggregated_Signal"
        
        # Should be weighted average of confidence (0.6 * 0.8 + 0.4 * 0.7) / 1.0 = 0.76
        expected_confidence = (0.6 * 0.8 + 0.4 * 0.7)
        assert abs(signal.confidence - expected_confidence) < 0.01
        
        # Should be weighted average of position size (0.6 * 0.03 + 0.4 * 0.025) / 1.0 = 0.028
        expected_position_size = (0.6 * 0.03 + 0.4 * 0.025)
        assert abs(signal.position_size - expected_position_size) < 0.001
        
        # Should be STRONG since confidence > 0.7 and dominant weight > 0.7
        assert signal.signal_strength == SignalStrength.STRONG
        
        # Should have aggregation metadata
        assert signal.analysis_data['aggregation_method'] == 'weighted_average'
        assert len(signal.analysis_data['strategies_combined']) == 2
    
    def test_aggregate_conflicting_signals_weighted_average(self, aggregator, mock_vix_signal_long, mock_vix_signal_short):
        """Test aggregation when strategies conflict (LONG vs SHORT) using weighted average."""
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],  # LONG, weight 0.6
            "Mean_Reversion_Strategy": [mock_vix_signal_short]   # SHORT, weight 0.4
        }
        
        # Modify the SHORT signal to have the correct strategy name
        mock_vix_signal_short.strategy_name = "Mean_Reversion_Strategy"
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        assert len(aggregated) == 1
        signal = aggregated[0]
        
        # Should be LONG since VIX strategy has higher weight (0.6 > 0.4)
        assert signal.signal_type == SignalType.LONG
        assert signal.strategy_name == "Aggregated_Signal"
        
        # Should only include signals matching the dominant type (LONG)
        assert signal.analysis_data['relevant_signals_count'] == 1
        assert signal.analysis_data['original_signals_count'] == 2
        
        # Should have conflict analysis
        conflict_analysis = signal.analysis_data['signal_conflict_analysis']
        assert conflict_analysis['has_opposing'] is True
        assert conflict_analysis['has_conflict'] is True
    
    def test_aggregate_conflicting_signals_strongest_wins(self, sample_strategy_weights, mock_vix_signal_long, mock_mean_reversion_signal_long):
        """Test aggregation using 'strongest_wins' method."""
        config = {'conflict_resolution': 'strongest_wins'}
        aggregator = SignalAggregator(sample_strategy_weights, config)
        
        # Make VIX signal stronger (higher confidence * weight)
        mock_vix_signal_long.confidence = 0.9  # 0.9 * 0.6 = 0.54
        mock_mean_reversion_signal_long.confidence = 0.8  # 0.8 * 0.4 = 0.32
        
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],
            "Mean_Reversion_Strategy": [mock_mean_reversion_signal_long]
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        assert len(aggregated) == 1
        signal = aggregated[0]
        
        # Should pick the VIX signal (strongest)
        assert signal.confidence == 0.9
        assert signal.position_size == min(0.10, mock_vix_signal_long.position_size)  # Capped by max_position_size
        
        # Should have strongest_wins metadata
        assert signal.analysis_data['aggregation_method'] == 'strongest_wins'
        assert signal.analysis_data['selected_strategy'] == "VIX_Correlation_Strategy"
    
    def test_aggregate_conflicting_signals_conservative(self, sample_strategy_weights, mock_vix_signal_long, mock_vix_signal_short):
        """Test aggregation using 'conservative' method with opposing signals."""
        config = {'conflict_resolution': 'conservative'}
        aggregator = SignalAggregator(sample_strategy_weights, config)
        
        mock_vix_signal_short.strategy_name = "Mean_Reversion_Strategy"
        
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],  # LONG
            "Mean_Reversion_Strategy": [mock_vix_signal_short]   # SHORT
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        # Conservative mode should reject opposing signals
        assert len(aggregated) == 0
    
    def test_aggregate_with_low_confidence_filtering(self, aggregator, mock_vix_signal_long):
        """Test that low confidence signals are filtered out."""
        # Create a low confidence signal
        low_confidence_signal = TradingSignal(
            asset="ethereum",
            signal_type=SignalType.LONG,
            timestamp=datetime.now().timestamp(),
            price=3000.0,
            strategy_name="Mean_Reversion_Strategy",
            signal_strength=SignalStrength.WEAK,
            confidence=0.05,  # Below default threshold of 0.1
            position_size=0.02
        )
        
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],
            "Mean_Reversion_Strategy": [low_confidence_signal]
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        # Should only have bitcoin signal (ethereum filtered out due to low confidence)
        assert len(aggregated) == 1
        assert aggregated[0].asset == "bitcoin"
    
    def test_aggregate_multiple_assets(self, aggregator):
        """Test aggregation with signals for multiple assets."""
        bitcoin_signal = TradingSignal(
            asset="bitcoin",
            signal_type=SignalType.LONG,
            timestamp=datetime.now().timestamp(),
            price=50000.0,
            strategy_name="VIX_Correlation_Strategy",
            signal_strength=SignalStrength.STRONG,
            confidence=0.8,
            position_size=0.03
        )
        
        ethereum_signal = TradingSignal(
            asset="ethereum",
            signal_type=SignalType.SHORT,
            timestamp=datetime.now().timestamp(),
            price=3000.0,
            strategy_name="Mean_Reversion_Strategy",
            signal_strength=SignalStrength.MODERATE,
            confidence=0.6,
            position_size=0.025
        )
        
        strategy_signals = {
            "VIX_Correlation_Strategy": [bitcoin_signal],
            "Mean_Reversion_Strategy": [ethereum_signal]
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        # Should have 2 signals, one for each asset
        assert len(aggregated) == 2
        
        assets = {signal.asset for signal in aggregated}
        assert assets == {"bitcoin", "ethereum"}
        
        # Signals should be sorted by confidence (bitcoin should be first)
        assert aggregated[0].asset == "bitcoin"  # Higher confidence
        assert aggregated[1].asset == "ethereum"
    
    def test_aggregate_empty_signals(self, aggregator):
        """Test aggregation with empty signals."""
        aggregated = aggregator.aggregate_signals({})
        assert len(aggregated) == 0
        
        aggregated = aggregator.aggregate_signals({"VIX_Correlation_Strategy": []})
        assert len(aggregated) == 0
    
    def test_aggregate_unknown_strategy(self, aggregator, mock_vix_signal_long):
        """Test aggregation with unknown strategy (should be ignored)."""
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],
            "Unknown_Strategy": [mock_vix_signal_long]  # Should be ignored
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        # Should only process known strategy
        assert len(aggregated) == 1
        assert aggregated[0].asset == "bitcoin"
    
    def test_get_aggregation_stats(self, aggregator, mock_vix_signal_long, mock_mean_reversion_signal_long, mock_vix_signal_short):
        """Test aggregation statistics functionality."""
        mock_vix_signal_short.strategy_name = "Mean_Reversion_Strategy"
        
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],
            "Mean_Reversion_Strategy": [mock_mean_reversion_signal_long, mock_vix_signal_short]
        }
        
        stats = aggregator.get_aggregation_stats(strategy_signals)
        
        assert stats['strategy_count'] == 2
        assert stats['total_signals'] == 3
        assert stats['signals_per_strategy']['VIX_Correlation_Strategy'] == 1
        assert stats['signals_per_strategy']['Mean_Reversion_Strategy'] == 2
        assert stats['total_unique_assets'] == 1  # All signals for bitcoin
        assert stats['assets_with_conflicts'] == 1  # Bitcoin has conflicting signals
        
        # Should have conflict analysis for bitcoin
        assert 'bitcoin' in stats['conflict_analysis']
        bitcoin_conflict = stats['conflict_analysis']['bitcoin']
        assert bitcoin_conflict['has_conflict'] is True
        assert bitcoin_conflict['signal_count'] == 3
    
    def test_position_size_capping(self, sample_strategy_weights):
        """Test that position sizes are properly capped."""
        config = {'max_position_size': 0.02}  # Low cap
        aggregator = SignalAggregator(sample_strategy_weights, config)
        
        large_position_signal = TradingSignal(
            asset="bitcoin",
            signal_type=SignalType.LONG,
            timestamp=datetime.now().timestamp(),
            price=50000.0,
            strategy_name="VIX_Correlation_Strategy",
            signal_strength=SignalStrength.STRONG,
            confidence=0.8,
            position_size=0.05  # Above cap
        )
        
        strategy_signals = {
            "VIX_Correlation_Strategy": [large_position_signal]
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        assert len(aggregated) == 1
        # Position size should be capped
        assert aggregated[0].position_size == 0.02
    
    def test_weighted_risk_management_params(self, aggregator, mock_vix_signal_long, mock_mean_reversion_signal_long):
        """Test that risk management parameters are properly weighted."""
        strategy_signals = {
            "VIX_Correlation_Strategy": [mock_vix_signal_long],      # stop_loss: 47500, take_profit: 55000, confidence: 0.8
            "Mean_Reversion_Strategy": [mock_mean_reversion_signal_long]  # stop_loss: 47300, take_profit: 54800, confidence: 0.7
        }
        
        aggregated = aggregator.aggregate_signals(strategy_signals)
        
        assert len(aggregated) == 1
        signal = aggregated[0]
        
        # Effective weights: VIX = 0.6 * 0.8 = 0.48, Mean = 0.4 * 0.7 = 0.28, Total = 0.76
        # Should be weighted average: (0.48 * 47500 + 0.28 * 47300) / 0.76 ≈ 47426.32
        vix_effective_weight = 0.6 * 0.8  # strategy_weight * confidence
        mean_effective_weight = 0.4 * 0.7
        total_effective_weight = vix_effective_weight + mean_effective_weight
        
        expected_stop_loss = (vix_effective_weight * 47500 + mean_effective_weight * 47300) / total_effective_weight
        assert abs(signal.stop_loss - expected_stop_loss) < 1.0
        
        # Should be weighted average: (0.48 * 55000 + 0.28 * 54800) / 0.76 ≈ 54926.32
        expected_take_profit = (vix_effective_weight * 55000 + mean_effective_weight * 54800) / total_effective_weight
        assert abs(signal.take_profit - expected_take_profit) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
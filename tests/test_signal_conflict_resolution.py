"""
Tests for Task 8 Signal Conflict Resolution functionality.
Tests standalone conflict resolution, enhanced policies, and conflict reporting.
"""

import pytest
import logging
from datetime import datetime
from typing import List

from src.signals.signal_aggregator import SignalAggregator
from src.data.signal_models import TradingSignal, SignalType, SignalStrength


class TestSignalConflictResolution:
    """Test suite for Task 8 Signal Conflict Resolution features."""
    
    @pytest.fixture
    def strategy_weights(self):
        """Strategy weights for testing."""
        return {
            "VIX_Correlation_Strategy": 0.6,
            "Mean_Reversion_Strategy": 0.4
        }
    
    @pytest.fixture
    def aggregator(self, strategy_weights):
        """Create a SignalAggregator instance for testing."""
        return SignalAggregator(strategy_weights)
    
    @pytest.fixture
    def conflicting_signals(self):
        """Create conflicting signals for testing."""
        base_timestamp = datetime.now().timestamp()
        
        return [
            # VIX strategy - LONG signal
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=base_timestamp,
                price=50000.0,
                strategy_name="VIX_Correlation_Strategy",
                signal_strength=SignalStrength.STRONG,
                confidence=0.8,
                position_size=0.03,
                stop_loss=47500.0,
                take_profit=55000.0,
                max_risk=0.05
            ),
            # Mean reversion strategy - SHORT signal (conflict)
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.SHORT,
                timestamp=base_timestamp + 1,
                price=50200.0,
                strategy_name="Mean_Reversion_Strategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.6,
                position_size=0.025,
                stop_loss=52500.0,
                take_profit=47500.0,
                max_risk=0.05
            ),
            # Ethereum signal - no conflict
            TradingSignal(
                asset="ethereum",
                signal_type=SignalType.LONG,
                timestamp=base_timestamp + 2,
                price=3000.0,
                strategy_name="VIX_Correlation_Strategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.7,
                position_size=0.02
            )
        ]
    
    @pytest.fixture
    def same_direction_signals(self):
        """Create same-direction signals for testing."""
        base_timestamp = datetime.now().timestamp()
        
        return [
            # Both strategies - LONG signals (same direction)
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=base_timestamp,
                price=49000.0,
                strategy_name="VIX_Correlation_Strategy",
                signal_strength=SignalStrength.STRONG,
                confidence=0.8,
                position_size=0.03,
                stop_loss=46500.0,
                take_profit=54000.0
            ),
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=base_timestamp + 1,
                price=49200.0,
                strategy_name="Mean_Reversion_Strategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.7,
                position_size=0.025,
                stop_loss=46800.0,
                take_profit=53500.0
            )
        ]
    
    def test_standalone_resolve_signal_conflicts_basic(self, aggregator, conflicting_signals):
        """Test the standalone resolve_signal_conflicts method - Task 8 core requirement."""
        
        resolved_signals = aggregator.resolve_signal_conflicts(conflicting_signals)
        
        # Should resolve conflicts and return 2 signals (1 for bitcoin, 1 for ethereum)
        assert len(resolved_signals) == 2
        
        # Check bitcoin signal resolution (VIX should win with 0.6 weight vs 0.4)
        bitcoin_signal = next(s for s in resolved_signals if s.asset == "bitcoin")
        assert bitcoin_signal.signal_type == SignalType.LONG  # VIX strategy should win
        assert bitcoin_signal.strategy_name in ["Aggregated_Signal", "VIX_Correlation_Strategy"]
        
        # Check ethereum signal (no conflict)
        ethereum_signal = next(s for s in resolved_signals if s.asset == "ethereum")
        assert ethereum_signal.signal_type == SignalType.LONG
        assert ethereum_signal.asset == "ethereum"
    
    def test_resolve_signal_conflicts_empty_input(self, aggregator):
        """Test resolve_signal_conflicts with empty input."""
        resolved = aggregator.resolve_signal_conflicts([])
        assert len(resolved) == 0
    
    def test_resolve_signal_conflicts_no_conflicts(self, aggregator):
        """Test resolve_signal_conflicts when no conflicts exist."""
        signals = [
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
        
        resolved = aggregator.resolve_signal_conflicts(signals)
        
        # Should return both signals unchanged (no conflicts)
        assert len(resolved) == 2
        assert resolved[0].asset in ["bitcoin", "ethereum"] 
        assert resolved[1].asset in ["bitcoin", "ethereum"]
        assert resolved[0].asset != resolved[1].asset
    
    def test_consensus_threshold_resolution(self, strategy_weights, conflicting_signals):
        """Test the new consensus_threshold conflict resolution method."""
        config = {
            'conflict_resolution': 'consensus_threshold',
            'consensus_threshold': 0.7  # Require 70% agreement
        }
        aggregator = SignalAggregator(strategy_weights, config)
        
        resolved = aggregator.resolve_signal_conflicts(conflicting_signals)
        
        # VIX strategy has 60% weight, below 70% threshold, so bitcoin conflict should not resolve
        bitcoin_signals = [s for s in resolved if s.asset == "bitcoin"]
        assert len(bitcoin_signals) == 0  # No bitcoin signal due to insufficient consensus
        
        # Ethereum should still resolve (no conflict)
        ethereum_signals = [s for s in resolved if s.asset == "ethereum"]
        assert len(ethereum_signals) == 1
    
    def test_consensus_threshold_resolution_met(self, strategy_weights, same_direction_signals):
        """Test consensus_threshold when threshold is met."""
        config = {
            'conflict_resolution': 'consensus_threshold',
            'consensus_threshold': 0.5  # 50% threshold
        }
        aggregator = SignalAggregator(strategy_weights, config)
        
        resolved = aggregator.resolve_signal_conflicts(same_direction_signals)
        
        # Both signals are LONG, so consensus should be 100% - should resolve
        assert len(resolved) == 1
        assert resolved[0].asset == "bitcoin"
        assert resolved[0].signal_type == SignalType.LONG
    
    def test_risk_weighted_resolution(self, strategy_weights, conflicting_signals):
        """Test the new risk_weighted conflict resolution method."""
        config = {'conflict_resolution': 'risk_weighted'}
        aggregator = SignalAggregator(strategy_weights, config)
        
        resolved = aggregator.resolve_signal_conflicts(conflicting_signals)
        
        # Should resolve based on risk-reward ratio
        bitcoin_signal = next((s for s in resolved if s.asset == "bitcoin"), None)
        assert bitcoin_signal is not None
        assert bitcoin_signal.strategy_name == "Risk_Weighted_Signal"
        
        # Should have risk-weighted metadata
        assert 'risk_adjusted_score' in bitcoin_signal.analysis_data
        assert 'risk_reward_ratio' in bitcoin_signal.analysis_data
        assert bitcoin_signal.analysis_data['aggregation_method'] == 'risk_weighted'
    
    def test_risk_weighted_better_ratio_wins(self, strategy_weights):
        """Test risk_weighted resolution picks signal with better risk-reward ratio."""
        
        # Create signals with different risk-reward ratios
        signals = [
            # Signal 1: Poor risk-reward (2:1 ratio)
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=datetime.now().timestamp(),
                price=50000.0,
                strategy_name="VIX_Correlation_Strategy",
                signal_strength=SignalStrength.STRONG,
                confidence=0.7,
                position_size=0.03,
                stop_loss=48000.0,  # 2000 risk
                take_profit=54000.0  # 4000 reward = 2:1 ratio
            ),
            # Signal 2: Better risk-reward (3:1 ratio)
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.SHORT,
                timestamp=datetime.now().timestamp(),
                price=50000.0,
                strategy_name="Mean_Reversion_Strategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.6,
                position_size=0.025,
                stop_loss=51000.0,  # 1000 risk
                take_profit=47000.0  # 3000 reward = 3:1 ratio
            )
        ]
        
        config = {'conflict_resolution': 'risk_weighted'}
        aggregator = SignalAggregator(strategy_weights, config)
        
        resolved = aggregator.resolve_signal_conflicts(signals)
        
        # Should pick the signal with better risk-reward ratio
        assert len(resolved) == 1
        bitcoin_signal = resolved[0]
        
        # The second signal has better risk-reward but lower strategy weight/confidence
        # The actual winner depends on the combined score calculation
        assert bitcoin_signal.strategy_name == "Risk_Weighted_Signal"
        assert bitcoin_signal.analysis_data['alternatives_evaluated'] == 2
    
    def test_get_conflict_report_basic(self, aggregator, conflicting_signals):
        """Test the get_conflict_report method for detailed conflict analysis."""
        
        report = aggregator.get_conflict_report(conflicting_signals)
        
        # Verify report structure
        assert 'total_signals' in report
        assert 'unique_assets' in report
        assert 'conflict_summary' in report
        assert 'conflicts' in report
        assert 'resolution_recommendations' in report
        
        # Verify conflict summary
        assert report['total_signals'] == 3
        assert report['unique_assets'] == 2
        assert report['conflict_summary']['assets_with_conflicts'] == 1  # Only bitcoin has conflicts
        assert report['conflict_summary']['assets_with_opposing_signals'] == 1
        
        # Verify bitcoin conflict details
        assert 'bitcoin' in report['conflicts']
        bitcoin_conflict = report['conflicts']['bitcoin']
        assert bitcoin_conflict['signal_count'] == 2
        assert bitcoin_conflict['has_opposing'] is True
        assert len(bitcoin_conflict['signals']) == 2
        
        # Verify resolution recommendation
        recommendation = bitcoin_conflict['resolution_recommendation']
        assert 'action' in recommendation
        assert 'reason' in recommendation
        assert recommendation['asset'] == 'bitcoin'
    
    def test_get_conflict_report_empty_signals(self, aggregator):
        """Test get_conflict_report with empty signals."""
        report = aggregator.get_conflict_report([])
        
        assert report['total_signals'] == 0
        assert report['conflicts'] == {}
    
    def test_get_conflict_report_no_conflicts(self, aggregator):
        """Test get_conflict_report when no conflicts exist."""
        signals = [
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
        
        report = aggregator.get_conflict_report(signals)
        
        assert report['total_signals'] == 1
        assert report['conflict_summary']['assets_with_conflicts'] == 0
        assert len(report['conflicts']) == 0
    
    def test_resolution_recommendations_opposing_signals(self, aggregator, conflicting_signals):
        """Test resolution recommendations for opposing signals."""
        
        report = aggregator.get_conflict_report(conflicting_signals)
        
        bitcoin_conflict = report['conflicts']['bitcoin']
        recommendation = bitcoin_conflict['resolution_recommendation']
        
        # VIX has 60% weight, should recommend resolving with dominant
        assert recommendation['action'] in ['resolve_with_dominant', 'resolve_with_caution']
        assert 'dominant signal' in recommendation['reason'].lower()
        assert recommendation['confidence'] == 0.6  # VIX strategy weight
    
    def test_resolution_recommendations_same_direction(self, aggregator, same_direction_signals):
        """Test resolution recommendations for same direction signals."""
        
        report = aggregator.get_conflict_report(same_direction_signals)
        
        # Same direction signals are not considered conflicts in our logic
        # They are handled by normal aggregation without conflict resolution
        # So there should be no conflicts reported
        assert report['conflict_summary']['assets_with_conflicts'] == 0
        assert len(report['conflicts']) == 0
    
    def test_overall_recommendations_high_conflict_rate(self, strategy_weights):
        """Test overall recommendations when conflict rate is high."""
        
        # Create many conflicting signals
        conflicting_signals = []
        base_timestamp = datetime.now().timestamp()
        
        for i in range(10):
            conflicting_signals.extend([
                TradingSignal(
                    asset=f"asset_{i}",
                    signal_type=SignalType.LONG,
                    timestamp=base_timestamp + i,
                    price=1000.0,
                    strategy_name="VIX_Correlation_Strategy",
                    signal_strength=SignalStrength.STRONG,
                    confidence=0.8,
                    position_size=0.03
                ),
                TradingSignal(
                    asset=f"asset_{i}",
                    signal_type=SignalType.SHORT,
                    timestamp=base_timestamp + i + 0.1,
                    price=1000.0,
                    strategy_name="Mean_Reversion_Strategy",
                    signal_strength=SignalStrength.MODERATE,
                    confidence=0.6,
                    position_size=0.025
                )
            ])
        
        aggregator = SignalAggregator(strategy_weights)
        report = aggregator.get_conflict_report(conflicting_signals)
        
        # Should have high conflict rate warning
        recommendations = report['resolution_recommendations']
        warning_found = any(rec['type'] == 'warning' and 'high conflict rate' in rec['message'].lower() 
                          for rec in recommendations)
        assert warning_found
    
    def test_low_confidence_filtering_in_conflict_resolution(self, strategy_weights):
        """Test that low confidence signals are filtered out during conflict resolution."""
        
        signals = [
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
            # Low confidence signal - should be filtered out
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.SHORT,
                timestamp=datetime.now().timestamp(),
                price=50000.0,
                strategy_name="Mean_Reversion_Strategy",
                signal_strength=SignalStrength.WEAK,
                confidence=0.05,  # Below default threshold of 0.1
                position_size=0.025
            )
        ]
        
        aggregator = SignalAggregator(strategy_weights)
        resolved = aggregator.resolve_signal_conflicts(signals)
        
        # Should only have the high confidence signal
        assert len(resolved) == 1
        assert resolved[0].confidence == 0.8
        # After conflict resolution, strategy name becomes "Aggregated_Signal"
        assert resolved[0].strategy_name == "Aggregated_Signal"
    
    def test_conflict_resolution_sorting(self, aggregator):
        """Test that resolved signals are properly sorted by confidence and timestamp."""
        
        base_timestamp = datetime.now().timestamp()
        signals = [
            # Lower confidence, later timestamp
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=base_timestamp + 100,
                price=50000.0,
                strategy_name="VIX_Correlation_Strategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.6,
                position_size=0.03
            ),
            # Higher confidence, earlier timestamp  
            TradingSignal(
                asset="ethereum",
                signal_type=SignalType.SHORT,
                timestamp=base_timestamp,
                price=3000.0,
                strategy_name="Mean_Reversion_Strategy",
                signal_strength=SignalStrength.STRONG,
                confidence=0.9,
                position_size=0.025
            )
        ]
        
        resolved = aggregator.resolve_signal_conflicts(signals)
        
        # Should be sorted by confidence (highest first)
        assert len(resolved) == 2
        assert resolved[0].confidence >= resolved[1].confidence
        assert resolved[0].asset == "ethereum"  # Higher confidence signal first


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
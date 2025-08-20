"""
Signal Aggregator for combining and resolving signals from multiple trading strategies.
Handles weighted combination, conflict resolution, and position size optimization.
"""

import logging
import asyncio
import threading
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime
import numpy as np

from src.data.signal_models import TradingSignal, SignalType, SignalStrength
from src.utils.discord_webhook import DiscordAlertManager
from src.utils.config_utils import get_discord_config_from_env, validate_discord_config


class SignalAggregator:
    """
    Aggregates trading signals from multiple strategies using configurable weights.
    
    Features:
    - Weighted signal combination based on strategy performance/confidence
    - Conflict resolution when strategies disagree on same asset
    - Position size optimization through weighted averaging
    - Signal deduplication and prioritization
    """
    
    def __init__(self, strategy_weights: Dict[str, float], aggregation_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Signal Aggregator.
        
        Args:
            strategy_weights: Dictionary mapping strategy names to their weights
                             Example: {"VIX_Correlation_Strategy": 0.6, "Mean_Reversion_Strategy": 0.4}
            aggregation_config: Optional configuration for aggregation behavior
        """
        self.logger = logging.getLogger(__name__)
        
        # Normalize strategy weights to sum to 1.0
        total_weight = sum(strategy_weights.values())
        if total_weight <= 0:
            raise ValueError("Strategy weights must sum to a positive value")
        
        self.strategy_weights = {name: weight / total_weight for name, weight in strategy_weights.items()}
        
        # Set aggregation configuration with defaults
        default_config = {
            'min_confidence_threshold': 0.1,  # Minimum confidence to include signal
            'conflict_resolution': 'weighted_average',  # 'weighted_average', 'strongest_wins', 'conservative'
            'max_position_size': 0.10,  # Maximum position size cap
            'min_position_size': 0.005,  # Minimum position size threshold
            'require_majority_agreement': False,  # Require >50% weight agreement for signal
            'signal_timeout_hours': 24,  # How long signals are valid
            'discord_alerts': os.getenv('DISCORD_ALERTS_ENABLED', 'false').lower() == 'true',  # Enable Discord alerts
            'discord_webhook_url': os.getenv('DISCORD_WEBHOOK_URL', ''),  # Discord webhook URL
            'discord_config': {  # Discord alert configuration
                'min_confidence': float(os.getenv('DISCORD_MIN_CONFIDENCE', '0.6')),
                'min_strength': os.getenv('DISCORD_MIN_STRENGTH', 'WEAK'),
                'rate_limit': int(os.getenv('DISCORD_RATE_LIMIT_SECONDS', '60')),
                'enabled_assets': ['bitcoin', 'ethereum'],
                'enabled_signal_types': ['LONG', 'SHORT']
            },
        }
        
        self.config = {**default_config, **(aggregation_config or {})}
        
        # Initialize Discord alert manager if configured
        self.discord_manager = None
        self._discord_executor = None
        
        discord_enabled = self.config.get('discord_alerts', False)
        
        if discord_enabled:
            # Get Discord configuration from environment variables
            discord_config = get_discord_config_from_env()
            
            # Validate the configuration
            if validate_discord_config(discord_config):
                try:
                    self.discord_manager = DiscordAlertManager(
                        discord_config['webhook_url'],
                        discord_config
                    )
                    # Initialize thread pool executor for Discord alerts
                    self._discord_executor = ThreadPoolExecutor(
                        max_workers=2, 
                        thread_name_prefix="discord-alerts"
                    )
                    self.logger.info("Discord alert manager initialized with thread pool")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Discord alert manager: {e}")
                    # Still initialize executor for consistency
                    self._discord_executor = ThreadPoolExecutor(
                        max_workers=2, 
                        thread_name_prefix="discord-alerts"
                    )
            else:
                # Initialize thread pool executor even without Discord for consistency
                self._discord_executor = ThreadPoolExecutor(
                    max_workers=2, 
                    thread_name_prefix="discord-alerts"
                )
                self.logger.warning("Discord alerts enabled but configuration is invalid. Check DISCORD_WEBHOOK_URL in .env file.")
        else:
            # Initialize thread pool executor even without Discord for consistency
            self._discord_executor = ThreadPoolExecutor(
                max_workers=2, 
                thread_name_prefix="discord-alerts"
            )
        
        self.logger.info(f"Signal Aggregator initialized with {len(self.strategy_weights)} strategies")
        self.logger.debug(f"Strategy weights: {self.strategy_weights}")
        self.logger.debug(f"Aggregation config: {self.config}")
    
    def aggregate_signals(self, strategy_signals: Dict[str, List[TradingSignal]]) -> List[TradingSignal]:
        """
        Aggregate signals from multiple strategies.
        
        Args:
            strategy_signals: Dictionary mapping strategy names to their signal lists
                            Example: {"VIX_Correlation_Strategy": [signal1, signal2], 
                                    "Mean_Reversion_Strategy": [signal3]}
        
        Returns:
            List of aggregated TradingSignal objects with resolved conflicts
        """
        if not strategy_signals:
            self.logger.warning("No strategy signals provided for aggregation")
            return []
        
        # Validate strategy names
        unknown_strategies = set(strategy_signals.keys()) - set(self.strategy_weights.keys())
        if unknown_strategies:
            self.logger.warning(f"Unknown strategies provided: {unknown_strategies}")
        
        # Group signals by asset
        signals_by_asset = self._group_signals_by_asset(strategy_signals)
        
        # Aggregate signals for each asset
        aggregated_signals = []
        
        for asset, asset_signals in signals_by_asset.items():
            try:
                aggregated_signal = self._aggregate_asset_signals(asset, asset_signals)
                
                if aggregated_signal:
                    aggregated_signals.append(aggregated_signal)
                    
            except Exception as e:
                self.logger.error(f"Failed to aggregate signals for {asset}: {e}")
                continue
        
        # Sort by confidence and timestamp (handle different timestamp types)
        def sort_key(signal):
            # Ensure timestamp is numeric for sorting
            timestamp = signal.timestamp
            if isinstance(timestamp, str):
                try:
                    timestamp = int(timestamp)
                except (ValueError, TypeError):
                    timestamp = 0
            elif not isinstance(timestamp, (int, float)):
                timestamp = 0
            
            return (-signal.confidence, -timestamp)
        
        aggregated_signals.sort(key=sort_key)
        
        # Send Discord alerts if configured
        if self.discord_manager and aggregated_signals:
            self._schedule_discord_alerts(aggregated_signals)
        
        self.logger.info(f"Aggregated {len(aggregated_signals)} signals from {len(strategy_signals)} strategies")
        
        return aggregated_signals
    
    def _group_signals_by_asset(self, strategy_signals: Dict[str, List[TradingSignal]]) -> Dict[str, List[TradingSignal]]:
        """Group all signals by asset for conflict resolution."""
        signals_by_asset = defaultdict(list)
        
        for strategy_name, signals in strategy_signals.items():
            # Only include strategies we have weights for
            if strategy_name not in self.strategy_weights:
                continue
                
            for signal in signals:
                # Filter by minimum confidence threshold
                if signal.confidence >= self.config['min_confidence_threshold']:
                    signals_by_asset[signal.symbol].append(signal)
        
        return dict(signals_by_asset)
    
    def _aggregate_asset_signals(self, asset: str, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """
        Aggregate signals for a single asset.
        
        Args:
            asset: Asset name
            signals: List of signals for this asset from different strategies
            
        Returns:
            Aggregated signal or None if no valid aggregation possible
        """
        if not signals:
            return None
        
        # Analyze signal conflicts
        signal_analysis = self._analyze_signal_conflicts(signals)
        
        # Apply conflict resolution strategy
        if self.config['conflict_resolution'] == 'weighted_average':
            return self._resolve_via_weighted_average(asset, signals, signal_analysis)
        elif self.config['conflict_resolution'] == 'strongest_wins':
            return self._resolve_via_strongest_signal(signals)
        elif self.config['conflict_resolution'] == 'conservative':
            return self._resolve_via_conservative_approach(asset, signals, signal_analysis)
        else:
            raise ValueError(f"Unknown conflict resolution method: {self.config['conflict_resolution']}")
    
    def _analyze_signal_conflicts(self, signals: List[TradingSignal]) -> Dict[str, Any]:
        """Analyze conflicts and agreements among signals."""
        signal_types = [signal.signal_type for signal in signals]
        strategy_weights_sum = sum(self.strategy_weights.get(signal.strategy_name, 0) for signal in signals)
        
        # Calculate weighted vote for each signal type
        type_weights = defaultdict(float)
        for signal in signals:
            strategy_weight = self.strategy_weights.get(signal.strategy_name, 0)
            type_weights[signal.signal_type] += strategy_weight
        
        # Determine dominant signal type
        dominant_type = max(type_weights.items(), key=lambda x: x[1]) if type_weights else (SignalType.HOLD, 0)
        
        # Check for conflicts
        unique_types = set(signal_types)
        has_conflict = len(unique_types) > 1 and SignalType.HOLD not in unique_types
        
        # Check for opposing signals (LONG vs SHORT)
        has_opposing = (SignalType.LONG in unique_types and SignalType.SHORT in unique_types)
        
        return {
            'signal_count': len(signals),
            'unique_types': unique_types,
            'has_conflict': has_conflict,
            'has_opposing': has_opposing,
            'dominant_type': dominant_type[0],
            'dominant_weight': dominant_type[1],
            'type_weights': dict(type_weights),
            'strategy_weights_sum': strategy_weights_sum
        }
    
    def _resolve_via_weighted_average(self, asset: str, signals: List[TradingSignal], analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """Resolve conflicts using weighted averaging of signals."""
        
        # If opposing signals, check if we meet majority requirement
        if analysis['has_opposing'] and self.config['require_majority_agreement']:
            if analysis['dominant_weight'] <= 0.5:
                self.logger.debug(f"No majority agreement for {asset}, skipping signal")
                return None
        
        # Use dominant signal type
        final_signal_type = analysis['dominant_type']
        
        if final_signal_type == SignalType.HOLD:
            return None
        
        # Calculate weighted averages for signal parameters
        total_weight = 0
        weighted_confidence = 0
        weighted_position_size = 0
        weighted_price = 0
        weighted_stop_loss = 0
        weighted_take_profit = 0
        weighted_max_risk = 0
        
        # Collect analysis data
        combined_analysis_data = {}
        latest_timestamp = 0
        
        # Only include signals that match the dominant type (or are neutral)
        relevant_signals = [s for s in signals if s.signal_type == final_signal_type or s.signal_type == SignalType.HOLD]
        
        for signal in relevant_signals:
            strategy_weight = self.strategy_weights.get(signal.strategy_name, 0)
            
            # Weight by both strategy weight and signal confidence
            effective_weight = strategy_weight * signal.confidence
            
            total_weight += effective_weight
            weighted_confidence += signal.confidence * effective_weight
            weighted_position_size += signal.position_size * effective_weight
            weighted_price += signal.price * effective_weight
            
            # Handle optional risk management parameters
            if signal.stop_loss:
                weighted_stop_loss += signal.stop_loss * effective_weight
            if signal.take_profit:
                weighted_take_profit += signal.take_profit * effective_weight
            if signal.max_risk:
                weighted_max_risk += signal.max_risk * effective_weight
            
            # Combine analysis data
            if signal.analysis_data:
                for key, value in signal.analysis_data.items():
                    if key not in combined_analysis_data:
                        combined_analysis_data[key] = []
                    combined_analysis_data[key].append({
                        'strategy': signal.strategy_name,
                        'value': value,
                        'weight': strategy_weight
                    })
            
            # Handle timestamp comparison safely
            current_timestamp = signal.timestamp
            if isinstance(current_timestamp, str):
                try:
                    current_timestamp = int(current_timestamp)
                except (ValueError, TypeError):
                    current_timestamp = 0
            elif not isinstance(current_timestamp, (int, float)):
                current_timestamp = 0
            
            latest_timestamp = max(latest_timestamp, current_timestamp)
        
        if total_weight == 0:
            return None
        
        # Calculate final weighted values
        final_confidence = weighted_confidence / total_weight
        final_position_size = weighted_position_size / total_weight
        final_price = weighted_price / total_weight
        
        # Apply position size constraints
        final_position_size = max(self.config['min_position_size'], 
                                min(self.config['max_position_size'], final_position_size))
        
        # Calculate risk management parameters
        final_stop_loss = weighted_stop_loss / total_weight if weighted_stop_loss > 0 else None
        final_take_profit = weighted_take_profit / total_weight if weighted_take_profit > 0 else None
        final_max_risk = weighted_max_risk / total_weight if weighted_max_risk > 0 else None
        
        # Determine final signal strength based on confidence and agreement
        if final_confidence > 0.7 and analysis['dominant_weight'] > 0.7:
            final_strength = SignalStrength.STRONG
        elif final_confidence > 0.5 and analysis['dominant_weight'] > 0.5:
            final_strength = SignalStrength.MODERATE
        else:
            final_strength = SignalStrength.WEAK
        
        # Create aggregated analysis data
        aggregated_analysis = {
            'aggregation_method': 'weighted_average',
            'strategies_combined': [s.strategy_name for s in relevant_signals],
            'strategy_weights': {s.strategy_name: self.strategy_weights.get(s.strategy_name, 0) for s in relevant_signals},
            'signal_conflict_analysis': analysis,
            'total_effective_weight': total_weight,
            'original_signals_count': len(signals),
            'relevant_signals_count': len(relevant_signals),
            'combined_data': combined_analysis_data
        }
        
        # Create aggregated signal
        from src.data.signal_models import SignalDirection
        
        aggregated_signal = TradingSignal(
            symbol=asset,
            signal_type=final_signal_type,
            direction=SignalDirection.BUY if final_signal_type == SignalType.LONG else SignalDirection.SELL,
            timestamp=latest_timestamp,
            price=final_price,
            strategy_name="Aggregated_Signal",
            signal_strength=final_strength,
            confidence=final_confidence,
            position_size=final_position_size,
            stop_loss=final_stop_loss,
            take_profit=final_take_profit,
            max_risk=final_max_risk,
            analysis_data=aggregated_analysis
        )
        
        self.logger.debug(f"Aggregated {len(relevant_signals)} signals for {asset}: {final_signal_type.value} "
                         f"(confidence: {final_confidence:.3f}, size: {final_position_size:.3f})")
        
        return aggregated_signal
    
    def _resolve_via_strongest_signal(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """Resolve conflicts by selecting the strongest signal (highest confidence * strategy weight)."""
        
        best_signal = None
        best_score = 0
        
        for signal in signals:
            strategy_weight = self.strategy_weights.get(signal.strategy_name, 0)
            score = signal.confidence * strategy_weight
            
            if score > best_score:
                best_score = score
                best_signal = signal
        
        if best_signal:
            # Create a copy with aggregation metadata
            aggregated_analysis = {
                'aggregation_method': 'strongest_wins',
                'selected_strategy': best_signal.strategy_name,
                'selection_score': best_score,
                'alternatives_count': len(signals) - 1
            }
            
            # Update analysis data
            updated_analysis = {**(best_signal.analysis_data or {}), **aggregated_analysis}
            
            return TradingSignal(
                symbol=best_signal.symbol,
                signal_type=best_signal.signal_type,
                direction=best_signal.direction,
                timestamp=best_signal.timestamp,
                price=best_signal.price,
                strategy_name="Aggregated_Signal",
                signal_strength=best_signal.signal_strength,
                confidence=best_signal.confidence,
                position_size=min(self.config['max_position_size'], best_signal.position_size),
                stop_loss=best_signal.stop_loss,
                take_profit=best_signal.take_profit,
                max_risk=best_signal.max_risk,
                analysis_data=updated_analysis
            )
        
        return None
    
    def _resolve_via_conservative_approach(self, asset: str, signals: List[TradingSignal], analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """Resolve conflicts using conservative approach - only act on strong agreement."""
        
        # Conservative approach: only generate signal if there's strong agreement
        if analysis['has_opposing']:
            self.logger.debug(f"Conservative mode: Opposing signals for {asset}, no action taken")
            return None
        
        if analysis['dominant_weight'] < 0.6:
            self.logger.debug(f"Conservative mode: Insufficient agreement for {asset} ({analysis['dominant_weight']:.2f})")
            return None
        
        # If we pass conservative checks, use weighted average
        return self._resolve_via_weighted_average(asset, signals, analysis)
    
    def get_aggregation_stats(self, strategy_signals: Dict[str, List[TradingSignal]]) -> Dict[str, Any]:
        """
        Get statistics about signal aggregation without actually aggregating.
        Useful for analysis and debugging.
        """
        stats = {
            'strategy_count': len(strategy_signals),
            'total_signals': sum(len(signals) for signals in strategy_signals.values()),
            'signals_per_strategy': {name: len(signals) for name, signals in strategy_signals.items()},
            'strategy_weights': self.strategy_weights.copy(),
            'config': self.config.copy()
        }
        
        # Analyze potential conflicts
        signals_by_asset = self._group_signals_by_asset(strategy_signals)
        
        conflict_analysis = {}
        for asset, signals in signals_by_asset.items():
            if len(signals) > 1:
                analysis = self._analyze_signal_conflicts(signals)
                conflict_analysis[asset] = analysis
        
        stats['conflict_analysis'] = conflict_analysis
        stats['assets_with_conflicts'] = len(conflict_analysis)
        stats['total_unique_assets'] = len(signals_by_asset)
        
        return stats
    
    def resolve_signal_conflicts(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Standalone method to resolve conflicting signals (Task 8).
        
        This method provides direct conflict resolution without full aggregation,
        useful for external conflict analysis and resolution.
        
        Args:
            signals: List of potentially conflicting TradingSignal objects
            
        Returns:
            List of conflict-free TradingSignal objects
        """
        if not signals:
            return []
        
        # Group signals by asset for conflict resolution
        signals_by_asset = defaultdict(list)
        for signal in signals:
            signals_by_asset[signal.symbol].append(signal)
        
        resolved_signals = []
        
        for asset, asset_signals in signals_by_asset.items():
            try:
                # If only one signal for this asset, no conflict
                if len(asset_signals) == 1:
                    resolved_signals.append(asset_signals[0])
                    continue
                
                # Filter signals by minimum confidence threshold
                qualified_signals = [s for s in asset_signals 
                                   if s.confidence >= self.config['min_confidence_threshold']]
                
                if not qualified_signals:
                    self.logger.debug(f"No qualified signals for {asset} after confidence filtering")
                    continue
                
                # Analyze conflicts
                conflict_analysis = self._analyze_signal_conflicts(qualified_signals)
                
                # Resolve conflicts based on configuration
                resolved_signal = self._resolve_asset_conflicts(asset, qualified_signals, conflict_analysis)
                
                if resolved_signal:
                    resolved_signals.append(resolved_signal)
                    
            except Exception as e:
                self.logger.error(f"Failed to resolve conflicts for {asset}: {e}")
                continue
        
        # Sort by confidence and timestamp for consistent output
        resolved_signals.sort(key=lambda s: (-s.confidence, -s.timestamp))
        
        self.logger.info(f"Resolved conflicts for {len(signals)} signals → {len(resolved_signals)} conflict-free signals")
        
        return resolved_signals
    
    def _resolve_asset_conflicts(self, asset: str, signals: List[TradingSignal], analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Enhanced conflict resolution for a single asset with multiple resolution policies.
        
        Args:
            asset: Asset name
            signals: List of signals for this asset
            analysis: Pre-computed conflict analysis
            
        Returns:
            Resolved signal or None if no resolution possible
        """
        # Log conflict details
        if analysis['has_conflict']:
            self.logger.debug(f"Resolving conflict for {asset}: {analysis['signal_count']} signals, "
                             f"types: {[t.value for t in analysis['unique_types']]}")
        
        # Apply enhanced conflict resolution policies
        resolution_method = self.config.get('conflict_resolution', 'weighted_average')
        
        if resolution_method == 'weighted_average':
            return self._resolve_via_weighted_average(asset, signals, analysis)
        elif resolution_method == 'strongest_wins':
            return self._resolve_via_strongest_signal(signals)
        elif resolution_method == 'conservative':
            return self._resolve_via_conservative_approach(asset, signals, analysis)
        elif resolution_method == 'consensus_threshold':
            return self._resolve_via_consensus_threshold(asset, signals, analysis)
        elif resolution_method == 'risk_weighted':
            return self._resolve_via_risk_weighted(asset, signals, analysis)
        else:
            self.logger.warning(f"Unknown conflict resolution method: {resolution_method}, using weighted_average")
            return self._resolve_via_weighted_average(asset, signals, analysis)
    
    def _resolve_via_consensus_threshold(self, asset: str, signals: List[TradingSignal], analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Resolve conflicts using consensus threshold - requires minimum percentage agreement.
        
        Args:
            asset: Asset name
            signals: List of signals for this asset
            analysis: Pre-computed conflict analysis
            
        Returns:
            Resolved signal or None if consensus not reached
        """
        consensus_threshold = self.config.get('consensus_threshold', 0.7)  # 70% agreement required
        
        # Check if dominant signal type meets consensus threshold
        if analysis['dominant_weight'] < consensus_threshold:
            self.logger.debug(f"Consensus threshold not met for {asset}: {analysis['dominant_weight']:.2f} < {consensus_threshold}")
            return None
        
        # If consensus reached, use weighted average approach
        return self._resolve_via_weighted_average(asset, signals, analysis)
    
    def _resolve_via_risk_weighted(self, asset: str, signals: List[TradingSignal], analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Resolve conflicts using risk-weighted approach - prioritizes signals with better risk-reward ratio.
        
        Args:
            asset: Asset name
            signals: List of signals for this asset
            analysis: Pre-computed conflict analysis
            
        Returns:
            Resolved signal or None if no suitable signal found
        """
        # Calculate risk-adjusted score for each signal
        risk_scored_signals = []
        
        for signal in signals:
            strategy_weight = self.strategy_weights.get(signal.strategy_name, 0)
            
            # Calculate risk-reward ratio
            risk_reward_ratio = 1.0  # Default if no risk management data
            
            if signal.stop_loss and signal.take_profit:
                downside_risk = abs(signal.price - signal.stop_loss)
                upside_potential = abs(signal.take_profit - signal.price)
                
                if downside_risk > 0:
                    risk_reward_ratio = upside_potential / downside_risk
            
            # Risk-adjusted score: confidence * strategy_weight * risk_reward_ratio
            risk_score = signal.confidence * strategy_weight * min(risk_reward_ratio, 3.0)  # Cap at 3:1 ratio
            
            risk_scored_signals.append((signal, risk_score))
        
        # Select signal with highest risk-adjusted score
        if not risk_scored_signals:
            return None
        
        best_signal, best_score = max(risk_scored_signals, key=lambda x: x[1])
        
        # Create resolved signal with risk-weighted metadata
        aggregated_analysis = {
            'aggregation_method': 'risk_weighted',
            'selected_strategy': best_signal.strategy_name,
            'risk_adjusted_score': best_score,
            'risk_reward_ratio': best_score / (best_signal.confidence * self.strategy_weights.get(best_signal.strategy_name, 0)),
            'alternatives_evaluated': len(signals),
            'conflict_analysis': analysis
        }
        
        # Update analysis data
        updated_analysis = {**(best_signal.analysis_data or {}), **aggregated_analysis}
        
        resolved_signal = TradingSignal(
            symbol=best_signal.symbol,
            signal_type=best_signal.signal_type,
            direction=best_signal.direction,
            timestamp=best_signal.timestamp,
            price=best_signal.price,
            strategy_name="Risk_Weighted_Signal",
            signal_strength=best_signal.signal_strength,
            confidence=best_signal.confidence,
            position_size=min(self.config['max_position_size'], best_signal.position_size),
            stop_loss=best_signal.stop_loss,
            take_profit=best_signal.take_profit,
            max_risk=best_signal.max_risk,
            analysis_data=updated_analysis
        )
        
        self.logger.debug(f"Risk-weighted resolution for {asset}: selected {best_signal.strategy_name} "
                         f"(score: {best_score:.3f})")
        
        return resolved_signal
    
    def get_conflict_report(self, signals: List[TradingSignal]) -> Dict[str, Any]:
        """
        Generate detailed conflict analysis report for given signals.
        
        Args:
            signals: List of TradingSignal objects to analyze
            
        Returns:
            Dictionary containing detailed conflict analysis
        """
        if not signals:
            return {'total_signals': 0, 'conflicts': {}}
        
        # Group signals by asset
        signals_by_asset = defaultdict(list)
        for signal in signals:
            signals_by_asset[signal.symbol].append(signal)
        
        conflict_report = {
            'total_signals': len(signals),
            'unique_assets': len(signals_by_asset),
            'conflict_summary': {
                'assets_with_conflicts': 0,
                'assets_with_opposing_signals': 0,
                'total_conflicts': 0,
                'resolution_required': 0
            },
            'conflicts': {},
            'resolution_recommendations': []
        }
        
        for asset, asset_signals in signals_by_asset.items():
            if len(asset_signals) <= 1:
                continue  # No conflicts possible
            
            # Analyze conflicts for this asset
            analysis = self._analyze_signal_conflicts(asset_signals)
            
            if analysis['has_conflict']:
                conflict_report['conflict_summary']['assets_with_conflicts'] += 1
                conflict_report['conflict_summary']['total_conflicts'] += 1
                
                if analysis['has_opposing']:
                    conflict_report['conflict_summary']['assets_with_opposing_signals'] += 1
                
                # Detailed conflict information
                conflict_info = {
                    'signal_count': analysis['signal_count'],
                    'signal_types': [t.value for t in analysis['unique_types']],
                    'has_opposing': analysis['has_opposing'],
                    'dominant_type': analysis['dominant_type'].value,
                    'dominant_weight': analysis['dominant_weight'],
                    'strategy_weights': analysis['strategy_weights_sum'],
                    'signals': []
                }
                
                # Add signal details
                for signal in asset_signals:
                    strategy_weight = self.strategy_weights.get(signal.strategy_name, 0)
                    conflict_info['signals'].append({
                        'strategy': signal.strategy_name,
                        'signal_type': signal.signal_type.value,
                        'confidence': signal.confidence,
                        'strategy_weight': strategy_weight,
                        'effective_weight': signal.confidence * strategy_weight,
                        'position_size': signal.position_size
                    })
                
                # Resolution recommendation
                recommendation = self._generate_resolution_recommendation(asset, asset_signals, analysis)
                conflict_info['resolution_recommendation'] = recommendation
                
                conflict_report['conflicts'][asset] = conflict_info
                
                if recommendation['action'] != 'no_action':
                    conflict_report['conflict_summary']['resolution_required'] += 1
        
        # Generate overall recommendations
        conflict_report['resolution_recommendations'] = self._generate_overall_recommendations(conflict_report)
        
        return conflict_report
    
    def _generate_resolution_recommendation(self, asset: str, signals: List[TradingSignal], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate resolution recommendation for a specific asset conflict."""
        
        recommendation = {
            'asset': asset,
            'action': 'no_action',
            'reason': '',
            'suggested_method': self.config.get('conflict_resolution', 'weighted_average'),
            'confidence': 0.0
        }
        
        if not analysis['has_conflict']:
            recommendation['action'] = 'no_action'
            recommendation['reason'] = 'No conflict detected'
            return recommendation
        
        # Analyze conflict severity and recommend action
        if analysis['has_opposing']:
            if analysis['dominant_weight'] > 0.7:
                recommendation['action'] = 'resolve_with_dominant'
                recommendation['reason'] = f"Strong dominant signal ({analysis['dominant_weight']:.1%})"
                recommendation['confidence'] = analysis['dominant_weight']
            elif analysis['dominant_weight'] > 0.5:
                recommendation['action'] = 'resolve_with_caution'
                recommendation['reason'] = f"Moderate dominant signal ({analysis['dominant_weight']:.1%})"
                recommendation['confidence'] = analysis['dominant_weight']
                recommendation['suggested_method'] = 'conservative'
            else:
                recommendation['action'] = 'avoid_trade'
                recommendation['reason'] = f"Weak dominant signal ({analysis['dominant_weight']:.1%})"
                recommendation['confidence'] = 0.0
        else:
            # Same direction conflicts (different strengths/sizes)
            recommendation['action'] = 'aggregate'
            recommendation['reason'] = 'Same direction signals - safe to aggregate'
            recommendation['confidence'] = analysis['dominant_weight']
        
        return recommendation
    
    def _generate_overall_recommendations(self, conflict_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate overall system recommendations based on conflict analysis."""
        
        recommendations = []
        
        # High conflict rate warning
        if conflict_report['unique_assets'] > 0:
            conflict_rate = conflict_report['conflict_summary']['assets_with_conflicts'] / conflict_report['unique_assets']
            
            if conflict_rate > 0.5:
                recommendations.append({
                    'type': 'warning',
                    'message': f"High conflict rate ({conflict_rate:.1%}) - consider reviewing strategy weights",
                    'suggested_action': 'Review strategy weights and conflict resolution method'
                })
        
        # Opposing signals warning
        if conflict_report['conflict_summary']['assets_with_opposing_signals'] > 0:
            recommendations.append({
                'type': 'info',
                'message': f"{conflict_report['conflict_summary']['assets_with_opposing_signals']} assets have opposing signals",
                'suggested_action': 'Consider using conservative conflict resolution'
            })
        
        # Resolution method suggestion
        resolution_required = conflict_report['conflict_summary']['resolution_required']
        if resolution_required > 0:
            recommendations.append({
                'type': 'action',
                'message': f"{resolution_required} conflicts require resolution",
                'suggested_action': 'Run resolve_signal_conflicts() to get conflict-free signals'
            })
        
        return recommendations
    
    def _schedule_discord_alerts(self, signals: List[TradingSignal]) -> None:
        """
        Schedule Discord alerts without blocking the main thread.
        
        Args:
            signals: List of aggregated TradingSignal objects
        """
        if not self.discord_manager or not signals:
            return
        
        try:
            # Primary: Use thread pool executor for reliable async execution
            if self._discord_executor:
                future = self._discord_executor.submit(self._send_discord_alerts_sync, signals)
                # Add callback for error handling
                future.add_done_callback(self._handle_discord_task_completion)
                self.logger.debug("Scheduled Discord alerts via thread pool executor")
            else:
                # Fallback to direct async execution
                self._schedule_discord_alerts_fallback(signals)
                
        except Exception as e:
            self.logger.error(f"Failed to schedule Discord alerts: {e}")
    
    def _send_discord_alerts_sync(self, signals: List[TradingSignal]) -> None:
        """
        Send Discord alerts in a synchronous context (runs in thread pool).
        
        Args:
            signals: List of aggregated TradingSignal objects
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._send_discord_alerts(signals))
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Failed to send Discord alerts in thread: {e}")
    
    def _schedule_discord_alerts_fallback(self, signals: List[TradingSignal]) -> None:
        """
        Fallback method for scheduling Discord alerts when thread pool is not available.
        
        Args:
            signals: List of aggregated TradingSignal objects
        """
        try:
            # Try to get running loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._send_discord_alerts(signals))
                self.logger.debug("Scheduled Discord alerts in async context")
            except RuntimeError:
                # No running loop, create new one in thread
                import threading
                def run_in_thread():
                    try:
                        asyncio.run(self._send_discord_alerts(signals))
                    except Exception as e:
                        self.logger.error(f"Failed to send Discord alerts in fallback thread: {e}")
                
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
                self.logger.debug("Scheduled Discord alerts in new thread")
                
        except Exception as e:
            self.logger.error(f"Failed to schedule Discord alerts (fallback): {e}")
    
    async def _send_discord_alerts(self, signals: List[TradingSignal]) -> None:
        """
        Send Discord alerts for aggregated signals.
        
        Args:
            signals: List of aggregated TradingSignal objects
        """
        if not self.discord_manager:
            return
        
        try:
            results = await self.discord_manager.process_signals(signals)
            self.logger.info(f"Discord alerts sent: {results['sent']}/{results['total']} successful")
        except Exception as e:
            self.logger.error(f"Failed to send Discord alerts: {e}")
    
    def _handle_discord_task_completion(self, future):
        """
        Handle completion of Discord alert task.
        
        Args:
            future: Future object from thread pool executor
        """
        try:
            future.result()  # This will raise exception if task failed
            self.logger.debug("Discord alert task completed successfully")
        except Exception as e:
            self.logger.error(f"Discord alert task failed: {e}")
    
    async def send_test_discord_alert(self) -> bool:
        """
        Send a test Discord alert to verify configuration.
        
        Returns:
            bool: True if successful
        """
        if not self.discord_manager:
            self.logger.warning("Discord manager not configured")
            return False
        
        try:
            return await self.discord_manager.send_test_alert()
        except Exception as e:
            self.logger.error(f"Failed to send test Discord alert: {e}")
            return False
    
    def cleanup(self):
        """
        Clean up resources, especially the thread pool executor.
        Call this when shutting down the aggregator.
        """
        if hasattr(self, '_discord_executor') and self._discord_executor:
            try:
                self._discord_executor.shutdown(wait=True)
                self.logger.info("Discord alert thread pool executor shut down")
            except Exception as e:
                self.logger.error(f"Error shutting down Discord executor: {e}")
    
    def __del__(self):
        """
        Destructor to ensure thread pool is cleaned up.
        """
        self.cleanup() 
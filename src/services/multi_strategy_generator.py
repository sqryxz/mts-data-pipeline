"""
Multi-Strategy Signal Generator - Task 9
Orchestrates multiple strategies and aggregates results into final trading signals.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from src.signals.strategies.strategy_registry import StrategyRegistry
from src.signals.signal_aggregator import SignalAggregator
from src.data.signal_models import TradingSignal
from src.data.sqlite_helper import CryptoDatabase
from src.utils.exceptions import ConfigurationError, DataProcessingError
from src.utils.multi_webhook_discord_manager import MultiWebhookDiscordManager


class MultiStrategyGenerator:
    """
    Task 9: Multi-Strategy Signal Generator
    
    Orchestrates multiple signal strategies and aggregates their outputs into
    final trading signals. Handles strategy loading, data management, and
    signal aggregation with conflict resolution.
    """
    
    def __init__(self, strategy_configs: Dict[str, Dict[str, Any]], aggregator_config: Dict[str, Any]):
        """
        Initialize the multi-strategy generator.
        
        Args:
            strategy_configs: Dictionary mapping strategy names to their config parameters
                             Format: {"strategy_name": {"config_path": "path/to/config.json", ...}}
            aggregator_config: Configuration for signal aggregation including strategy weights
                              Format: {"strategy_weights": {"strategy_name": weight, ...}, ...}
        """
        self.logger = logging.getLogger(__name__)
        
        # Validate inputs
        if not strategy_configs:
            raise ConfigurationError("Strategy configurations cannot be empty")
        
        if not aggregator_config or 'strategy_weights' not in aggregator_config:
            raise ConfigurationError("Aggregator config must include 'strategy_weights'")
        
        # Initialize components
        self.strategy_configs = strategy_configs
        self.aggregator_config = aggregator_config
        
        # Initialize strategy registry
        self.registry = StrategyRegistry()
        self.registry.load_strategies_from_directory("src/signals/strategies")
        
        # Initialize signal aggregator
        strategy_weights = aggregator_config['strategy_weights']
        aggregation_config = aggregator_config.get('aggregation_config', {})
        self.aggregator = SignalAggregator(strategy_weights, aggregation_config)
        
        # Initialize database connection
        self.db = CryptoDatabase()
        
        # Load and validate strategies
        self.strategies = self._load_strategies()
        
        # Initialize multi-webhook Discord manager if configured (after strategies are loaded)
        self.multi_webhook_manager = self._initialize_multi_webhook_manager()
        
        self.logger.info(f"MultiStrategyGenerator initialized with {len(self.strategies)} strategies")
    
    def _load_strategies(self) -> Dict[str, Any]:
        """Load all configured strategies from the registry."""
        strategies = {}
        
        for strategy_name, config in self.strategy_configs.items():
            try:
                config_path = config.get('config_path')
                if not config_path:
                    raise ConfigurationError(f"No config_path specified for strategy: {strategy_name}")
                
                # Load strategy from registry
                strategy_instance = self.registry.get_strategy(strategy_name, config_path)
                strategies[strategy_name] = strategy_instance
                
                self.logger.info(f"Successfully loaded strategy: {strategy_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load strategy {strategy_name}: {e}")
                raise ConfigurationError(f"Failed to load strategy {strategy_name}: {e}")
        
        return strategies
    
    def generate_aggregated_signals(self, days: int = 30) -> List[TradingSignal]:
        """
        Generate aggregated trading signals from all configured strategies.
        
        Args:
            days: Number of days of historical data to use for analysis
            
        Returns:
            List of aggregated TradingSignal objects
        """
        self.logger.info(f"Generating aggregated signals using {days} days of data")
        
        try:
            # Get all unique assets from all strategies
            all_assets = self._get_all_assets()
            
            # Fetch market data for all assets
            market_data = self._get_market_data(all_assets, days)
            
            # Generate signals from all strategies
            strategy_signals = self._generate_individual_signals(market_data)
            
            # Aggregate signals using the signal aggregator
            aggregated_signals = self.aggregator.aggregate_signals(strategy_signals)
            
            self.logger.info(f"Generated {len(aggregated_signals)} aggregated signals from "
                           f"{sum(len(signals) for signals in strategy_signals.values())} individual signals")
            
            return aggregated_signals
            
        except Exception as e:
            self.logger.error(f"Failed to generate aggregated signals: {e}")
            raise DataProcessingError(f"Signal generation failed: {e}")
    
    def _get_all_assets(self) -> List[str]:
        """Get all unique assets from all strategy configurations."""
        all_assets = set()
        
        for strategy_name, strategy in self.strategies.items():
            try:
                params = strategy.get_parameters()
                assets = params.get('assets', [])
                all_assets.update(assets)
            except Exception as e:
                self.logger.warning(f"Could not get assets from strategy {strategy_name}: {e}")
        
        return list(all_assets)
    
    def _get_market_data(self, assets: List[str], days: int) -> Dict[str, Any]:
        """
        Get comprehensive market data for all assets.
        
        Args:
            assets: List of asset names
            days: Number of days of historical data
            
        Returns:
            Dictionary containing market data for all assets
        """
        try:
            # Use the enhanced market data provider from Task 6
            market_data = self.db.get_strategy_market_data(assets, days)
            
            self.logger.debug(f"Retrieved market data for {len(assets)} assets over {days} days")
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve market data: {e}")
            raise DataProcessingError(f"Market data retrieval failed: {e}")
    
    def _generate_individual_signals(self, market_data: Dict[str, Any]) -> Dict[str, List[TradingSignal]]:
        """
        Generate signals from each individual strategy.
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            Dictionary mapping strategy names to their generated signals
        """
        strategy_signals = {}
        
        for strategy_name, strategy in self.strategies.items():
            try:
                # Run strategy analysis
                analysis_results = strategy.analyze(market_data)
                
                # Generate signals from analysis
                signals = strategy.generate_signals(analysis_results)
                
                strategy_signals[strategy_name] = signals
                
                self.logger.info(f"Strategy {strategy_name} generated {len(signals)} signals")
                
            except Exception as e:
                self.logger.error(f"Strategy {strategy_name} failed to generate signals: {e}")
                # Continue with other strategies instead of failing completely
                strategy_signals[strategy_name] = []
        
        return strategy_signals
    
    def _initialize_multi_webhook_manager(self) -> Optional[MultiWebhookDiscordManager]:
        """Initialize multi-webhook Discord manager from configuration."""
        try:
            config_path = "config/strategy_discord_webhooks.json"
            if not Path(config_path).exists():
                self.logger.info("No strategy Discord webhook configuration found")
                return None
            
            with open(config_path, 'r') as f:
                webhook_config = json.load(f)
            
            strategy_webhooks = webhook_config.get('strategy_webhooks', {})
            if not strategy_webhooks:
                self.logger.info("No strategy webhooks configured")
                return None
            
            # Filter to only include strategies we actually have
            filtered_webhooks = {}
            for strategy_name, config in strategy_webhooks.items():
                if strategy_name in self.strategies:
                    filtered_webhooks[strategy_name] = config
                    self.logger.info(f"Configured Discord webhook for strategy: {strategy_name}")
            
            if filtered_webhooks:
                return MultiWebhookDiscordManager(filtered_webhooks)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to initialize multi-webhook Discord manager: {e}")
            return None
    
    def generate_signals_with_discord_routing(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate signals and send individual strategy signals to their specific Discord webhooks.
        
        Args:
            days: Number of days of historical data to use for analysis
            
        Returns:
            Dict with aggregated signals and Discord sending results
        """
        self.logger.info(f"Generating signals with Discord routing using {days} days of data")
        
        try:
            # Get all unique assets from all strategies
            all_assets = self._get_all_assets()
            
            # Fetch market data for all assets
            market_data = self._get_market_data(all_assets, days)
            
            # Generate signals from all strategies
            strategy_signals = self._generate_individual_signals(market_data)
            
            # Send individual strategy signals to their Discord webhooks
            discord_results = {}
            if self.multi_webhook_manager:
                discord_results = self.multi_webhook_manager.send_strategy_signals_sync(strategy_signals)
                
                total_sent = sum(result.get('sent', 0) for result in discord_results.values())
                self.logger.info(f"Sent {total_sent} individual strategy signals to Discord")
            else:
                self.logger.info("Multi-webhook Discord manager not configured")
            
            # Also generate aggregated signals
            aggregated_signals = self.aggregator.aggregate_signals(strategy_signals)
            
            results = {
                'individual_signals': strategy_signals,
                'aggregated_signals': aggregated_signals,
                'discord_results': discord_results,
                'total_individual_signals': sum(len(signals) for signals in strategy_signals.values()),
                'total_aggregated_signals': len(aggregated_signals)
            }
            
            self.logger.info(f"Generated {results['total_aggregated_signals']} aggregated signals from "
                           f"{results['total_individual_signals']} individual signals")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to generate signals with Discord routing: {e}")
            raise DataProcessingError(f"Signal generation with Discord routing failed: {e}")
    
    def get_strategy_performance_summary(self, signals: List[TradingSignal]) -> Dict[str, Any]:
        """
        Get performance summary of generated signals.
        
        Args:
            signals: List of generated TradingSignal objects
            
        Returns:
            Dictionary containing performance metrics
        """
        if not signals:
            return {
                'total_signals': 0,
                'signal_types': {},
                'assets': {},
                'confidence_stats': {},
                'strategy_distribution': {}
            }
        
        # Basic statistics
        total_signals = len(signals)
        signal_types = {}
        assets = {}
        confidences = []
        strategy_distribution = {}
        
        for signal in signals:
            # Signal type distribution
            signal_type = signal.signal_type.value
            signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            
            # Asset distribution
            assets[signal.asset] = assets.get(signal.asset, 0) + 1
            
            # Confidence tracking
            confidences.append(signal.confidence)
            
            # Strategy distribution (from analysis_data)
            if signal.analysis_data and 'strategies_combined' in signal.analysis_data:
                strategies = signal.analysis_data['strategies_combined']
                for strategy in strategies:
                    strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
            else:
                # Single strategy signal
                strategy_name = signal.strategy_name
                strategy_distribution[strategy_name] = strategy_distribution.get(strategy_name, 0) + 1
        
        # Calculate confidence statistics
        confidence_stats = {
            'mean': sum(confidences) / len(confidences) if confidences else 0,
            'min': min(confidences) if confidences else 0,
            'max': max(confidences) if confidences else 0,
            'high_confidence_count': sum(1 for c in confidences if c > 0.7)
        }
        
        return {
            'total_signals': total_signals,
            'signal_types': signal_types,
            'assets': assets,
            'confidence_stats': confidence_stats,
            'strategy_distribution': strategy_distribution,
            'generation_timestamp': datetime.now().isoformat()
        }
    
    def export_signals_to_json(self, signals: List[TradingSignal], filepath: str) -> None:
        """
        Export generated signals to JSON file.
        
        Args:
            signals: List of TradingSignal objects
            filepath: Path to output JSON file
        """
        try:
            # Convert signals to serializable format
            signals_data = []
            for signal in signals:
                signal_dict = {
                    'asset': signal.asset,
                    'signal_type': signal.signal_type.value,
                    'timestamp': signal.timestamp,
                    'price': signal.price,
                    'strategy_name': signal.strategy_name,
                    'signal_strength': signal.signal_strength.value,
                    'confidence': signal.confidence,
                    'position_size': signal.position_size,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'max_risk': signal.max_risk,
                    'analysis_data': signal.analysis_data
                }
                signals_data.append(signal_dict)
            
            # Create export data with metadata
            export_data = {
                'signals': signals_data,
                'metadata': {
                    'generation_timestamp': datetime.now().isoformat(),
                    'total_signals': len(signals),
                    'strategy_configs': self.strategy_configs,
                    'aggregator_config': self.aggregator_config
                },
                'performance_summary': self.get_strategy_performance_summary(signals)
            }
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(signals)} signals to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export signals to JSON: {e}")
            raise DataProcessingError(f"JSON export failed: {e}")
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """
        Get current status of all loaded strategies.
        
        Returns:
            Dictionary containing strategy status information
        """
        status = {
            'total_strategies': len(self.strategies),
            'loaded_strategies': list(self.strategies.keys()),
            'registry_strategies': self.registry.list_strategies(),
            'aggregator_weights': self.aggregator.strategy_weights,
            'aggregator_config': self.aggregator.config
        }
        
        # Get parameters from each strategy
        strategy_params = {}
        for name, strategy in self.strategies.items():
            try:
                params = strategy.get_parameters()
                strategy_params[name] = params
            except Exception as e:
                strategy_params[name] = {'error': str(e)}
        
        status['strategy_parameters'] = strategy_params
        
        return status
    
    def run_conflict_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Run conflict analysis on signals without aggregation.
        
        Args:
            days: Number of days of historical data to use
            
        Returns:
            Dictionary containing conflict analysis results
        """
        try:
            # Get market data
            all_assets = self._get_all_assets()
            market_data = self._get_market_data(all_assets, days)
            
            # Generate individual signals
            strategy_signals = self._generate_individual_signals(market_data)
            
            # Flatten signals for conflict analysis
            all_signals = []
            for signals in strategy_signals.values():
                all_signals.extend(signals)
            
            # Run conflict analysis
            conflict_report = self.aggregator.get_conflict_report(all_signals)
            
            return conflict_report
            
        except Exception as e:
            self.logger.error(f"Conflict analysis failed: {e}")
            raise DataProcessingError(f"Conflict analysis failed: {e}")


def create_default_multi_strategy_generator() -> MultiStrategyGenerator:
    """
    Create a MultiStrategyGenerator with default configuration.
    
    Returns:
        Configured MultiStrategyGenerator instance
    """
    # Default strategy configurations
    strategy_configs = {
        "vixcorrelation": {
            "config_path": "config/strategies/vix_correlation.json"
        },
        "meanreversion": {
            "config_path": "config/strategies/mean_reversion.json"
        },
        "volatility": {
            "config_path": "config/strategies/volatility_strategy.json"
        },
        "ripple": {
            "config_path": "config/strategies/ripple_signals.json"
        }
    }
    
    # Default aggregator configuration
    aggregator_config = {
        "strategy_weights": {
            "vixcorrelation": 0.30,
            "meanreversion": 0.25,
            "volatility": 0.25,
            "ripple": 0.20
        },
        "aggregation_config": {
            "conflict_resolution": "weighted_average",
            "min_confidence_threshold": 0.1,
            "max_position_size": 0.05
        }
    }
    
    return MultiStrategyGenerator(strategy_configs, aggregator_config) 
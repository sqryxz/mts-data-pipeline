#!/usr/bin/env python3
"""
Generate Last 24 Hours of Alerts and Backtest Analysis
This script generates trading alerts for the last 24 hours and runs them through
the backtest engine to analyze ROI and Sharpe ratio performance.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.signals.backtest_interface import BacktestInterface, BacktestResult
from src.data.sqlite_helper import CryptoDatabase
from src.signals.strategies.vix_correlation_strategy import VIXCorrelationStrategy
from src.signals.strategies.momentum_strategy import MomentumStrategy
from src.signals.strategies.volatility_strategy import VolatilityStrategy
from src.utils.exceptions import DataProcessingError, ConfigurationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/24h_alerts_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AlertGenerator:
    """Generate trading alerts for the last 24 hours."""
    
    def __init__(self, db_path: str = "data/crypto_data.db"):
        self.db = CryptoDatabase(db_path)
        
        # Initialize strategies with default configs if config files don't exist
        try:
            self.strategies = {
                'vix_correlation': VIXCorrelationStrategy("config/strategies/vix_correlation_strategy.json"),
                'momentum': MomentumStrategy("config/strategies/momentum_strategy.json"),
                'volatility': VolatilityStrategy("config/strategies/volatility_strategy.json")
            }
        except FileNotFoundError:
            # Create default configs and initialize strategies
            self._create_default_configs()
            self.strategies = {
                'vix_correlation': VIXCorrelationStrategy("config/strategies/vix_correlation_strategy.json"),
                'momentum': MomentumStrategy("config/strategies/momentum_strategy.json"),
                'volatility': VolatilityStrategy("config/strategies/volatility_strategy.json")
            }
    
    def _create_default_configs(self):
        """Create default configuration files for strategies."""
        os.makedirs("config/strategies", exist_ok=True)
        
        # VIX Correlation Strategy config
        vix_config = {
            "assets": ["bitcoin", "ethereum"],
            "correlation_threshold": 0.7,
            "vix_threshold": 25.0,
            "base_position_size": 0.02,
            "max_position_size": 0.05,
            "min_confidence": 0.6
        }
        
        with open("config/strategies/vix_correlation_strategy.json", "w") as f:
            json.dump(vix_config, f, indent=2)
        
        # Volatility Strategy config
        volatility_config = {
            "assets": ["bitcoin", "ethereum"],
            "volatility_window": 15,
            "historical_hours": 24,
            "volatility_threshold_percentile": 90,
            "extreme_volatility_percentile": 95,
            "base_position_size": 0.02,
            "max_position_size": 0.05,
            "min_confidence": 0.6
        }
        
        with open("config/strategies/volatility_strategy.json", "w") as f:
            json.dump(volatility_config, f, indent=2)
    
    def get_last_24h_data(self) -> Dict[str, pd.DataFrame]:
        """Get market data for the last 24 hours for all monitored assets."""
        # Get monitored assets from config
        monitored_assets = ['bitcoin', 'ethereum']  # Default assets
        
        data = {}
        for asset in monitored_assets:
            try:
                # Get data for the last 1 day (24 hours)
                df = self.db.get_crypto_data(cryptocurrency=asset, days=1)
                if not df.empty:
                    data[asset] = df
                    logger.info(f"Loaded {len(df)} records for {asset}")
                else:
                    logger.warning(f"No data found for {asset}")
            except Exception as e:
                logger.error(f"Error loading data for {asset}: {e}")
        
        return data
    
    def generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate trading alerts for the last 24 hours."""
        alerts = []
        market_data = self.get_last_24h_data()
        
        for asset, df in market_data.items():
            logger.info(f"Generating alerts for {asset}")
            
            # Generate alerts for each strategy
            for strategy_name, strategy in self.strategies.items():
                try:
                    signals = []
                    
                    # Handle different strategy interfaces
                    if strategy_name == 'momentum':
                        # Momentum strategy uses different interface
                        signals = strategy.generate_signals(df, asset)
                    else:
                        # Other strategies use analyze -> generate_signals pattern
                        market_data = {asset: df}
                        analysis_results = strategy.analyze(market_data)
                        signals = strategy.generate_signals(analysis_results)
                    
                    for signal in signals:
                        alert = {
                            "timestamp": int(datetime.now().timestamp() * 1000),
                            "asset": signal.symbol if hasattr(signal, 'symbol') else signal.asset if hasattr(signal, 'asset') else asset,
                            "signal_type": signal.signal_type.value,
                            "direction": signal.direction.value,
                            "price": signal.price,
                            "confidence": signal.confidence,
                            "strategy_name": strategy_name,
                            "position_size": signal.position_size,
                            "stop_loss": signal.stop_loss,
                            "take_profit": signal.take_profit,
                            "alert_type": "trading_signal",
                            "analysis_data": {
                                "strategy": strategy_name,
                                "signal_strength": signal.confidence,
                                "market_conditions": self._analyze_market_conditions(df)
                            }
                        }
                        alerts.append(alert)
                        
                except Exception as e:
                    logger.error(f"Error generating signals for {asset} with {strategy_name}: {e}")
        
        logger.info(f"Generated {len(alerts)} alerts")
        return alerts
    
    def _analyze_market_conditions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze current market conditions."""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        # Calculate basic indicators
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(24)  # Annualized
        
        return {
            "current_price": latest['close'],
            "volume": latest['volume'],
            "volatility": volatility,
            "trend": "bullish" if latest['close'] > df['close'].iloc[-2] else "bearish",
            "price_change_24h": ((latest['close'] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
        }
    
    def save_alerts(self, alerts: List[Dict[str, Any]], output_dir: str = "data/alerts"):
        """Save generated alerts to JSON files."""
        os.makedirs(output_dir, exist_ok=True)
        
        for i, alert in enumerate(alerts):
            timestamp = datetime.fromtimestamp(alert['timestamp'] / 1000)
            filename = f"generated_alert_{alert['asset']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(alert, f, indent=2)
            
            logger.info(f"Saved alert: {filename}")
        
        # Save summary
        summary = {
            "generation_timestamp": datetime.now().isoformat(),
            "total_alerts": len(alerts),
            "assets": list(set(alert['asset'] for alert in alerts)),
            "strategies": list(set(alert['strategy_name'] for alert in alerts)),
            "signal_types": list(set(alert['signal_type'] for alert in alerts))
        }
        
        summary_file = os.path.join(output_dir, "24h_alerts_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved summary: {summary_file}")


class AlertBacktester:
    """Backtest the generated alerts to analyze performance."""
    
    def __init__(self, db_path: str = "data/crypto_data.db"):
        self.db = CryptoDatabase(db_path)
        self.backtest_interface = BacktestInterface()
    
    def load_alerts(self, alerts_dir: str = "data/alerts") -> List[Dict[str, Any]]:
        """Load generated alerts from the alerts directory."""
        alerts = []
        
        for filename in os.listdir(alerts_dir):
            if filename.startswith("generated_alert_") and filename.endswith(".json"):
                filepath = os.path.join(alerts_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        alert = json.load(f)
                        alerts.append(alert)
                except Exception as e:
                    logger.error(f"Error loading alert {filename}: {e}")
        
        # Sort by timestamp
        alerts.sort(key=lambda x: x['timestamp'])
        logger.info(f"Loaded {len(alerts)} alerts for backtesting")
        return alerts
    
    def convert_alerts_to_signals(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert alerts to trading signals for backtesting."""
        signals = []
        
        for alert in alerts:
            signal = {
                "timestamp": alert['timestamp'],
                "asset": alert['asset'],
                "signal_type": alert['signal_type'],
                "direction": alert['direction'],
                "price": alert['price'],
                "confidence": alert['confidence'],
                "strategy": alert['strategy_name'],
                "position_size": alert['position_size'],
                "stop_loss": alert['stop_loss'],
                "take_profit": alert['take_profit']
            }
            signals.append(signal)
        
        return signals
    
    def run_backtest(self, alerts: List[Dict[str, Any]]) -> BacktestResult:
        """Run backtest on the generated alerts."""
        if not alerts:
            raise ValueError("No alerts provided for backtesting")
        
        # Get time range from alerts
        timestamps = [alert['timestamp'] for alert in alerts]
        start_time = datetime.fromtimestamp(min(timestamps) / 1000)
        end_time = datetime.fromtimestamp(max(timestamps) / 1000)
        
        # Add some buffer time for price movement
        end_time += timedelta(hours=6)
        
        logger.info(f"Running backtest from {start_time} to {end_time}")
        
        # Convert alerts to signals
        signals = self.convert_alerts_to_signals(alerts)
        
        # Run backtest using the interface
        result = self.backtest_interface.backtest_signals(
            signals=signals,
            start_date=start_time,
            end_date=end_time,
            initial_capital=10000,  # $10,000 starting capital
            commission=0.001  # 0.1% commission
        )
        
        return result
    
    def generate_report(self, result: BacktestResult, output_dir: str = "backtest_results") -> str:
        """Generate a comprehensive backtest report."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create detailed report
        report_content = f"""
# 24-Hour Alerts Backtest Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Strategy**: {result.strategy_name}
- **Period**: {result.start_date} to {result.end_date}
- **Status**: {result.status.value}
- **Execution Time**: {result.execution_time:.2f} seconds

## Performance Metrics
- **Total Return**: {result.total_return:.2%}
- **Annualized Return**: {result.annualized_return:.2%}
- **Sharpe Ratio**: {result.sharpe_ratio:.3f}
- **Maximum Drawdown**: {result.max_drawdown:.2%}
- **Win Rate**: {result.win_rate:.2%}
- **Volatility**: {result.volatility:.2%}
- **VaR (95%)**: {result.var_95:.2%}
- **Calmar Ratio**: {result.calmar_ratio:.3f}

## Trading Statistics
- **Total Trades**: {result.total_trades}
- **Profitable Trades**: {result.profitable_trades}
- **Losing Trades**: {result.losing_trades}
- **Average Trade Return**: {result.average_trade_return:.2%}
- **Average Winning Trade**: {result.average_winning_trade:.2%}
- **Average Losing Trade**: {result.average_losing_trade:.2%}

## Signal Analysis
- **Total Signals**: {result.total_signals}
- **Long Signals**: {result.long_signals}
- **Short Signals**: {result.short_signals}
- **Hold Signals**: {result.hold_signals}

## Risk Analysis
- **Sharpe Ratio**: {result.sharpe_ratio:.3f} 
  - Excellent: > 1.5
  - Good: 1.0 - 1.5
  - Acceptable: 0.5 - 1.0
  - Poor: < 0.5

- **Maximum Drawdown**: {result.max_drawdown:.2%}
  - Low Risk: < 10%
  - Moderate Risk: 10% - 20%
  - High Risk: > 20%

## Recommendations
"""
        
        # Add recommendations based on performance
        if result.sharpe_ratio > 1.5:
            report_content += "- **Excellent Sharpe Ratio**: Strategy shows strong risk-adjusted returns\n"
        elif result.sharpe_ratio > 1.0:
            report_content += "- **Good Sharpe Ratio**: Strategy performs well relative to risk\n"
        elif result.sharpe_ratio > 0.5:
            report_content += "- **Acceptable Sharpe Ratio**: Consider optimization for better risk-adjusted returns\n"
        else:
            report_content += "- **Poor Sharpe Ratio**: Strategy needs significant improvement\n"
        
        if result.max_drawdown < 0.10:
            report_content += "- **Low Risk Profile**: Acceptable drawdown levels\n"
        elif result.max_drawdown < 0.20:
            report_content += "- **Moderate Risk**: Consider risk management improvements\n"
        else:
            report_content += "- **High Risk**: Implement stricter risk controls\n"
        
        if result.win_rate > 0.6:
            report_content += "- **High Win Rate**: Strategy shows good directional accuracy\n"
        elif result.win_rate > 0.5:
            report_content += "- **Moderate Win Rate**: Consider signal filtering improvements\n"
        else:
            report_content += "- **Low Win Rate**: Strategy needs signal quality improvements\n"
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(output_dir, f"24h_alerts_backtest_report_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        # Save detailed results as JSON
        results_file = os.path.join(output_dir, f"24h_alerts_backtest_results_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        logger.info(f"Report saved: {report_file}")
        logger.info(f"Results saved: {results_file}")
        
        return report_file


def main():
    """Main execution function."""
    logger.info("Starting 24-hour alerts generation and backtesting")
    
    try:
        # Step 1: Generate alerts
        logger.info("Step 1: Generating alerts for the last 24 hours")
        alert_generator = AlertGenerator()
        alerts = alert_generator.generate_alerts()
        
        if not alerts:
            logger.warning("No alerts generated. Exiting.")
            return
        
        # Save generated alerts
        alert_generator.save_alerts(alerts)
        
        # Step 2: Run backtest
        logger.info("Step 2: Running backtest on generated alerts")
        backtester = AlertBacktester()
        result = backtester.run_backtest(alerts)
        
        # Step 3: Generate report
        logger.info("Step 3: Generating backtest report")
        report_file = backtester.generate_report(result)
        
        logger.info("=== BACKTEST COMPLETE ===")
        logger.info(f"Total Return: {result.total_return:.2%}")
        logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
        logger.info(f"Max Drawdown: {result.max_drawdown:.2%}")
        logger.info(f"Win Rate: {result.win_rate:.2%}")
        logger.info(f"Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()

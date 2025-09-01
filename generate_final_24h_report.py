#!/usr/bin/env python3
"""
Final 24-Hour Alerts Analysis Report
This script analyzes the generated alerts and provides comprehensive ROI and Sharpe ratio analysis.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertAnalyzer:
    """Analyze generated alerts and calculate performance metrics."""
    
    def __init__(self):
        self.alerts = []
        self.analysis_results = {}
    
    def load_alerts(self, alerts_dir: str = "data/alerts"):
        """Load all generated alerts from the alerts directory."""
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
        self.alerts = alerts
        
        logger.info(f"Loaded {len(alerts)} alerts for analysis")
        return alerts
    
    def analyze_alerts(self) -> Dict[str, Any]:
        """Analyze the loaded alerts and calculate performance metrics."""
        if not self.alerts:
            return {}
        
        # Basic statistics
        total_alerts = len(self.alerts)
        assets = list(set(alert['asset'] for alert in self.alerts))
        strategies = list(set(alert['strategy_name'] for alert in self.alerts))
        signal_types = list(set(alert['signal_type'] for alert in self.alerts))
        
        # Calculate average metrics
        avg_confidence = np.mean([alert['confidence'] for alert in self.alerts])
        avg_position_size = np.mean([alert['position_size'] for alert in self.alerts])
        
        # Signal distribution
        signal_distribution = {}
        for signal_type in signal_types:
            signal_distribution[signal_type] = len([a for a in self.alerts if a['signal_type'] == signal_type])
        
        # Strategy distribution
        strategy_distribution = {}
        for strategy in strategies:
            strategy_distribution[strategy] = len([a for a in self.alerts if a['strategy_name'] == strategy])
        
        # Asset distribution
        asset_distribution = {}
        for asset in assets:
            asset_distribution[asset] = len([a for a in self.alerts if a['asset'] == asset])
        
        # Calculate potential ROI based on signal characteristics
        potential_roi_analysis = self._calculate_potential_roi()
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics()
        
        # Calculate Sharpe ratio estimate
        sharpe_analysis = self._calculate_sharpe_estimate()
        
        self.analysis_results = {
            'summary': {
                'total_alerts': total_alerts,
                'assets': assets,
                'strategies': strategies,
                'signal_types': signal_types,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'metrics': {
                'average_confidence': avg_confidence,
                'average_position_size': avg_position_size,
                'signal_distribution': signal_distribution,
                'strategy_distribution': strategy_distribution,
                'asset_distribution': asset_distribution
            },
            'performance': {
                'potential_roi': potential_roi_analysis,
                'risk_metrics': risk_metrics,
                'sharpe_analysis': sharpe_analysis
            },
            'detailed_alerts': self.alerts
        }
        
        return self.analysis_results
    
    def _calculate_potential_roi(self) -> Dict[str, Any]:
        """Calculate potential ROI based on signal characteristics."""
        if not self.alerts:
            return {}
        
        total_potential_return = 0
        total_risk = 0
        signal_returns = []
        
        for alert in self.alerts:
            # Calculate potential return based on signal type and confidence
            if alert['signal_type'] == 'LONG':
                # Assume 5% average gain for long signals
                potential_return = 0.05 * alert['confidence']
                risk = 0.03 * alert['confidence']  # 3% average risk
            elif alert['signal_type'] == 'SHORT':
                # Assume 3% average gain for short signals (more conservative)
                potential_return = 0.03 * alert['confidence']
                risk = 0.04 * alert['confidence']  # 4% average risk for shorts
            else:
                potential_return = 0
                risk = 0
            
            # Weight by position size
            weighted_return = potential_return * alert['position_size']
            weighted_risk = risk * alert['position_size']
            
            total_potential_return += weighted_return
            total_risk += weighted_risk
            signal_returns.append(weighted_return)
        
        # Calculate metrics
        avg_return = np.mean(signal_returns) if signal_returns else 0
        return_volatility = np.std(signal_returns) if len(signal_returns) > 1 else 0
        
        return {
            'total_potential_return': total_potential_return,
            'total_risk': total_risk,
            'average_return_per_signal': avg_return,
            'return_volatility': return_volatility,
            'risk_return_ratio': total_potential_return / total_risk if total_risk > 0 else 0,
            'signal_returns': signal_returns
        }
    
    def _calculate_risk_metrics(self) -> Dict[str, Any]:
        """Calculate risk metrics for the alerts."""
        if not self.alerts:
            return {}
        
        # Calculate position concentration risk
        position_sizes = [alert['position_size'] for alert in self.alerts]
        max_position_size = max(position_sizes) if position_sizes else 0
        avg_position_size = np.mean(position_sizes) if position_sizes else 0
        
        # Calculate confidence distribution
        confidences = [alert['confidence'] for alert in self.alerts]
        avg_confidence = np.mean(confidences) if confidences else 0
        min_confidence = min(confidences) if confidences else 0
        max_confidence = max(confidences) if confidences else 0
        
        # Calculate diversification metrics
        assets = list(set(alert['asset'] for alert in self.alerts))
        strategies = list(set(alert['strategy_name'] for alert in self.alerts))
        
        return {
            'position_concentration': {
                'max_position_size': max_position_size,
                'average_position_size': avg_position_size,
                'total_exposure': sum(position_sizes)
            },
            'confidence_metrics': {
                'average_confidence': avg_confidence,
                'min_confidence': min_confidence,
                'max_confidence': max_confidence,
                'confidence_std': np.std(confidences) if len(confidences) > 1 else 0
            },
            'diversification': {
                'asset_count': len(assets),
                'strategy_count': len(strategies),
                'signals_per_asset': len(self.alerts) / len(assets) if assets else 0,
                'signals_per_strategy': len(self.alerts) / len(strategies) if strategies else 0
            }
        }
    
    def _calculate_sharpe_estimate(self) -> Dict[str, Any]:
        """Calculate estimated Sharpe ratio based on signal characteristics."""
        if not self.alerts:
            return {}
        
        # Get potential returns from ROI analysis
        roi_analysis = self._calculate_potential_roi()
        signal_returns = roi_analysis.get('signal_returns', [])
        
        if not signal_returns:
            return {'estimated_sharpe': 0, 'risk_free_rate': 0.02}
        
        # Calculate metrics
        avg_return = np.mean(signal_returns)
        return_std = np.std(signal_returns) if len(signal_returns) > 1 else 0.01
        
        # Assume 2% risk-free rate
        risk_free_rate = 0.02
        
        # Calculate Sharpe ratio
        if return_std > 0:
            sharpe_ratio = (avg_return - risk_free_rate) / return_std
        else:
            sharpe_ratio = 0
        
        # Classify Sharpe ratio
        if sharpe_ratio > 1.5:
            sharpe_classification = "Excellent"
        elif sharpe_ratio > 1.0:
            sharpe_classification = "Good"
        elif sharpe_ratio > 0.5:
            sharpe_classification = "Acceptable"
        else:
            sharpe_classification = "Poor"
        
        return {
            'estimated_sharpe': sharpe_ratio,
            'risk_free_rate': risk_free_rate,
            'average_return': avg_return,
            'return_volatility': return_std,
            'classification': sharpe_classification,
            'interpretation': self._interpret_sharpe_ratio(sharpe_ratio)
        }
    
    def _interpret_sharpe_ratio(self, sharpe_ratio: float) -> str:
        """Provide interpretation of the Sharpe ratio."""
        if sharpe_ratio > 2.0:
            return "Exceptional risk-adjusted returns. Strategy shows excellent performance relative to risk."
        elif sharpe_ratio > 1.5:
            return "Very good risk-adjusted returns. Strategy performs well above market average."
        elif sharpe_ratio > 1.0:
            return "Good risk-adjusted returns. Strategy provides solid performance relative to risk."
        elif sharpe_ratio > 0.5:
            return "Acceptable risk-adjusted returns. Strategy shows moderate performance relative to risk."
        elif sharpe_ratio > 0:
            return "Below average risk-adjusted returns. Strategy needs improvement."
        else:
            return "Poor risk-adjusted returns. Strategy underperforms relative to risk."
    
    def generate_report(self, output_dir: str = "backtest_results") -> str:
        """Generate a comprehensive analysis report."""
        os.makedirs(output_dir, exist_ok=True)
        
        if not self.analysis_results:
            self.analyze_alerts()
        
        # Create detailed report
        report_content = f"""
# 24-Hour Alerts Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Alerts Generated**: {self.analysis_results['summary']['total_alerts']}
- **Assets Covered**: {', '.join(self.analysis_results['summary']['assets'])}
- **Strategies Used**: {', '.join(self.analysis_results['summary']['strategies'])}
- **Signal Types**: {', '.join(self.analysis_results['summary']['signal_types'])}

## Performance Metrics

### Potential ROI Analysis
- **Total Potential Return**: {self.analysis_results['performance']['potential_roi']['total_potential_return']:.2%}
- **Total Risk**: {self.analysis_results['performance']['potential_roi']['total_risk']:.2%}
- **Risk-Return Ratio**: {self.analysis_results['performance']['potential_roi']['risk_return_ratio']:.3f}
- **Average Return per Signal**: {self.analysis_results['performance']['potential_roi']['average_return_per_signal']:.2%}
- **Return Volatility**: {self.analysis_results['performance']['potential_roi']['return_volatility']:.2%}

### Sharpe Ratio Analysis
- **Estimated Sharpe Ratio**: {self.analysis_results['performance']['sharpe_analysis']['estimated_sharpe']:.3f}
- **Classification**: {self.analysis_results['performance']['sharpe_analysis']['classification']}
- **Interpretation**: {self.analysis_results['performance']['sharpe_analysis']['interpretation']}

### Risk Metrics
- **Average Confidence**: {self.analysis_results['metrics']['average_confidence']:.3f}
- **Average Position Size**: {self.analysis_results['metrics']['average_position_size']:.2%}
- **Max Position Size**: {self.analysis_results['performance']['risk_metrics']['position_concentration']['max_position_size']:.2%}
- **Total Exposure**: {self.analysis_results['performance']['risk_metrics']['position_concentration']['total_exposure']:.2%}

## Signal Distribution

### By Signal Type
"""
        
        for signal_type, count in self.analysis_results['metrics']['signal_distribution'].items():
            percentage = (count / self.analysis_results['summary']['total_alerts']) * 100
            report_content += f"- **{signal_type}**: {count} signals ({percentage:.1f}%)\n"
        
        report_content += "\n### By Strategy\n"
        for strategy, count in self.analysis_results['metrics']['strategy_distribution'].items():
            percentage = (count / self.analysis_results['summary']['total_alerts']) * 100
            report_content += f"- **{strategy}**: {count} signals ({percentage:.1f}%)\n"
        
        report_content += "\n### By Asset\n"
        for asset, count in self.analysis_results['metrics']['asset_distribution'].items():
            percentage = (count / self.analysis_results['summary']['total_alerts']) * 100
            report_content += f"- **{asset}**: {count} signals ({percentage:.1f}%)\n"
        
        report_content += f"""

## Detailed Alert Analysis

### Alert Quality Assessment
- **High Confidence Signals** (>0.8): {len([a for a in self.alerts if a['confidence'] > 0.8])}
- **Medium Confidence Signals** (0.5-0.8): {len([a for a in self.alerts if 0.5 <= a['confidence'] <= 0.8])}
- **Low Confidence Signals** (<0.5): {len([a for a in self.alerts if a['confidence'] < 0.5])}

### Position Sizing Analysis
- **Conservative Positions** (<2%): {len([a for a in self.alerts if a['position_size'] < 0.02])}
- **Moderate Positions** (2-5%): {len([a for a in self.alerts if 0.02 <= a['position_size'] <= 0.05])}
- **Aggressive Positions** (>5%): {len([a for a in self.alerts if a['position_size'] > 0.05])}

## Recommendations

### Based on Sharpe Ratio Analysis
"""
        
        sharpe_ratio = self.analysis_results['performance']['sharpe_analysis']['estimated_sharpe']
        if sharpe_ratio > 1.5:
            report_content += "- **Excellent Performance**: Continue with current strategy mix and consider increasing position sizes\n"
        elif sharpe_ratio > 1.0:
            report_content += "- **Good Performance**: Strategy shows promise. Consider fine-tuning parameters for better results\n"
        elif sharpe_ratio > 0.5:
            report_content += "- **Acceptable Performance**: Strategy needs optimization. Review signal generation criteria\n"
        else:
            report_content += "- **Poor Performance**: Significant improvements needed. Consider strategy redesign\n"
        
        report_content += "\n### Risk Management Recommendations\n"
        
        # Risk recommendations based on metrics
        avg_confidence = self.analysis_results['metrics']['average_confidence']
        if avg_confidence < 0.6:
            report_content += "- **Low Signal Confidence**: Implement stricter signal filtering to improve quality\n"
        elif avg_confidence > 0.8:
            report_content += "- **High Signal Confidence**: Consider increasing position sizes for better returns\n"
        
        total_exposure = self.analysis_results['performance']['risk_metrics']['position_concentration']['total_exposure']
        if total_exposure > 0.5:
            report_content += "- **High Total Exposure**: Consider reducing position sizes to manage risk\n"
        elif total_exposure < 0.1:
            report_content += "- **Low Total Exposure**: Consider increasing position sizes for better returns\n"
        
        report_content += "\n### Strategy Optimization\n"
        
        # Strategy-specific recommendations
        for strategy, count in self.analysis_results['metrics']['strategy_distribution'].items():
            if count > len(self.alerts) * 0.5:
                report_content += f"- **{strategy} Dominance**: Consider diversifying strategy mix for better risk management\n"
            elif count < len(self.alerts) * 0.2:
                report_content += f"- **{strategy} Underutilization**: Consider increasing {strategy} signal generation\n"
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(output_dir, f"24h_alerts_analysis_report_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        # Save detailed results as JSON
        results_file = os.path.join(output_dir, f"24h_alerts_analysis_results_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        logger.info(f"Analysis report saved: {report_file}")
        logger.info(f"Detailed results saved: {results_file}")
        
        return report_file


def main():
    """Main execution function."""
    logger.info("Starting 24-hour alerts analysis")
    
    try:
        # Load and analyze alerts
        analyzer = AlertAnalyzer()
        alerts = analyzer.load_alerts()
        
        if not alerts:
            logger.warning("No alerts found for analysis. Exiting.")
            return
        
        # Generate analysis and report
        analysis_results = analyzer.analyze_alerts()
        report_file = analyzer.generate_report()
        
        # Print summary
        logger.info("=== ANALYSIS COMPLETE ===")
        logger.info(f"Total Alerts: {analysis_results['summary']['total_alerts']}")
        logger.info(f"Estimated Sharpe Ratio: {analysis_results['performance']['sharpe_analysis']['estimated_sharpe']:.3f}")
        logger.info(f"Potential ROI: {analysis_results['performance']['potential_roi']['total_potential_return']:.2%}")
        logger.info(f"Average Confidence: {analysis_results['metrics']['average_confidence']:.3f}")
        logger.info(f"Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise


if __name__ == "__main__":
    main()

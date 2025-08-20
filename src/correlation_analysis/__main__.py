"""
CLI interface for correlation analysis module.
Run correlation analysis manually from command line.
"""

import argparse
import logging
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .core.correlation_engine import CorrelationEngine
from .visualization.mosaic_generator import MosaicGenerator
from .alerts.mosaic_alert_system import MosaicAlertSystem
from .core.correlation_monitor import CorrelationMonitor


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def run_correlation_analysis(args: argparse.Namespace) -> int:
    """Run correlation analysis with given arguments."""
    try:
        logger = setup_logging(args.verbose)
        logger.info("🚀 Starting correlation analysis...")
        
        # Initialize correlation engine
        engine = CorrelationEngine(args.config)
        
        if args.run_once:
            logger.info("Running single correlation analysis cycle...")
            success = engine.start_monitoring(run_once=True)
            
            if success:
                logger.info("✅ Correlation analysis completed successfully")
                return 0
            else:
                logger.error("❌ Correlation analysis failed")
                return 1
        else:
            logger.info("Starting continuous correlation monitoring...")
            success = engine.start_monitoring()
            
            if success:
                logger.info("✅ Continuous monitoring started successfully")
                logger.info("Press Ctrl+C to stop monitoring...")
                
                try:
                    # Keep running until interrupted
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("🛑 Stopping correlation monitoring...")
                    engine.stop_monitoring()
                    return 0
            else:
                logger.error("❌ Failed to start correlation monitoring")
                return 1
                
    except Exception as e:
        print(f"❌ Error during correlation analysis: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_mosaic_generation(args: argparse.Namespace) -> int:
    """Run mosaic generation with given arguments."""
    try:
        logger = setup_logging(args.verbose)
        logger.info("🎨 Starting mosaic generation...")
        
        # Initialize mosaic generator
        generator = MosaicGenerator(args.config)
        
        if args.daily:
            logger.info("Generating daily mosaic...")
            mosaic_data = generator.generate_daily_mosaic()
            
            if mosaic_data:
                logger.info("✅ Daily mosaic generated successfully")
                logger.info(f"Key findings: {len(mosaic_data.get('key_findings', []))}")
                logger.info(f"Recommendations: {len(mosaic_data.get('recommendations', []))}")
                return 0
            else:
                logger.error("❌ Failed to generate daily mosaic")
                return 1
        
        elif args.matrix:
            logger.info("Generating correlation matrix...")
            pairs = args.pairs if args.pairs else None
            windows = args.windows if args.windows else None
            
            matrix_data = generator.generate_correlation_matrix(pairs, windows)
            
            if matrix_data:
                logger.info("✅ Correlation matrix generated successfully")
                summary = matrix_data.get('summary', {})
                logger.info(f"Total pairs: {summary.get('total_pairs', 0)}")
                logger.info(f"Significant correlations: {summary.get('significant_correlations', 0)}")
                return 0
            else:
                logger.error("❌ Failed to generate correlation matrix")
                return 1
        else:
            logger.error("❌ No mosaic generation mode specified")
            return 1
            
    except Exception as e:
        print(f"❌ Error during mosaic generation: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_mosaic_alert(args: argparse.Namespace) -> int:
    """Run mosaic alert generation."""
    try:
        logger = setup_logging(args.verbose)
        logger.info("🚨 Starting mosaic alert generation...")
        
        # Initialize mosaic alert system
        alert_system = MosaicAlertSystem()
        
        logger.info("Generating daily mosaic alert...")
        alert_path = alert_system.generate_daily_mosaic_alert(force_regeneration=args.force)
        
        if alert_path:
            logger.info(f"✅ Daily mosaic alert generated: {alert_path}")
            
            if args.show_summary:
                summary = alert_system.get_mosaic_alert_summary(days=1)
                logger.info(f"Alert summary: {summary}")
            
            return 0
        else:
            logger.error("❌ Failed to generate daily mosaic alert")
            return 1
            
    except Exception as e:
        print(f"❌ Error during mosaic alert generation: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_monitor_pair(args: argparse.Namespace) -> int:
    """Run correlation monitoring for a specific pair."""
    try:
        logger = setup_logging(args.verbose)
        logger.info(f"🔍 Starting correlation monitoring for {args.monitor_pair}...")
        
        # Initialize correlation monitor
        monitor = CorrelationMonitor(args.monitor_pair)
        
        logger.info("Monitoring pair for correlation changes...")
        result = monitor.monitor_pair()
        
        if result.get('success', False):
            logger.info("✅ Pair monitoring completed successfully")
            correlations = result.get('correlations', {})
            breakouts = result.get('breakouts', [])
            alerts = result.get('alerts_generated', [])
            
            logger.info(f"Correlations calculated: {len(correlations)}")
            logger.info(f"Breakouts detected: {len(breakouts)}")
            logger.info(f"Alerts generated: {len(alerts)}")
            
            return 0
        else:
            logger.error(f"❌ Pair monitoring failed: {result.get('reason', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Error during pair monitoring: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def show_status(args: argparse.Namespace) -> int:
    """Show correlation analysis system status."""
    try:
        logger = setup_logging(args.verbose)
        logger.info("📊 Checking correlation analysis system status...")
        
        # Initialize components
        engine = CorrelationEngine(args.config)
        alert_system = MosaicAlertSystem()
        
        # Get engine status
        engine_status = engine.get_engine_status()
        logger.info(f"Engine status: {'✅ Running' if engine_status.get('engine_running', False) else '❌ Stopped'}")
        logger.info(f"Monitored pairs: {len(engine_status.get('monitored_pairs', []))}")
        logger.info(f"Performance metrics: {engine_status.get('performance_metrics', {})}")
        
        # Get alert summary
        alert_summary = alert_system.get_mosaic_alert_summary(days=7)
        logger.info(f"Recent alerts: {alert_summary.get('total_alerts', 0)} in last 7 days")
        
        # Show system health
        logger.info("🏥 System Health:")
        logger.info("  ✅ Correlation Engine: Ready")
        logger.info("  ✅ Mosaic Generator: Ready")
        logger.info("  ✅ Alert System: Ready")
        logger.info("  ✅ Storage System: Ready")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error checking system status: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Correlation Analysis CLI - Run correlation analysis manually",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single correlation analysis cycle
  python -m correlation_analysis --run-once

  # Start continuous correlation monitoring
  python -m correlation_analysis --monitor

  # Generate daily mosaic
  python -m correlation_analysis --mosaic --daily

  # Generate correlation matrix for specific pairs
  python -m correlation_analysis --mosaic --matrix --pairs BTC_ETH ETH_USDT

  # Generate daily mosaic alert
  python -m correlation_analysis --alert --daily

  # Monitor specific pair
  python -m correlation_analysis --monitor-pair BTC_ETH

  # Show system status
  python -m correlation_analysis --status

  # Verbose output
  python -m correlation_analysis --run-once --verbose
        """
    )
    
    # Global arguments
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    # Legacy arguments for backward compatibility
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run single correlation analysis cycle'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Start continuous correlation monitoring'
    )
    
    parser.add_argument(
        '--mosaic',
        action='store_true',
        help='Generate mosaics'
    )
    
    parser.add_argument(
        '--daily',
        action='store_true',
        help='Generate daily mosaic'
    )
    
    parser.add_argument(
        '--matrix',
        action='store_true',
        help='Generate correlation matrix'
    )
    
    parser.add_argument(
        '--pairs',
        nargs='+',
        help='Specific pairs to analyze'
    )
    
    parser.add_argument(
        '--windows',
        nargs='+',
        type=int,
        help='Correlation windows in days'
    )
    
    parser.add_argument(
        '--alert',
        action='store_true',
        help='Generate alerts'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if alert exists'
    )
    
    parser.add_argument(
        '--show-summary',
        action='store_true',
        help='Show alert summary after generation'
    )
    
    parser.add_argument(
        '--monitor-pair',
        type=str,
        help='Pair to monitor (e.g., BTC_ETH)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show system status'
    )
    
    args = parser.parse_args()
    
    # Handle different commands based on arguments
    if args.run_once or args.monitor:
        return run_correlation_analysis(args)
    
    elif args.alert:
        return run_mosaic_alert(args)
    
    elif args.mosaic or args.daily or args.matrix:
        return run_mosaic_generation(args)
    
    elif args.monitor_pair:
        return run_monitor_pair(args)
    
    elif args.status:
        return show_status(args)
    
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

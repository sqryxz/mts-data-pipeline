#!/usr/bin/env python3
"""
Main entry point for the MTS Crypto Data Pipeline.

This script provides a command-line interface for manually triggering
data collection and other operations.
"""

import sys
import argparse
import logging
import os
import json
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.logging_config import setup_logging
from config.settings import Config
from src.services.collector import DataCollector
from src.services.macro_collector import MacroDataCollector
from src.services.scheduler import SimpleScheduler
from src.services.monitor import HealthChecker
from src.utils.exceptions import CryptoDataPipelineError


class HealthRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health monitoring endpoints."""
    
    health_checker = None  # Will be set by the server factory
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self._handle_health_check()
        else:
            self._handle_not_found()
    
    def _handle_health_check(self):
        """Handle health check endpoint."""
        try:
            # Get system health status
            health_status = self.health_checker.get_system_health_status()
            
            # Convert to response format
            response = {
                'status': health_status['status'],
                'healthy': health_status['healthy'],
                'message': health_status['message'],
                'timestamp': health_status['checked_at'],
                'components': health_status['components']
            }
            
            # Send response
            self._send_json_response(200, response)
            
        except Exception as e:
            # Handle errors gracefully
            error_response = {
                'status': 'error',
                'healthy': False,
                'message': f'Health check failed: {str(e)}',
                'timestamp': HealthChecker().get_system_health_status()['checked_at']
            }
            self._send_json_response(500, error_response)
    
    def _handle_not_found(self):
        """Handle 404 Not Found."""
        response = {
            'status': 'error',
            'message': 'Endpoint not found. Available endpoints: /health',
            'path': self.path
        }
        self._send_json_response(404, response)
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger = logging.getLogger('health_server')
        logger.info(f"{self.client_address[0]} - {format % args}")


def setup_application() -> tuple[DataCollector, logging.Logger]:
    """
    Initialize the application with all required services.
    
    Returns:
        Tuple of (collector, logger) instances
    """
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Log application startup
    logger.info("Initializing MTS Crypto Data Pipeline")
    
    try:
        # Load configuration
        config = Config()
        logger.info(f"Configuration loaded - API Base URL: {config.COINGECKO_BASE_URL}")
        
        # Initialize data collector with default dependencies
        collector = DataCollector()
        logger.info("Data collector initialized successfully")
        
        return collector, logger
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise


def run_collection(collector: DataCollector, logger: logging.Logger, days: int = 1) -> bool:
    """
    Execute the data collection process.
    
    Args:
        collector: DataCollector instance
        logger: Logger instance
        days: Number of days of data to collect (default: 1)
        
    Returns:
        bool: True if collection was successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("STARTING MANUAL DATA COLLECTION")
    logger.info("=" * 60)
    
    try:
        # Run the collection
        results = collector.collect_all_data(days=days)
        
        # Log summary results
        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total cryptocurrencies attempted: {results['total_attempted']}")
        logger.info(f"Successful collections: {results['successful']}")
        logger.info(f"Failed collections: {results['failed']}")
        logger.info(f"Total retries used: {results['retries_used']}")
        logger.info(f"Collection duration: {results['duration_seconds']:.2f} seconds")
        
        if results['successful_cryptos']:
            logger.info(f"Successfully collected data for: {', '.join(results['successful_cryptos'])}")
        
        if results['failed_cryptos']:
            logger.warning(f"Failed to collect data for: {', '.join(results['failed_cryptos'])}")
        
        if results['error_categories']:
            logger.warning(f"Error categories encountered: {results['error_categories']}")
        
        # Determine overall success
        collection_success = results['successful'] > 0
        if collection_success:
            logger.info("✅ Data collection completed successfully")
        else:
            logger.error("❌ Data collection failed - no cryptocurrencies collected")
        
        logger.info("=" * 60)
        return collection_success
        
    except CryptoDataPipelineError as e:
        logger.error(f"Pipeline error during collection: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during collection: {e}")
        return False


def run_macro_collection(logger: logging.Logger, days: int = 30, indicators: list = None) -> bool:
    """
    Execute the macro data collection process.
    
    Args:
        logger: Logger instance
        days: Number of days of data to collect (default: 30)
        indicators: List of indicators to collect (default: ALL)
        
    Returns:
        bool: True if collection was successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("STARTING MACRO DATA COLLECTION")
    logger.info("=" * 60)
    
    try:
        # Initialize macro collector
        macro_collector = MacroDataCollector()
        
        # Handle indicators list
        if not indicators or 'ALL' in indicators:
            logger.info("Collecting all macro indicators...")
            results = macro_collector.collect_all_indicators(days=days)
        else:
            logger.info(f"Collecting specific indicators: {', '.join(indicators)}")
            results = {}
            for indicator in indicators:
                try:
                    records = macro_collector.collect_indicator(indicator, days=days)
                    results[indicator] = records
                except Exception as e:
                    logger.error(f"Failed to collect {indicator}: {e}")
                    results[indicator] = []
        
        # Log summary results
        logger.info("=" * 60)
        logger.info("MACRO COLLECTION SUMMARY")
        logger.info("=" * 60)
        
        successful_indicators = [k for k, v in results.items() if v]
        failed_indicators = [k for k, v in results.items() if not v]
        total_records = sum(len(records) for records in results.values())
        valid_records = sum(sum(1 for r in records if r.value is not None) for records in results.values())
        
        logger.info(f"Total indicators attempted: {len(results)}")
        logger.info(f"Successful indicators: {len(successful_indicators)}")
        logger.info(f"Failed indicators: {len(failed_indicators)}")
        logger.info(f"Total records collected: {total_records}")
        logger.info(f"Valid data points: {valid_records}")
        logger.info(f"Missing data points: {total_records - valid_records}")
        
        if successful_indicators:
            logger.info(f"Successfully collected: {', '.join(successful_indicators)}")
        
        if failed_indicators:
            logger.warning(f"Failed to collect: {', '.join(failed_indicators)}")
        
        # Determine overall success
        collection_success = len(successful_indicators) > 0
        if collection_success:
            logger.info("✅ Macro data collection completed successfully")
        else:
            logger.error("❌ Macro data collection failed - no indicators collected")
        
        logger.info("=" * 60)
        return collection_success
        
    except Exception as e:
        logger.error(f"Unexpected error during macro collection: {e}")
        return False


def run_scheduler(logger: logging.Logger, 
                 interval_minutes: int = 60,
                 days: int = 1,
                 collect_crypto: bool = True,
                 collect_macro: bool = False,
                 macro_indicators: list = None) -> None:
    """
    Start the automated scheduler for data collection.
    
    Args:
        logger: Logger instance
        interval_minutes: Minutes between collections (default: 60)
        days: Number of days of data to collect each run (default: 1)
        collect_crypto: Whether to collect crypto data (default: True)
        collect_macro: Whether to collect macro data (default: False)
        macro_indicators: List of macro indicators to collect (default: None = all)
    """
    logger.info("=" * 60)
    logger.info("STARTING AUTOMATED DATA COLLECTION SCHEDULER")
    logger.info("=" * 60)
    
    try:
        # Initialize collectors
        collector = None
        macro_collector = None
        
        if collect_crypto:
            collector = DataCollector()
            logger.info("✅ Crypto collector initialized")
        
        if collect_macro:
            macro_collector = MacroDataCollector()
            logger.info("✅ Macro collector initialized")
        
        # Create scheduler with configuration
        scheduler = SimpleScheduler(
            collector=collector,
            macro_collector=macro_collector,
            interval_seconds=interval_minutes * 60,
            days_to_collect=days,
            collect_crypto=collect_crypto,
            collect_macro=collect_macro,
            macro_indicators=macro_indicators
        )
        
        # Log configuration
        logger.info(f"📅 Collection interval: {interval_minutes} minutes")
        logger.info(f"📊 Days per collection: {days}")
        logger.info(f"🪙 Crypto collection: {'✅ Enabled' if collect_crypto else '❌ Disabled'}")
        logger.info(f"📈 Macro collection: {'✅ Enabled' if collect_macro else '❌ Disabled'}")
        if collect_macro and macro_indicators:
            logger.info(f"📋 Macro indicators: {', '.join(macro_indicators)}")
        
        logger.info("Press Ctrl+C to stop the scheduler")
        logger.info("=" * 60)
        
        # Start scheduler
        if scheduler.start():
            try:
                # Keep the main thread alive
                while scheduler.is_running():
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal, stopping scheduler...")
                scheduler.stop()
                logger.info("✅ Scheduler stopped gracefully")
        else:
            logger.error("❌ Failed to start scheduler")
            
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise
    finally:
        logger.info("Automated scheduler stopped")


def run_server(logger: logging.Logger, port: int = 8080) -> None:
    """
    Start the HTTP health monitoring server.
    
    Args:
        logger: Logger instance
        port: Port to listen on (default: 8080)
    """
    logger.info("=" * 60)
    logger.info("STARTING HEALTH MONITORING SERVER")
    logger.info("=" * 60)
    
    try:
        # Initialize health checker
        health_checker = HealthChecker()
        
        # Set health checker as class variable
        HealthRequestHandler.health_checker = health_checker
        
        # Create and configure HTTP server
        server = HTTPServer(('0.0.0.0', port), HealthRequestHandler)
        
        logger.info(f"Health server listening on http://0.0.0.0:{port}")
        logger.info("Available endpoints:")
        logger.info(f"  • GET /health - System health status")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("=" * 60)
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping server...")
            server.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start serving requests
        server.serve_forever()
        
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {port} is already in use. Please choose a different port or stop the existing service.")
        else:
            logger.error(f"Failed to start server: {e}")
        raise
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        logger.info("Health monitoring server stopped")


def main():
    """
    Main entry point for the application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="MTS Crypto Data Pipeline - Collect cryptocurrency market data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --collect                    # Collect latest crypto data (1 day)
  python main.py --collect --days 7          # Collect 7 days of crypto data
  python main.py --collect-macro             # Collect all macro indicators
  python main.py --collect-macro --macro-indicators VIX DXY  # Collect specific indicators
  python main.py --collect --collect-macro   # Collect both crypto and macro data
  python main.py --schedule --collect        # Schedule crypto data collection (every 60 min)
  python main.py --schedule --collect-macro  # Schedule macro data collection
  python main.py --schedule --collect --collect-macro --interval 30  # Schedule both every 30 min
  python main.py --server                    # Start health monitoring server
  python main.py --server --port 9090       # Start server on custom port
  python main.py --version                   # Show version info
        """
    )
    
    parser.add_argument(
        '--collect',
        action='store_true',
        help='Trigger data collection for top 3 cryptocurrencies'
    )
    
    parser.add_argument(
        '--collect-macro',
        action='store_true',
        help='Trigger macro economic indicators collection'
    )
    
    parser.add_argument(
        '--macro-indicators',
        nargs='+',
        choices=['VIX', 'DXY', 'TREASURY_10Y', 'FED_FUNDS_RATE', 'ALL'],
        default=None,
        help='Specific macro indicators to collect (default: ALL)'
    )
    
    parser.add_argument(
        '--server',
        action='store_true',
        help='Start HTTP health monitoring server'
    )
    
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Start automated data collection scheduler'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Minutes between scheduled collections (default: 60)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days of data to collect (default: 1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for health monitoring server (default: 8080)'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    args = parser.parse_args()
    
    # Handle version request
    if args.version:
        print("MTS Crypto Data Pipeline v1.0.0")
        print("Collects OHLCV data for Bitcoin, Ethereum, and top market cap cryptocurrency")
        return 0
    
    # Validate arguments
    if args.days < 1:
        print("Error: --days must be a positive integer", file=sys.stderr)
        return 1
    
    if args.days > 365:
        print("Error: --days cannot exceed 365 (API limitations)", file=sys.stderr)
        return 1
    
    if args.port < 1 or args.port > 65535:
        print("Error: --port must be between 1 and 65535", file=sys.stderr)
        return 1
    
    if args.interval < 1:
        print("Error: --interval must be a positive integer (minutes)", file=sys.stderr)
        return 1
    
    # Check for conflicting arguments
    if args.server and (args.collect or args.collect_macro or args.schedule):
        print("Error: Cannot specify other options with --server", file=sys.stderr)
        return 1
    
    if args.schedule and not (args.collect or args.collect_macro):
        print("Error: --schedule requires at least one of --collect or --collect-macro", file=sys.stderr)
        return 1
    
    # Validate macro indicators argument - only check if explicitly provided
    if args.macro_indicators is not None and not args.collect_macro:
        print("Error: --macro-indicators can only be used with --collect-macro", file=sys.stderr)
        return 1
    
    # Validate interval argument
    if args.interval != 60 and not args.schedule:  # 60 is the default
        print("Error: --interval can only be used with --schedule", file=sys.stderr)
        return 1
    
    # If no action specified, show help
    if not args.collect and not args.collect_macro and not args.server and not args.schedule:
        parser.print_help()
        return 0
    
    try:
        # Initialize application
        collector, logger = setup_application()
        
        # Set log level if verbose
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")
        
        # Execute requested actions
        if args.server:
            run_server(logger, port=args.port)
            return 0
        
        if args.schedule:
            # Handle macro indicators processing
            macro_indicators = None
            if args.collect_macro and args.macro_indicators:
                macro_indicators = args.macro_indicators if 'ALL' not in args.macro_indicators else None
            
            run_scheduler(
                logger=logger,
                interval_minutes=args.interval,
                days=args.days,
                collect_crypto=args.collect,
                collect_macro=args.collect_macro,
                macro_indicators=macro_indicators
            )
            return 0
        
        # Manual collection mode
        crypto_success = True
        macro_success = True
        
        if args.collect:
            crypto_success = run_collection(collector, logger, days=args.days)
        
        if args.collect_macro:
            indicators = args.macro_indicators if args.macro_indicators is not None else ['ALL']
            macro_success = run_macro_collection(logger, days=args.days, indicators=indicators)
        
        # Return overall success
        overall_success = crypto_success and macro_success
        return 0 if overall_success else 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
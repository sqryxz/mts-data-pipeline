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
  python main.py --collect                    # Collect latest data (1 day)
  python main.py --collect --days 7          # Collect 7 days of data
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
        '--server',
        action='store_true',
        help='Start HTTP health monitoring server'
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
    
    # Check for conflicting arguments
    if args.collect and args.server:
        print("Error: Cannot specify both --collect and --server", file=sys.stderr)
        return 1
    
    # If no action specified, show help
    if not args.collect and not args.server:
        parser.print_help()
        return 0
    
    try:
        # Initialize application
        collector, logger = setup_application()
        
        # Set log level if verbose
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")
        
        # Execute requested action
        if args.collect:
            success = run_collection(collector, logger, days=args.days)
            return 0 if success else 1
        elif args.server:
            run_server(logger, port=args.port)
            return 0
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
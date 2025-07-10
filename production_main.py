#!/usr/bin/env python3
"""
Production Main Entry Point for MTS Crypto Data Pipeline.

This script orchestrates the entire production system including:
- Data collection (crypto and macro)
- Real-time data collection (order books, funding rates)
- Signal generation and aggregation
- API server management
- Health monitoring and alerting
- Scheduled operations
"""

import sys
import os
import argparse
import logging
import signal
import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import psutil

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from config.logging_config import setup_logging
from src.services.collector import DataCollector
from src.services.macro_collector import MacroDataCollector
from src.services.multi_strategy_generator import MultiStrategyGenerator
from src.services.scheduler import SimpleScheduler
from src.services.monitor import HealthChecker
from src.services.orderbook_collector import OrderBookCollector
from src.services.funding_collector import FundingCollector
from src.data.realtime_storage import RealtimeStorage
from src.utils.exceptions import CryptoDataPipelineError


class ProductionOrchestrator:
    """
    Production orchestrator for the MTS pipeline.
    
    Manages all production services including:
    - Data collection services
    - Real-time data collection
    - Signal generation
    - Health monitoring
    - Alerting system
    - API server
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Service instances
        self.data_collector: Optional[DataCollector] = None
        self.macro_collector: Optional[MacroDataCollector] = None
        self.signal_generator: Optional[MultiStrategyGenerator] = None
        self.health_checker: Optional[HealthChecker] = None
        
        # Real-time service instances
        self.realtime_storage: Optional[RealtimeStorage] = None
        self.orderbook_collector: Optional[OrderBookCollector] = None
        self.funding_collector: Optional[FundingCollector] = None
        
        # Control flags
        self._shutdown_requested = False
        self._services_running = False
        
        # Process management
        self._api_process: Optional[mp.Process] = None
        self._scheduler_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._realtime_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._last_collection_time = None
        self._last_signal_generation_time = None
        self._performance_metrics = {
            'collections_completed': 0,
            'signals_generated': 0,
            'realtime_collections': 0,
            'errors_encountered': 0,
            'uptime_start': datetime.now()
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Production orchestrator initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown_requested = True

    def initialize_services(self):
        """Initialize all services"""
        self.logger.info("Initializing production services...")
        
        try:
            # Initialize health checker first
            self.health_checker = HealthChecker()
            
            # Initialize data collection services
            self.data_collector = DataCollector()
            self.macro_collector = MacroDataCollector()
            
            # Initialize real-time services if enabled
            if self.config.REALTIME_ENABLED:
                self.logger.info("Initializing real-time services...")
                self.realtime_storage = RealtimeStorage(
                    db_path=self.config.REALTIME_DB_PATH,
                    csv_dir=self.config.REALTIME_DATA_DIR
                )
                self.orderbook_collector = OrderBookCollector(storage=self.realtime_storage)
                self.funding_collector = FundingCollector(storage=self.realtime_storage)
                self.logger.info("Real-time services initialized")
            
            # Initialize signal generation
            self.signal_generator = MultiStrategyGenerator({}, {})
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise

    def start_api_server(self):
        """Start the FastAPI server in a separate process"""
        if self._api_process and self._api_process.is_alive():
            self.logger.warning("API server already running")
            return
        
        try:
            # Import and start API server
            from src.api.signal_api import app
            import uvicorn
            
            def run_api():
                uvicorn.run(
                    app,
                    host=self.config.API_HOST,
                    port=self.config.API_PORT,
                    workers=1,  # Single worker for simplicity in production
                    log_level=self.config.LOG_LEVEL.lower()
                )
            
            self._api_process = mp.Process(target=run_api)
            self._api_process.start()
            
            self.logger.info(f"API server started on {self.config.API_HOST}:{self.config.API_PORT}")
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            raise

    async def start_realtime_collection(self):
        """Start real-time data collection"""
        if not self.config.REALTIME_ENABLED:
            self.logger.info("Real-time collection disabled in configuration")
            return
        
        try:
            self.logger.info("Starting real-time data collection...")
            
            # Start order book collection
            orderbook_task = asyncio.create_task(
                self.orderbook_collector.start_collection(self.config.REALTIME_SYMBOLS)
            )
            
            # Start funding rate collection
            funding_task = asyncio.create_task(
                self.funding_collector.start_periodic_collection()
            )
            
            # Wait for both tasks
            await asyncio.gather(orderbook_task, funding_task)
            
        except Exception as e:
            self.logger.error(f"Real-time collection failed: {e}")
            self._performance_metrics['errors_encountered'] += 1

    def start_production_services(self):
        """Start all production services"""
        self.logger.info("Starting production services...")
        
        try:
            # Initialize services
            self.initialize_services()
            
            # Start API server
            self.start_api_server()
            
            self._services_running = True
            
            self.logger.info("All production services started successfully")
            self.logger.info(f"API available at: http://{self.config.API_HOST}:{self.config.API_PORT}")
            self.logger.info(f"Health check at: http://{self.config.API_HOST}:{self.config.API_PORT}/health")
            
            # Start real-time collection if enabled
            if self.config.REALTIME_ENABLED:
                # Run real-time collection in the background
                def run_realtime():
                    asyncio.run(self.start_realtime_collection())
                
                realtime_thread = threading.Thread(target=run_realtime, daemon=True)
                realtime_thread.start()
                self.logger.info("Real-time data collection started")
            
            # Main loop
            while not self._shutdown_requested:
                time.sleep(5)
                
                # Check for dead processes
                if self._api_process and not self._api_process.is_alive():
                    self.logger.error("API process died, restarting...")
                    self.start_api_server()
            
            self.logger.info("Shutdown requested, stopping services...")
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down...")
        except Exception as e:
            self.logger.error(f"Production services failed: {e}")
            raise
        finally:
            self.stop_production_services()

    def start_realtime_only(self):
        """Start only real-time data collection services"""
        self.logger.info("Starting real-time-only mode...")
        
        try:
            # Initialize only real-time services
            self.health_checker = HealthChecker()
            
            if not self.config.REALTIME_ENABLED:
                raise ValueError("Real-time collection must be enabled for real-time-only mode")
            
            self.realtime_storage = RealtimeStorage(
                db_path=self.config.REALTIME_DB_PATH,
                csv_dir=self.config.REALTIME_DATA_DIR
            )
            self.orderbook_collector = OrderBookCollector(storage=self.realtime_storage)
            self.funding_collector = FundingCollector(storage=self.realtime_storage)
            
            self._services_running = True
            
            # Run real-time collection
            asyncio.run(self.start_realtime_collection())
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down...")
        except Exception as e:
            self.logger.error(f"Real-time services failed: {e}")
            raise
        finally:
            self.stop_production_services()

    def start_collector_only(self):
        """Start only data collection services"""
        self.logger.info("Starting collector-only mode...")
        
        try:
            # Initialize collection services
            self.health_checker = HealthChecker()
            self.data_collector = DataCollector()
            self.macro_collector = MacroDataCollector()
            
            self._services_running = True
            
            # Run scheduled collection
            scheduler = SimpleScheduler(
                interval_minutes=self.config.DATA_COLLECTION_INTERVAL_MINUTES,
                days=1,
                collect_crypto=True,
                collect_macro=True
            )
            
            scheduler.start()
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down...")
        except Exception as e:
            self.logger.error(f"Collector services failed: {e}")
            raise
        finally:
            self.stop_production_services()

    def stop_production_services(self):
        """Stop all production services gracefully"""
        self.logger.info("Stopping production services...")
        
        self._services_running = False
        
        # Stop real-time collection
        if self.orderbook_collector:
            try:
                asyncio.run(self.orderbook_collector.stop_collection())
            except Exception as e:
                self.logger.error(f"Error stopping order book collector: {e}")
        
        if self.funding_collector:
            try:
                asyncio.run(self.funding_collector.stop_collection())
            except Exception as e:
                self.logger.error(f"Error stopping funding collector: {e}")
        
        # Stop API process
        if self._api_process and self._api_process.is_alive():
            self.logger.info("Stopping API server...")
            self._api_process.terminate()
            self._api_process.join(timeout=10)
            if self._api_process.is_alive():
                self._api_process.kill()
        
        self.logger.info("All production services stopped")


def main():
    """Main entry point for production deployment"""
    parser = argparse.ArgumentParser(description="MTS Production Pipeline")
    parser.add_argument(
        '--mode',
        choices=['full', 'api-only', 'collector-only', 'signals-only', 'realtime-only'],
        default='full',
        help='Production mode to run'
    )
    parser.add_argument(
        '--config-env',
        default='production',
        help='Configuration environment (development, staging, production)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Set environment
    os.environ['ENVIRONMENT'] = args.config_env
    os.environ['LOG_LEVEL'] = args.log_level
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = Config()
        logger.info(f"Starting MTS Pipeline in {args.mode} mode")
        logger.info(f"Environment: {config.ENVIRONMENT.value}")
        logger.info(f"Real-time enabled: {config.REALTIME_ENABLED}")
        
        # Create orchestrator
        orchestrator = ProductionOrchestrator(config)
        
        if args.mode == 'full':
            # Start all services
            orchestrator.start_production_services()
        
        elif args.mode == 'api-only':
            # Start only API server
            orchestrator.initialize_services()
            orchestrator.start_api_server()
            
            # Wait for shutdown
            while not orchestrator._shutdown_requested:
                time.sleep(1)
            
            orchestrator.stop_production_services()
        
        elif args.mode == 'collector-only':
            # Start only data collection
            orchestrator.start_collector_only()
        
        elif args.mode == 'realtime-only':
            # Start only real-time data collection
            orchestrator.start_realtime_only()
        
        elif args.mode == 'signals-only':
            # Start only signal generation (existing functionality)
            orchestrator.initialize_services()
            # Add signal-only logic here
            logger.info("Signals-only mode not yet implemented")
        
    except Exception as e:
        logger.error(f"Production pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
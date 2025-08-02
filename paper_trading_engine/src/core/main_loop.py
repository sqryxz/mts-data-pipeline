"""
Main execution loop for continuous signal processing
"""

import time
import logging
import signal
import sys
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from .models import TradingSignal
from .health_checker import HealthChecker
from .error_handler import ErrorHandler, ErrorSeverity, GracefulShutdown
from ..portfolio.portfolio_manager import PortfolioManager
from ..execution.execution_engine import ExecutionEngine
from ..services.market_data_service import MarketDataService
from ..analytics.report_generator import ReportGenerator
from ..core.enums import SignalType  # Moved to top level


class MainExecutionLoop:
    """Main execution loop for continuous signal processing"""
    
    def __init__(self,
                 signal_directory: str = "data/alerts",
                 portfolio_manager: Optional[PortfolioManager] = None,
                 execution_engine: Optional[ExecutionEngine] = None,
                 poll_interval: float = 1.0,
                 error_retry_interval: float = 5.0,
                 report_directory: str = "data/reports",
                 health_check_interval: float = 30.0):
        self.signal_directory = Path(signal_directory)
        self.signal_directory.mkdir(parents=True, exist_ok=True)
        self.portfolio_manager = portfolio_manager or PortfolioManager(initial_capital=10000.0)
        self.execution_engine = execution_engine or ExecutionEngine(self.portfolio_manager)
        self.market_data = MarketDataService(use_real_time=True)
        self.report_generator = ReportGenerator(output_directory=report_directory)
        
        # Production features
        self.health_checker = HealthChecker()
        self.error_handler = ErrorHandler(max_errors=1000, error_threshold=10)
        
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.processed_files = set()
        self.last_status_print = None  # Track last status print time
        self.last_health_check = None
        self.poll_interval = poll_interval
        self.error_retry_interval = error_retry_interval
        self.health_check_interval = health_check_interval
        self.stats = {
            'signals_processed': 0, 'trades_executed': 0, 'errors': 0,
            'start_time': None, 'last_signal_time': None
        }
        
        # Register shutdown and recovery callbacks
        self._register_callbacks()
    
    def _register_callbacks(self):
        """Register shutdown and recovery callbacks"""
        # Register shutdown callbacks
        self.error_handler.register_shutdown_callback(self._save_portfolio_state)
        self.error_handler.register_shutdown_callback(self._generate_final_report)
        self.error_handler.register_shutdown_callback(self._log_final_stats)
        
        # Register recovery callbacks
        self.error_handler.register_recovery_callback(self._reload_portfolio_state)
        self.error_handler.register_recovery_callback(self._reset_error_counters)
    
    def _save_portfolio_state(self):
        """Save portfolio state during shutdown"""
        try:
            self.portfolio_manager.save_state()
            self.logger.info("Portfolio state saved during shutdown")
        except Exception as e:
            self.logger.error(f"Failed to save portfolio state: {e}")
    
    def _reload_portfolio_state(self):
        """Reload portfolio state during recovery"""
        try:
            self.portfolio_manager.load_state()
            self.logger.info("Portfolio state reloaded during recovery")
        except Exception as e:
            self.logger.error(f"Failed to reload portfolio state: {e}")
    
    def _reset_error_counters(self):
        """Reset error counters during recovery"""
        self.stats['errors'] = 0
        self.logger.info("Error counters reset during recovery")
    
    def _log_final_stats(self):
        """Log final statistics during shutdown"""
        try:
            self._print_final_stats()
        except Exception as e:
            self.logger.error(f"Failed to log final stats: {e}")
    
    def start(self):
        """Start the main execution loop"""
        
        self.logger.info("Starting main execution loop...")
        self.logger.info(f"Monitoring directory: {self.signal_directory}")
        self.logger.info(f"Initial portfolio value: ${self.portfolio_manager.get_total_value():.2f}")
        
        # Initialize portfolio
        self.portfolio_manager.initialize()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # Use graceful shutdown context manager
        with GracefulShutdown(self.error_handler):
            try:
                self._main_loop()
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, shutting down...")
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                self.error_handler.handle_error(e, context={"type": "main_loop_error"}, 
                                             severity=ErrorSeverity.CRITICAL)
                raise
            finally:
                self.stop()
    
    def stop(self):
        """Stop the main execution loop"""
        
        self.running = False
        self.logger.info("Stopping main execution loop...")
        
        # Print final statistics
        self._print_final_stats()
    
    def _main_loop(self):
        """Main processing loop with error handling and health checking"""
        while self.running:
            try:
                # Check system health periodically
                self._check_system_health()
                
                # Process signals
                self._process_signal_files()
                
                # Update position prices
                self._update_position_prices()
                
                # Print status
                self._print_status()
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.stats['errors'] += 1
                
                # Handle error through error handler
                self.error_handler.handle_error(e, context={"type": "main_loop_iteration"}, 
                                             severity=ErrorSeverity.MEDIUM)
                
                # Check if system should continue
                if not self.error_handler.is_system_healthy():
                    self.logger.warning("System health check failed, considering shutdown")
                
                time.sleep(self.error_retry_interval)
    
    def _check_system_health(self):
        """Check system health periodically"""
        if (self.last_health_check is None or 
            (datetime.now() - self.last_health_check).total_seconds() >= self.health_check_interval):
            
            try:
                health_data = self.health_checker.check_system_health()
                
                if health_data['status'] == 'critical':
                    self.logger.critical("System health check failed - CRITICAL")
                    self.error_handler.handle_error(
                        Exception("System health check failed"),
                        context={"health_data": health_data},
                        severity=ErrorSeverity.CRITICAL
                    )
                elif health_data['status'] == 'warning':
                    self.logger.warning("System health check - WARNING")
                
                self.last_health_check = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                self.error_handler.handle_error(e, context={"type": "health_check"}, 
                                             severity=ErrorSeverity.MEDIUM)
    
    def _process_signal_files(self):
        """Process new signal files in the monitored directory"""
        
        try:
            # Look for JSON files in the signal directory
            for file_path in self.signal_directory.glob("*.json"):
                if file_path.name not in self.processed_files:
                    try:
                        self._process_signal_file(file_path)
                    except Exception as e:
                        self.logger.error(f"Error processing signal file {file_path}: {e}")
                        self.stats['errors'] += 1
                        self.error_handler.handle_error(e, context={"file_path": str(file_path)}, 
                                                     severity=ErrorSeverity.MEDIUM)
                    
        except Exception as e:
            self.logger.error(f"Error processing signal files: {e}")
            self.stats['errors'] += 1
            self.error_handler.handle_error(e, context={"type": "signal_directory_scan"}, 
                                         severity=ErrorSeverity.MEDIUM)
        
        # Memory management: limit processed_files set size
        if len(self.processed_files) > 1000:
            self.logger.info(f"Clearing processed files cache (size: {len(self.processed_files)})")
            self.processed_files.clear()
    
    def _process_signal_file(self, file_path: Path):
        """Process a single signal file with enhanced error handling"""
        try:
            # Check if file is still being written (race condition protection)
            initial_size = file_path.stat().st_size
            time.sleep(0.1)  # Wait a bit
            if file_path.stat().st_size != initial_size:
                self.logger.debug(f"File {file_path.name} still being written, skipping")
                return
            
            self.logger.info(f"Processing signal file: {file_path.name}")
            signal_obj = self._parse_signal_file(file_path)
            
            if signal_obj:
                try:
                    result = self.execution_engine.process_signal(signal_obj)
                    if result and result.success:
                        self.logger.info(f"Signal processed successfully: {signal_obj.asset} {signal_obj.signal_type}")
                        self.stats['signals_processed'] += 1
                        self.stats['trades_executed'] += 1
                        self.stats['last_signal_time'] = datetime.now()
                    else:
                        self.logger.warning(f"Signal processing failed: {signal_obj.asset}")
                        self.stats['signals_processed'] += 1
                        self.error_handler.handle_error(
                            Exception(f"Signal processing failed for {signal_obj.asset}"),
                            context={"signal": signal_obj.__dict__, "file_path": str(file_path)},
                            severity=ErrorSeverity.MEDIUM
                        )
                except Exception as e:
                    self.logger.error(f"Error executing signal {signal_obj.asset}: {e}")
                    self.error_handler.handle_error(e, context={"signal": signal_obj.__dict__, "file_path": str(file_path)}, 
                                                 severity=ErrorSeverity.MEDIUM)
                    self.stats['errors'] += 1
            else:
                self.logger.warning(f"Failed to parse signal file: {file_path.name}")
                self.error_handler.handle_error(
                    Exception(f"Failed to parse signal file: {file_path.name}"),
                    context={"file_path": str(file_path)},
                    severity=ErrorSeverity.LOW
                )
                # Don't mark as processed if parsing failed
                return
            
            # Only mark as processed if we successfully processed or attempted to process
            self.processed_files.add(file_path.name)
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path.name}: {e}")
            self.stats['errors'] += 1
            self.error_handler.handle_error(e, context={"file_path": str(file_path)}, 
                                         severity=ErrorSeverity.MEDIUM)
            # Don't mark as processed if there was an error
    
    def _parse_signal_file(self, file_path: Path) -> Optional[TradingSignal]:
        """Parse a signal file and return a TradingSignal"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            signal_type_map = {'LONG': SignalType.LONG, 'SHORT': SignalType.SHORT, 'EXIT': SignalType.EXIT}
            timestamp_str = data.get('timestamp', datetime.now().isoformat())
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if isinstance(timestamp_str, str) else datetime.now()
            
            return TradingSignal(
                asset=data.get('asset', 'BTC'), 
                signal_type=signal_type_map.get(data.get('signal_type', 'LONG'), SignalType.LONG),
                price=data.get('price', 50000.0), 
                confidence=data.get('confidence', 0.8),
                timestamp=timestamp, 
                source=file_path.name, 
                metadata=data
            )
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing signal file {file_path.name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing signal file {file_path.name}: {e}")
            return None
    
    def _update_position_prices(self):
        """Update current prices for open positions"""
        
        try:
            # Get current prices for all assets with open positions
            current_prices = {}
            for asset in self.portfolio_manager.positions.keys():
                current_price = self.market_data.get_current_price(asset)
                current_prices[asset] = current_price
            
            # Update position prices
            if current_prices:
                self.portfolio_manager.update_position_prices(current_prices)
                
        except Exception as e:
            self.logger.error(f"Error updating position prices: {e}")
    
    def _print_status(self):
        """Print periodic status information"""
        current_time = datetime.now()
        if (self.last_status_print is None or 
            (current_time - self.last_status_print).total_seconds() >= 30):
            self.last_status_print = current_time
            state = self.portfolio_manager.get_state()
            self.logger.info(f"Status Update:\n  Portfolio Value: ${state.total_value:.2f}\n  Total P&L: ${state.total_pnl:.2f}\n  Signals Processed: {self.stats['signals_processed']}\n  Trades Executed: {self.stats['trades_executed']}\n  Errors: {self.stats['errors']}\n  Open Positions: {len(state.positions)}")
    
    def _print_final_stats(self):
        """Print final statistics when shutting down"""
        
        runtime = None
        if self.stats['start_time']:
            runtime = datetime.now() - self.stats['start_time']
        
        state = self.portfolio_manager.get_state()
        
        self.logger.info("=" * 50)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("=" * 50)
        self.logger.info(f"Runtime: {runtime}")
        self.logger.info(f"Signals Processed: {self.stats['signals_processed']}")
        self.logger.info(f"Trades Executed: {self.stats['trades_executed']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Final Portfolio Value: ${state.total_value:.2f}")
        self.logger.info(f"Total P&L: ${state.total_pnl:.2f}")
        self.logger.info(f"Win Rate: {state.win_rate:.1%}")
        self.logger.info(f"Trade Count: {state.trade_count}")
        
        # Add health and error information
        try:
            health_status = self.health_checker.get_health_summary()
            error_status = self.error_handler.get_health_status()
            
            self.logger.info(f"System Health: {health_status['overall_status']}")
            self.logger.info(f"Error Rate: {error_status['error_rate_per_minute']:.2f} errors/min")
            self.logger.info(f"Unresolved Errors: {error_status['unresolved_errors']}")
        except Exception as e:
            self.logger.error(f"Error getting health/error status: {e}")
        
        self.logger.info("=" * 50)
        
        # Generate final performance report
        self._generate_final_report()
    
    def _generate_final_report(self):
        """Generate final performance report"""
        try:
            if self.stats['trades_executed'] > 0:
                self.logger.info("Generating final performance report...")
                report_path = self.report_generator.generate_and_save_report(
                    self.portfolio_manager,
                    report_type="final_performance_report"
                )
                self.logger.info(f"Final report saved to: {report_path}")
            else:
                self.logger.info("No trades executed, skipping report generation")
        except Exception as e:
            self.logger.error(f"Error generating final report: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including health and error information"""
        # Get portfolio state
        portfolio_state = self.portfolio_manager.get_state()
        
        status = {
            "running": self.running,
            "stats": self.stats.copy(),
            "portfolio": {
                "total_value": portfolio_state.total_value,
                "total_pnl": portfolio_state.total_pnl,
                "cash": portfolio_state.cash,
                "positions_count": len(portfolio_state.positions)
            },
            "processed_files_count": len(self.processed_files)
        }
        
        if self.stats['start_time']:
            status["runtime_seconds"] = (datetime.now() - self.stats['start_time']).total_seconds()
        
        # Add health and error information
        try:
            status["health"] = self.health_checker.get_health_summary()
            status["errors"] = self.error_handler.get_health_status()
        except Exception as e:
            self.logger.error(f"Error getting health/error status: {e}")
            status["health"] = {"overall_status": "unknown"}
            status["errors"] = {"healthy": False, "error": str(e)}
        
        return status
    
    def generate_report(self, report_type: str = "performance_report", 
                       filename: Optional[str] = None) -> Optional[Path]:
        """
        Generate a performance report
        
        Args:
            report_type: Type of report to generate
            filename: Optional filename for the report
            
        Returns:
            Path to saved report file, or None if error
        """
        try:
            report_path = self.report_generator.generate_and_save_report(
                self.portfolio_manager,
                report_type=report_type,
                filename=filename
            )
            self.logger.info(f"Report generated: {report_path}")
            return report_path
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return None
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False  # Let main loop exit naturally instead of sys.exit(0)


def create_sample_signal_file(directory: str = "data/alerts"):
    """Create a sample signal file for testing"""
    
    import json
    from pathlib import Path
    
    signal_dir = Path(directory)
    signal_dir.mkdir(parents=True, exist_ok=True)
    
    sample_signal = {
        "asset": "BTC",
        "signal_type": "LONG",
        "price": 50000.0,
        "confidence": 0.8,
        "timestamp": datetime.now().isoformat(),
        "source": "test_signal"
    }
    
    file_path = signal_dir / f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(file_path, 'w') as f:
        json.dump(sample_signal, f, indent=2)
    
    print(f"Created sample signal file: {file_path}")
    return file_path 
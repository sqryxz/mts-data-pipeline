"""
MTS Signal Consumer - Monitors directory for MTS alert files
"""

import json
import os
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config.settings import Config
from src.core.models import TradingSignal
from src.signal_consumer.signal_processor import SignalProcessor
from src.signal_consumer.filters import SignalFilters
from src.utils.logger import get_logger

logger = get_logger('signal_consumer.mts')


class MTSAlertHandler(FileSystemEventHandler):
    """File system event handler for MTS alert files"""
    
    def __init__(self, consumer: 'MTSSignalConsumer'):
        self.consumer = consumer
        self.processed_files: Set[str] = set()
        self._lock = threading.Lock()  # Thread safety for processed_files
    
    def _wait_for_file_complete(self, file_path: str, max_wait: int = 5) -> bool:
        """Wait until file is completely written"""
        last_size = -1
        wait_time = 0
        while wait_time < max_wait:
            try:
                if not os.path.exists(file_path):
                    time.sleep(0.1)
                    wait_time += 0.1
                    continue
                    
                current_size = os.path.getsize(file_path)
                if current_size == last_size and current_size > 0:
                    return True  # File stable
                last_size = current_size
                time.sleep(0.1)
                wait_time += 0.1
            except OSError:
                time.sleep(0.1)
                wait_time += 0.1
        logger.warning(f"File {file_path} did not stabilize within {max_wait}s")
        return False
    
    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed (not already processed)"""
        with self._lock:
            if file_path in self.processed_files:
                return False
            # Additional checks could be added here (file age, size, etc.)
            return True
    
    def _mark_file_processed(self, file_path: str):
        """Mark file as processed (thread-safe)"""
        with self._lock:
            self.processed_files.add(file_path)
    
    def on_created(self, event):
        """Handle new file creation"""
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"New alert file detected: {event.src_path}")
            
            # Wait for file to be completely written
            if self._wait_for_file_complete(event.src_path):
                if self._should_process_file(event.src_path):
                    self.consumer.process_alert_file(event.src_path)
                    self._mark_file_processed(event.src_path)
                else:
                    logger.debug(f"File already processed: {event.src_path}")
            else:
                logger.warning(f"File not ready for processing: {event.src_path}")
    
    def on_modified(self, event):
        """Handle file modification (in case file is written slowly)"""
        if (not event.is_directory and 
            event.src_path.endswith('.json') and 
            self._should_process_file(event.src_path)):
            logger.debug(f"Alert file modified: {event.src_path}")
            
            # Wait for file to be completely written
            if self._wait_for_file_complete(event.src_path):
                self.consumer.process_alert_file(event.src_path)
                self._mark_file_processed(event.src_path)
            else:
                logger.warning(f"Modified file not ready for processing: {event.src_path}")


class MTSSignalConsumer:
    """Main MTS signal consumer that monitors alert directory"""
    
    def __init__(self, config: Config):
        self.config = config
        self.alert_path = Path(config.MTS_ALERT_PATH)
        self.processor = SignalProcessor()
        self.filters = SignalFilters()
        self.observer = None
        self.is_running = False
        self.processed_signals = []
        self._signals_lock = threading.Lock()  # Thread safety for processed_signals
        
        # Configuration for memory management
        self.max_signals_history = getattr(config, 'MAX_SIGNALS_HISTORY', 1000)
        self.max_file_size = getattr(config, 'MAX_FILE_SIZE', 1024 * 1024)  # 1MB default
        
        # Metrics tracking
        self.metrics = {
            'files_processed': 0,
            'files_failed': 0,
            'signals_created': 0,
            'start_time': time.time(),
            'last_activity': None
        }
        
        # Ensure alert directory exists
        self.alert_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"MTS Consumer initialized - monitoring: {self.alert_path}")
    
    def start_monitoring(self):
        """Start monitoring the MTS alert directory"""
        try:
            if self.is_running:
                logger.warning("Consumer already running")
                return
            
            # Process any existing files first
            self._process_existing_files()
            
            # Set up file system watcher
            self.observer = Observer()
            event_handler = MTSAlertHandler(self)
            self.observer.schedule(event_handler, str(self.alert_path), recursive=False)
            
            # Start monitoring
            self.observer.start()
            self.is_running = True
            
            logger.info(f"Started monitoring MTS alerts at: {self.alert_path}")
            
        except Exception as e:
            logger.error(f"Failed to start MTS consumer: {e}")
            self.is_running = False
    
    def stop_monitoring(self):
        """Stop monitoring the alert directory"""
        try:
            if self.observer and self.is_running:
                self.observer.stop()
                if not self.observer.join(timeout=5):
                    logger.warning("Observer thread did not stop within timeout")
                    # Force cleanup if needed
                self.observer = None
                self.is_running = False
                logger.info("Stopped MTS alert monitoring")
        except Exception as e:
            logger.error(f"Error stopping MTS consumer: {e}")
            self.is_running = False
    
    def process_alert_file(self, file_path: str) -> Optional[TradingSignal]:
        """
        Process a single MTS alert file
        
        Args:
            file_path: Path to the alert JSON file
            
        Returns:
            TradingSignal object if successfully processed, None otherwise
        """
        start_time = time.time()
        try:
            logger.debug(f"Processing alert file: {file_path}")
            
            # Check if file was already processed (thread-safe)
            with self._signals_lock:
                if file_path in getattr(self, '_processed_files', set()):
                    logger.debug(f"File already processed: {file_path}")
                    return None
            
            # Validate file path and size
            if not self._validate_file_path(file_path):
                return None
            
            # Read and parse JSON
            alert_data = self._read_alert_file(file_path)
            if not alert_data:
                self.metrics['files_failed'] += 1
                return None
            
            # Validate alert structure and content
            if not self.filters.validate_signal(alert_data):
                logger.warning(f"Alert validation failed: {file_path}")
                self.metrics['files_failed'] += 1
                return None
            
            # Check if signal should be processed
            if not self.filters.should_process_signal(alert_data):
                logger.debug(f"Signal filtered out: {file_path}")
                return None
            
            # Process alert into TradingSignal
            signal = self.processor.validate_and_process(alert_data)
            
            if signal:
                self._add_processed_signal(signal)
                # Mark file as processed
                if not hasattr(self, '_processed_files'):
                    self._processed_files = set()
                self._processed_files.add(file_path)
                
                self.metrics['files_processed'] += 1
                self.metrics['signals_created'] += 1
                self.metrics['last_activity'] = time.time()
                
                processing_time = time.time() - start_time
                logger.info(f"Successfully processed signal: {signal.asset} {signal.signal_type.value} in {processing_time:.3f}s")
                return signal
            else:
                logger.warning(f"Failed to convert alert to signal: {file_path}")
                self.metrics['files_failed'] += 1
                return None
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing alert file {file_path} after {processing_time:.3f}s: {e}")
            self.metrics['files_failed'] += 1
            return None
    
    def _read_alert_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read and parse JSON alert file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                logger.warning(f"Empty alert file: {file_path}")
                return None
            
            alert_data = json.loads(content)
            logger.debug(f"Parsed alert file: {file_path}")
            return alert_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in alert file {file_path}: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading alert file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading alert file {file_path}: {e}")
            return None
    
    def _process_existing_files(self):
        """Process any existing alert files in the directory"""
        try:
            json_files = list(self.alert_path.glob('*.json'))
            logger.info(f"Found {len(json_files)} existing alert files")
            
            for file_path in json_files:
                self.process_alert_file(str(file_path))
                
        except Exception as e:
            logger.error(f"Error processing existing files: {e}")
    
    def _add_processed_signal(self, signal: TradingSignal):
        """Add signal to processed list with memory management"""
        with self._signals_lock:
            self.processed_signals.append(signal)
            # Implement size limit to prevent memory leaks
            if len(self.processed_signals) > self.max_signals_history:
                # Keep only the most recent signals
                self.processed_signals = self.processed_signals[-self.max_signals_history:]
                logger.debug(f"Trimmed signal history to {self.max_signals_history} signals")
    
    def _validate_file_path(self, file_path: str) -> bool:
        """Validate file path and size"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"File too large ({file_size} bytes): {file_path}")
                return False
            
            # Basic path validation (prevent directory traversal)
            resolved_path = os.path.realpath(file_path)
            alert_dir = os.path.realpath(str(self.alert_path))
            if not resolved_path.startswith(alert_dir):
                logger.warning(f"File path outside alert directory: {file_path}")
                return False
            
            return True
            
        except OSError as e:
            logger.error(f"Error validating file path {file_path}: {e}")
            return False
    
    def get_processed_signals(self) -> list:
        """Get list of all processed signals (thread-safe)"""
        with self._signals_lock:
            return self.processed_signals.copy()
    
    def clear_processed_signals(self):
        """Clear the processed signals list (thread-safe)"""
        with self._signals_lock:
            self.processed_signals.clear()
            logger.debug("Cleared processed signals list")
    
    def get_status(self) -> Dict[str, Any]:
        """Get consumer status information"""
        try:
            with self._signals_lock:
                last_signal = None
                if self.processed_signals:
                    try:
                        last_signal = self.processed_signals[-1].timestamp.isoformat()
                    except (AttributeError, IndexError):
                        last_signal = None
                
                return {
                    'is_running': self.is_running,
                    'alert_path': str(self.alert_path),
                    'processed_count': len(self.processed_signals),
                    'last_signal': last_signal,
                    'metrics': self.metrics.copy()
                }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                'is_running': self.is_running,
                'alert_path': str(self.alert_path),
                'processed_count': 0,
                'last_signal': None,
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the consumer"""
        try:
            return {
                'status': 'healthy' if self.is_running else 'stopped',
                'observer_alive': self.observer.is_alive() if self.observer else False,
                'directory_accessible': self.alert_path.exists() and os.access(self.alert_path, os.R_OK),
                'last_activity': self.metrics.get('last_activity'),
                'uptime': time.time() - self.metrics['start_time'],
                'files_processed': self.metrics['files_processed'],
                'files_failed': self.metrics['files_failed'],
                'signals_created': self.metrics['signals_created']
            }
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
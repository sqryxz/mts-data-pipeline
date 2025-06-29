"""
Simple scheduler for automated data collection.

This module provides a basic scheduler that runs data collection
at regular intervals with graceful shutdown capabilities.
"""

import time
import threading
import signal
import logging
import json
import os
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

from src.services.collector import DataCollector
from src.utils.exceptions import CryptoDataPipelineError


class SimpleScheduler:
    """
    A simple scheduler that runs data collection at regular intervals.
    
    This scheduler uses time.sleep() for basic timing and supports
    graceful shutdown via signal handling or manual stop.
    
    The scheduler persists its state to avoid duplicate collections
    across restarts.
    """
    
    def __init__(self, 
                 collector: Optional[DataCollector] = None,
                 interval_seconds: int = 3600,  # Default: 1 hour
                 days_to_collect: int = 1,
                 state_file: Optional[str] = None):
        """
        Initialize the scheduler.
        
        Args:
            collector: DataCollector instance (creates default if None)
            interval_seconds: Time between collections in seconds (default: 3600 = 1 hour)
            days_to_collect: Number of days of data to collect each run (default: 1)
            state_file: Path to state persistence file (default: data/scheduler_state.json)
        """
        self.collector = collector if collector is not None else DataCollector()
        self.interval_seconds = interval_seconds
        self.days_to_collect = days_to_collect
        
        # State persistence
        self.state_file = state_file if state_file else os.path.join('data', 'scheduler_state.json')
        
        # Scheduler state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._last_collection_time: Optional[datetime] = None
        self._collection_count = 0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load previous state if available
        self._load_state()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.stop()
        
        # Register handlers for common termination signals
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination request
    
    def _run_collection(self) -> bool:
        """
        Run a single data collection cycle.
        
        Returns:
            bool: True if collection was successful, False otherwise
        """
        collection_start_time = datetime.now()
        
        try:
            self.logger.info("=" * 60)
            self.logger.info(f"SCHEDULED COLLECTION #{self._collection_count + 1}")
            self.logger.info(f"Interval: {self.interval_seconds}s, Days: {self.days_to_collect}")
            self.logger.info("=" * 60)
            
            # Run the collection
            results = self.collector.collect_all_data(days=self.days_to_collect)
            
            # Log results
            self.logger.info("=" * 60)
            self.logger.info("SCHEDULED COLLECTION SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"Total attempted: {results['total_attempted']}")
            self.logger.info(f"Successful: {results['successful']}")
            self.logger.info(f"Failed: {results['failed']}")
            self.logger.info(f"Duration: {results['duration_seconds']:.2f}s")
            
            if results['successful_cryptos']:
                self.logger.info(f"✅ Successfully collected: {', '.join(results['successful_cryptos'])}")
            
            if results['failed_cryptos']:
                self.logger.warning(f"❌ Failed to collect: {', '.join(results['failed_cryptos'])}")
            
            # Update state
            self._last_collection_time = collection_start_time
            self._collection_count += 1
            
            # Save state for persistence
            self._save_state()
            
            success = results['successful'] > 0
            if success:
                self.logger.info("✅ Scheduled collection completed successfully")
            else:
                self.logger.error("❌ Scheduled collection failed - no data collected")
            
            self.logger.info("=" * 60)
            return success
            
        except CryptoDataPipelineError as e:
            self.logger.error(f"Pipeline error during scheduled collection: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during scheduled collection: {e}")
            return False
    
    def _scheduler_loop(self):
        """
        Main scheduler loop that runs collections at intervals.
        
        This method runs in a separate thread and handles timing,
        collection execution, and shutdown events.
        """
        self.logger.info("Scheduler loop started")
        
        try:
            while not self._shutdown_event.is_set():
                # Check if we should skip this collection (too recent)
                if self._should_skip_collection():
                    # Calculate how long to wait until next collection is due
                    time_since_last = datetime.now() - self._last_collection_time
                    wait_time = self.interval_seconds - time_since_last.total_seconds()
                    wait_time = max(wait_time, 0)  # Ensure non-negative
                    
                    self.logger.info(f"Waiting {wait_time:.1f}s until next collection is due")
                    
                    # Wait for the remaining time or shutdown
                    if self._shutdown_event.wait(timeout=wait_time):
                        break
                    
                    # Continue to next iteration to check again
                    continue
                
                # Run collection
                collection_success = self._run_collection()
                
                if not collection_success:
                    self.logger.warning("Collection failed, but scheduler will continue")
                
                # Wait for next collection or shutdown
                self.logger.info(f"Next collection in {self.interval_seconds} seconds")
                
                # Use event.wait() instead of time.sleep() for interruptible waiting
                if self._shutdown_event.wait(timeout=self.interval_seconds):
                    # Shutdown event was set during wait
                    break
                    
        except Exception as e:
            self.logger.error(f"Fatal error in scheduler loop: {e}")
        finally:
            self.logger.info("Scheduler loop ended")
    
    def start(self) -> bool:
        """
        Start the scheduler.
        
        Returns:
            bool: True if scheduler started successfully, False if already running
        """
        if self._running:
            self.logger.warning("Scheduler is already running")
            return False
        
        self.logger.info("Starting scheduler...")
        self.logger.info(f"Collection interval: {self.interval_seconds} seconds")
        self.logger.info(f"Days per collection: {self.days_to_collect}")
        
        # Reset state
        self._running = True
        self._shutdown_event.clear()
        self._collection_count = 0
        
        # Start scheduler thread
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        
        self.logger.info("✅ Scheduler started successfully")
        return True
    
    def stop(self, timeout_seconds: int = 30) -> bool:
        """
        Stop the scheduler gracefully.
        
        Args:
            timeout_seconds: Maximum time to wait for scheduler to stop
            
        Returns:
            bool: True if stopped successfully, False if timeout occurred
        """
        if not self._running:
            self.logger.info("Scheduler is not running")
            return True
        
        self.logger.info("Stopping scheduler...")
        
        # Signal shutdown
        self._running = False
        self._shutdown_event.set()
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout_seconds)
            
            if self._thread.is_alive():
                self.logger.error(f"Scheduler thread did not stop within {timeout_seconds} seconds")
                return False
        
        self.logger.info("✅ Scheduler stopped successfully")
        return True
    
    def is_running(self) -> bool:
        """
        Check if the scheduler is currently running.
        
        Returns:
            bool: True if scheduler is running, False otherwise
        """
        return self._running and self._thread is not None and self._thread.is_alive()
    
    def get_status(self) -> dict[str, Any]:
        """
        Get the current status of the scheduler.
        
        Returns:
            dict: Scheduler status information
        """
        return {
            'running': self.is_running(),
            'interval_seconds': self.interval_seconds,
            'days_to_collect': self.days_to_collect,
            'collection_count': self._collection_count,
            'last_collection_time': self._last_collection_time.isoformat() if self._last_collection_time else None,
            'next_collection_time': (
                (self._last_collection_time + timedelta(seconds=self.interval_seconds)).isoformat()
                if self._last_collection_time else None
            )
        }
    
    def run_once(self) -> bool:
        """
        Run a single collection immediately (for testing or manual triggers).
        
        Returns:
            bool: True if collection was successful, False otherwise
        """
        if self._running:
            self.logger.warning("Cannot run manual collection while scheduler is running")
            return False
        
        self.logger.info("Running manual collection via scheduler")
        return self._run_collection()
    
    def wait_for_completion(self, timeout_seconds: Optional[int] = None):
        """
        Wait for the scheduler thread to complete (mainly for testing).
        
        Args:
            timeout_seconds: Maximum time to wait (None = wait indefinitely)
        """
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout_seconds)
    
    def _save_state(self):
        """Save scheduler state to file for persistence across restarts."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            state = {
                'last_collection_time': self._last_collection_time.isoformat() if self._last_collection_time else None,
                'collection_count': self._collection_count,
                'interval_seconds': self.interval_seconds,
                'days_to_collect': self.days_to_collect
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
            self.logger.debug(f"Scheduler state saved to {self.state_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save scheduler state: {e}")
    
    def _load_state(self):
        """Load scheduler state from file if available."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                # Load last collection time
                if state.get('last_collection_time'):
                    self._last_collection_time = datetime.fromisoformat(state['last_collection_time'])
                    self.logger.info(f"Loaded previous collection time: {self._last_collection_time}")
                
                # Note: collection_count is not loaded from state - it resets per session
                
                self.logger.debug(f"Scheduler state loaded from {self.state_file}")
            else:
                self.logger.debug(f"No previous state file found at {self.state_file}")
                
        except Exception as e:
            self.logger.warning(f"Failed to load scheduler state: {e}")
            # Continue with default state
    
    def _should_skip_collection(self) -> bool:
        """
        Check if collection should be skipped based on last collection time.
        
        Returns:
            bool: True if collection should be skipped (too recent), False otherwise
        """
        if self._last_collection_time is None:
            return False
        
        time_since_last = datetime.now() - self._last_collection_time
        time_until_next = timedelta(seconds=self.interval_seconds) - time_since_last
        
        if time_until_next.total_seconds() > 0:
            self.logger.info(f"Skipping collection - last run was {time_since_last.total_seconds():.1f}s ago")
            self.logger.info(f"Next collection due in {time_until_next.total_seconds():.1f}s")
            return True
        
        return False 
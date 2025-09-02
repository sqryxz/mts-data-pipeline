"""
Multi-Tier Scheduler for Optimized Data Collection

This scheduler handles different collection intervals for different asset types:
- BTC, ETH: 15-minute intervals  
- Other cryptos: Daily intervals
- Macro indicators: Daily intervals

Optimizes API calls while maintaining data freshness requirements.
"""

import asyncio
import logging
import threading
import time
import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.services.collector import DataCollector
from src.services.macro_collector import MacroDataCollector
from src.api.binance_client import BinanceClient
from src.utils.exceptions import CryptoDataPipelineError


class AssetTier(Enum):
    """Asset collection tiers with different priorities and intervals"""
    HIGH_FREQUENCY = "high_frequency"    # BTC, ETH - 15 minutes
    HOURLY = "hourly"                    # Other cryptos - 60 minutes
    MACRO = "macro"                      # Macro indicators - daily


@dataclass
class CollectionTask:
    """Represents a scheduled collection task"""
    asset_id: str
    tier: AssetTier
    interval_seconds: int
    last_collection: Optional[datetime] = None
    consecutive_failures: int = 0
    enabled: bool = True


class MultiTierScheduler:
    """
    Advanced scheduler with multiple collection tiers for optimal API usage.
    
    Features:
    - Different intervals for different asset types
    - API call optimization and batching
    - Failure recovery and exponential backoff
    - Real-time monitoring and health checks
    - State persistence across restarts
    """
    
    def __init__(self,
                 high_frequency_assets: List[str] = None,
                 daily_assets: List[str] = None,
                 macro_indicators: List[str] = None,
                 state_file: str = "data/multi_tier_scheduler_state.json"):
        
        # Default asset configuration optimized for minimal API calls
        self.high_frequency_assets = high_frequency_assets or [
            'bitcoin', 'ethereum', 'binancecoin', 'hyperliquid', 'solana', 
            'ripple', 'dogecoin', 'chainlink', 'sui', 'uniswap'
        ]
        self.hourly_assets = daily_assets or [
            'tether', 'bittensor', 'fetch-ai', 'singularitynet', 
            'render-token', 'ocean-protocol', 'ethena'
        ]
        self.macro_indicators = macro_indicators or [
            'VIXCLS', 'DFF', 'DGS10', 'DTWEXBGS', 'DEXUSEU', 
            'DEXCHUS', 'BAMLH0A0HYM2', 'RRPONTSYD', 'SOFR'
        ]
        
        # Collection intervals (optimized for API limits)
        self.intervals = {
            AssetTier.HIGH_FREQUENCY: 15 * 60,    # 15 minutes
            AssetTier.HOURLY: 60 * 60,             # 60 minutes
            AssetTier.MACRO: 24 * 60 * 60,         # 24 hours
        }
        
        # Initialize collectors
        self.crypto_collector = DataCollector()
        self.macro_collector = MacroDataCollector()
        self.binance_client = BinanceClient()
        
        # State management
        self.state_file = state_file
        self.tasks: Dict[str, CollectionTask] = {}
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Performance tracking
        self.total_api_calls = 0
        self.api_calls_by_hour = {}
        self.collection_stats = {
            'high_frequency': {'success': 0, 'failure': 0},
            'hourly': {'success': 0, 'failure': 0},
            'macro': {'success': 0, 'failure': 0}
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize tasks
        self._initialize_tasks()
        self._load_state()
        
        self.logger.info(f"MultiTierScheduler initialized with {len(self.tasks)} tasks")
        self.logger.info(f"High frequency assets: {self.high_frequency_assets}")
        self.logger.info(f"Hourly assets: {self.hourly_assets}")
        self.logger.info(f"Macro indicators: {len(self.macro_indicators)} indicators")
    
    def _initialize_tasks(self):
        """Initialize collection tasks for all assets"""
        
        # High frequency assets (BTC, ETH)
        for asset in self.high_frequency_assets:
            task_id = f"crypto_{asset}"
            self.tasks[task_id] = CollectionTask(
                asset_id=asset,
                tier=AssetTier.HIGH_FREQUENCY,
                interval_seconds=self.intervals[AssetTier.HIGH_FREQUENCY]
            )
        
        # Hourly crypto assets  
        for asset in self.hourly_assets:
            task_id = f"crypto_{asset}"
            self.tasks[task_id] = CollectionTask(
                asset_id=asset,
                tier=AssetTier.HOURLY,
                interval_seconds=self.intervals[AssetTier.HOURLY]
            )
        
        # Macro indicators
        for indicator in self.macro_indicators:
            task_id = f"macro_{indicator}"
            self.tasks[task_id] = CollectionTask(
                asset_id=indicator,
                tier=AssetTier.MACRO,
                interval_seconds=self.intervals[AssetTier.MACRO]
            )
    
    def _load_state(self):
        """Load previous scheduler state from disk"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                # Restore last collection times
                for task_id, task_state in state_data.get('tasks', {}).items():
                    if task_id in self.tasks:
                        if task_state.get('last_collection'):
                            self.tasks[task_id].last_collection = datetime.fromisoformat(
                                task_state['last_collection']
                            )
                        self.tasks[task_id].consecutive_failures = task_state.get('consecutive_failures', 0)
                        self.tasks[task_id].enabled = task_state.get('enabled', True)
                
                # Restore stats
                if 'collection_stats' in state_data:
                    self.collection_stats.update(state_data['collection_stats'])
                
                self.logger.info(f"Loaded scheduler state from {self.state_file}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load scheduler state: {e}")
    
    def _save_state(self):
        """Save current scheduler state to disk"""
        try:
            # Prepare state data
            state_data = {
                'tasks': {},
                'collection_stats': self.collection_stats,
                'total_api_calls': self.total_api_calls,
                'last_save': datetime.now().isoformat()
            }
            
            # Save task states
            for task_id, task in self.tasks.items():
                state_data['tasks'][task_id] = {
                    'last_collection': task.last_collection.isoformat() if task.last_collection else None,
                    'consecutive_failures': task.consecutive_failures,
                    'enabled': task.enabled
                }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # Write state file
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save scheduler state: {e}")
    
    def start(self) -> bool:
        """Start the multi-tier scheduler"""
        if self._running:
            self.logger.warning("Scheduler is already running")
            return True
        
        try:
            self.logger.info("Starting Multi-Tier Scheduler")
            self.logger.info("=" * 60)
            
            # Log collection strategy
            hf_count = len([t for t in self.tasks.values() if t.tier == AssetTier.HIGH_FREQUENCY])
            hourly_count = len([t for t in self.tasks.values() if t.tier == AssetTier.HOURLY])
            macro_count = len([t for t in self.tasks.values() if t.tier == AssetTier.MACRO])
            
            self.logger.info(f"📊 Collection Strategy:")
            self.logger.info(f"  🚀 High Frequency (15min): {hf_count} assets")
            self.logger.info(f"  ⏰ Hourly: {hourly_count} crypto assets")
            self.logger.info(f"  📈 Daily Macro: {macro_count} indicators")
            
            # Calculate expected API usage
            daily_api_calls = self._calculate_daily_api_usage()
            self.logger.info(f"  📡 Estimated daily API calls: {daily_api_calls}")
            
            self._running = True
            self._shutdown_event.clear()
            
            # Start scheduler thread
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="MultiTierScheduler",
                daemon=True
            )
            self._scheduler_thread.start()
            
            self.logger.info("✅ Multi-Tier Scheduler started successfully")
            self.logger.info("   Press Ctrl+C to stop")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            self._running = False
            return False
    
    def stop(self):
        """Stop the scheduler gracefully"""
        if not self._running:
            return
        
        self.logger.info("Stopping Multi-Tier Scheduler...")
        
        # Signal shutdown
        self._running = False
        self._shutdown_event.set()
        
        # Wait for scheduler thread to finish
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=10)
        
        # Save final state
        self._save_state()
        
        self.logger.info("✅ Multi-Tier Scheduler stopped")
    
    def _calculate_daily_api_usage(self) -> int:
        """Calculate expected daily API call usage"""
        calls_per_day = 0
        
        # High frequency assets (every 15 minutes = 96 times per day)
        hf_assets = len([t for t in self.tasks.values() if t.tier == AssetTier.HIGH_FREQUENCY])
        calls_per_day += hf_assets * 96
        
        # Hourly assets (every 60 minutes = 24 times per day)
        hourly_assets = len([t for t in self.tasks.values() if t.tier == AssetTier.HOURLY])
        calls_per_day += hourly_assets * 24
        
        # Macro indicators (once per day)
        macro_indicators = len([t for t in self.tasks.values() if t.tier == AssetTier.MACRO])
        calls_per_day += macro_indicators * 1
        
        return calls_per_day
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        self.logger.info("Scheduler loop started")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                current_time = datetime.now()
                
                # Check which tasks are due for collection
                due_tasks = self._get_due_tasks(current_time)
                
                if due_tasks:
                    self.logger.info(f"Found {len(due_tasks)} tasks due for collection")
                    
                    # Group tasks by tier for batch processing
                    tasks_by_tier = self._group_tasks_by_tier(due_tasks)
                    
                    # Process each tier
                    for tier, tier_tasks in tasks_by_tier.items():
                        if tier_tasks:
                            self._process_tier_tasks(tier, tier_tasks, current_time)
                
                # Save state periodically
                self._save_state()
                
                # Wait before next check (check every minute)
                if not self._shutdown_event.wait(timeout=60):
                    continue
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        self.logger.info("Scheduler loop ended")
    
    def _get_due_tasks(self, current_time: datetime) -> List[CollectionTask]:
        """Get tasks that are due for collection"""
        due_tasks = []
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            # Check if task is due
            if task.last_collection is None:
                # First run
                due_tasks.append(task)
            else:
                time_since_last = (current_time - task.last_collection).total_seconds()
                if time_since_last >= task.interval_seconds:
                    due_tasks.append(task)
        
        return due_tasks
    
    def _group_tasks_by_tier(self, tasks: List[CollectionTask]) -> Dict[AssetTier, List[CollectionTask]]:
        """Group tasks by their collection tier"""
        grouped = {tier: [] for tier in AssetTier}
        
        for task in tasks:
            grouped[task.tier].append(task)
        
        return grouped
    
    def _process_tier_tasks(self, tier: AssetTier, tasks: List[CollectionTask], current_time: datetime):
        """Process all tasks for a specific tier"""
        self.logger.info(f"Processing {len(tasks)} {tier.value} tasks")
        
        success_count = 0
        failure_count = 0
        
        for task in tasks:
            try:
                success = self._execute_collection_task(task, current_time)
                
                if success:
                    success_count += 1
                    task.consecutive_failures = 0
                    self.collection_stats[tier.value]['success'] += 1
                else:
                    failure_count += 1
                    task.consecutive_failures += 1
                    self.collection_stats[tier.value]['failure'] += 1
                
                # Update last collection time
                task.last_collection = current_time
                
                # Disable task if too many consecutive failures
                if task.consecutive_failures >= 3:
                    task.enabled = False
                    self.logger.warning(f"Disabled task {task.asset_id} after 3 consecutive failures")
                
            except Exception as e:
                self.logger.error(f"Failed to execute task {task.asset_id}: {e}")
                failure_count += 1
                task.consecutive_failures += 1
        
        # Log tier results
        self.logger.info(f"✅ {tier.value}: {success_count} successful, {failure_count} failed")
    
    def _execute_collection_task(self, task: CollectionTask, current_time: datetime) -> bool:
        """Execute a single collection task"""
        
        try:
            if task.tier in [AssetTier.HIGH_FREQUENCY, AssetTier.HOURLY]:
                # Crypto asset collection
                result = self.crypto_collector.collect_crypto_data(task.asset_id, days=1)
                self.total_api_calls += 1
                
                success = result.get('success', False)
                if success:
                    self.logger.debug(f"✅ Collected {task.asset_id} ({task.tier.value})")
                else:
                    self.logger.warning(f"❌ Failed to collect {task.asset_id}: {result.get('error', 'Unknown error')}")
                
                return success
                
            elif task.tier == AssetTier.MACRO:
                # Macro indicator collection
                records = self.macro_collector.collect_indicator(task.asset_id, days=1)
                self.total_api_calls += 1
                
                success = len(records) > 0
                if success:
                    self.logger.debug(f"✅ Collected macro {task.asset_id}")
                else:
                    self.logger.warning(f"❌ Failed to collect macro {task.asset_id}")
                
                return success
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error executing task {task.asset_id}: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        current_time = datetime.now()
        
        # Calculate task statuses
        task_status = {}
        for task_id, task in self.tasks.items():
            next_collection = None
            if task.last_collection:
                next_collection = task.last_collection + timedelta(seconds=task.interval_seconds)
            
            task_status[task_id] = {
                'tier': task.tier.value,
                'enabled': task.enabled,
                'last_collection': task.last_collection.isoformat() if task.last_collection else None,
                'next_collection': next_collection.isoformat() if next_collection else None,
                'consecutive_failures': task.consecutive_failures,
                'overdue': next_collection < current_time if next_collection else False
            }
        
        return {
            'running': self._running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': len([t for t in self.tasks.values() if t.enabled]),
            'total_api_calls': self.total_api_calls,
            'collection_stats': self.collection_stats,
            'expected_daily_calls': self._calculate_daily_api_usage(),
            'task_status': task_status,
            'last_updated': current_time.isoformat()
        }
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running 
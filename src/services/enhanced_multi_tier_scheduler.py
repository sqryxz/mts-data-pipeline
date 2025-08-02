"""
Enhanced Multi-Tier Scheduler with Signal Generation

This enhanced scheduler handles:
- Data collection at different intervals (15min for BTC/ETH, hourly for others, daily for macro)
- Automatic signal generation after data collection
- JSON alert generation for high-confidence signals
- Complete end-to-end pipeline operation
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
from src.services.multi_strategy_generator import MultiStrategyGenerator, create_default_multi_strategy_generator
from src.utils.json_alert_system import JSONAlertSystem
from src.utils.discord_webhook import DiscordAlertManager
from src.api.binance_client import BinanceClient
from src.utils.exceptions import CryptoDataPipelineError
from config.settings import Config


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
    last_signal_generation: Optional[datetime] = None
    consecutive_failures: int = 0
    enabled: bool = True


class EnhancedMultiTierScheduler:
    """
    Enhanced scheduler with data collection AND signal generation.
    
    Features:
    - Multi-tier data collection (15min, hourly, daily)
    - Automatic signal generation after data updates
    - JSON alert generation for high-confidence signals
    - API call optimization and batching
    - Failure recovery and exponential backoff
    - Real-time monitoring and health checks
    - State persistence across restarts
    """
    
    def __init__(self,
                 high_frequency_assets: List[str] = None,
                 hourly_assets: List[str] = None,
                 macro_indicators: List[str] = None,
                 enable_signal_generation: bool = True,
                 enable_alert_generation: bool = True,
                 enable_discord_alerts: bool = True,
                 signal_generation_interval: int = 3600,  # Generate signals every hour
                 macro_collection_time: str = "23:00",  # 11 PM - time for macro data collection
                 state_file: str = "data/enhanced_multi_tier_scheduler_state.json"):
        
        # Asset configuration
        self.high_frequency_assets = high_frequency_assets or ['bitcoin', 'ethereum']
        self.hourly_assets = hourly_assets or [
            'tether', 'solana', 'ripple', 'bittensor', 'fetch-ai', 
            'singularitynet', 'render-token', 'ocean-protocol'
        ]
        self.macro_indicators = macro_indicators or [
            'VIXCLS', 'DFF', 'DGS10', 'DTWEXBGS', 'DEXUSEU', 
            'DEXCHUS', 'BAMLH0A0HYM2', 'RRPONTSYD', 'SOFR'
        ]
        
        # Feature flags
        self.enable_signal_generation = enable_signal_generation
        self.enable_alert_generation = enable_alert_generation
        self.enable_discord_alerts = enable_discord_alerts
        self.signal_generation_interval = signal_generation_interval
        self.macro_collection_time = macro_collection_time  # Time for macro collection (HH:MM format)
        
        # Collection intervals
        self.intervals = {
            AssetTier.HIGH_FREQUENCY: 15 * 60,    # 15 minutes
            AssetTier.HOURLY: 60 * 60,             # 60 minutes
            AssetTier.MACRO: 24 * 60 * 60,         # 24 hours (but will use time-based scheduling)
        }
        
        # Initialize collectors
        self.crypto_collector = DataCollector()
        self.macro_collector = MacroDataCollector()
        self.binance_client = BinanceClient()
        
        # Initialize signal generation components (if enabled)
        self.signal_generator = None
        self.alert_system = None
        self.discord_manager = None
        
        # Setup logging first for component initialization
        self.logger = logging.getLogger(__name__)
        
        if self.enable_signal_generation:
            try:
                self.signal_generator = create_default_multi_strategy_generator()
                self.logger.info("✅ Signal generation enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize signal generator: {e}")
                self.enable_signal_generation = False
        
        if self.enable_alert_generation:
            try:
                self.alert_system = JSONAlertSystem()
                self.logger.info("✅ Alert generation enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize alert system: {e}")
                self.enable_alert_generation = False
        
        if self.enable_discord_alerts:
            try:
                config = Config()
                if config.DISCORD_WEBHOOK_URL:
                    discord_config = {
                        'min_confidence': config.DISCORD_MIN_CONFIDENCE,
                        'min_strength': config.DISCORD_MIN_STRENGTH,
                        'enabled_assets': ['bitcoin', 'ethereum'],
                        'rate_limit': config.DISCORD_RATE_LIMIT_SECONDS,
                        'batch_alerts': True
                    }
                    self.discord_manager = DiscordAlertManager(
                        config.DISCORD_WEBHOOK_URL, 
                        discord_config
                    )
                    self.logger.info("✅ Discord alerts enabled")
                else:
                    self.logger.warning("Discord alerts requested but DISCORD_WEBHOOK_URL not set in .env")
                    self.enable_discord_alerts = False
            except Exception as e:
                self.logger.warning(f"Failed to initialize Discord alerts: {e}")
                self.enable_discord_alerts = False
        
        # State management
        self.state_file = state_file
        self.tasks: Dict[str, CollectionTask] = {}
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Performance tracking
        self.total_api_calls = 0
        self.signals_generated = 0
        self.alerts_generated = 0
        self.discord_alerts_sent = 0
        self.api_calls_by_hour = {}
        self.collection_stats = {
            'high_frequency': {'success': 0, 'failure': 0},
            'hourly': {'success': 0, 'failure': 0},
            'macro': {'success': 0, 'failure': 0}
        }
        
        # Initialize tasks
        self._initialize_tasks()
        self._load_state()
        
        self.logger.info(f"EnhancedMultiTierScheduler initialized with {len(self.tasks)} tasks")
        self.logger.info(f"High frequency assets: {self.high_frequency_assets}")
        self.logger.info(f"Hourly assets: {self.hourly_assets}")
        self.logger.info(f"Macro indicators: {len(self.macro_indicators)} indicators")
        self.logger.info(f"Macro collection time: {self.macro_collection_time} (daily)")
        self.logger.info(f"Signal generation: {'✅ Enabled' if self.enable_signal_generation else '❌ Disabled'}")
        self.logger.info(f"Alert generation: {'✅ Enabled' if self.enable_alert_generation else '❌ Disabled'}")
        self.logger.info(f"Discord alerts: {'✅ Enabled' if self.enable_discord_alerts else '❌ Disabled'}")
    
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
                        if task_state.get('last_signal_generation'):
                            self.tasks[task_id].last_signal_generation = datetime.fromisoformat(
                                task_state['last_signal_generation']
                            )
                        self.tasks[task_id].consecutive_failures = task_state.get('consecutive_failures', 0)
                        self.tasks[task_id].enabled = task_state.get('enabled', True)
                
                # Restore stats
                if 'collection_stats' in state_data:
                    self.collection_stats.update(state_data['collection_stats'])
                
                if 'signals_generated' in state_data:
                    self.signals_generated = state_data['signals_generated']
                
                if 'alerts_generated' in state_data:
                    self.alerts_generated = state_data['alerts_generated']
                
                if 'discord_alerts_sent' in state_data:
                    self.discord_alerts_sent = state_data['discord_alerts_sent']
                
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
                'signals_generated': self.signals_generated,
                'alerts_generated': self.alerts_generated,
                'discord_alerts_sent': self.discord_alerts_sent,
                'last_save': datetime.now().isoformat()
            }
            
            # Save task states
            for task_id, task in self.tasks.items():
                state_data['tasks'][task_id] = {
                    'last_collection': task.last_collection.isoformat() if task.last_collection else None,
                    'last_signal_generation': task.last_signal_generation.isoformat() if task.last_signal_generation else None,
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
        """Start the enhanced multi-tier scheduler"""
        if self._running:
            self.logger.warning("Scheduler is already running")
            return True
        
        try:
            self.logger.info("Starting Enhanced Multi-Tier Scheduler with Signal Generation")
            self.logger.info("=" * 70)
            
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
            
            # Log signal generation features
            if self.enable_signal_generation:
                self.logger.info(f"  🎯 Signal Generation: Every {self.signal_generation_interval//60} minutes")
            if self.enable_alert_generation:
                self.logger.info(f"  🚨 Alert Generation: Enabled for high-confidence signals")
            if self.enable_discord_alerts:
                self.logger.info(f"  📢 Discord Alerts: Enabled via webhook")
            
            self._running = True
            self._shutdown_event.clear()
            
            # Start scheduler thread
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="EnhancedMultiTierScheduler",
                daemon=True
            )
            self._scheduler_thread.start()
            
            self.logger.info("✅ Enhanced Multi-Tier Scheduler started successfully")
            self.logger.info("   Press Ctrl+C to stop")
            self.logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start enhanced scheduler: {e}")
            self._running = False
            return False
    
    def stop(self):
        """Stop the scheduler gracefully"""
        if not self._running:
            return
        
        self.logger.info("Stopping Enhanced Multi-Tier Scheduler...")
        
        # Signal shutdown
        self._running = False
        self._shutdown_event.set()
        
        # Wait for scheduler thread to finish
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=10)
        
        # Save final state
        self._save_state()
        
        self.logger.info("✅ Enhanced Multi-Tier Scheduler stopped")
    
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
        """Main scheduler loop with signal generation"""
        self.logger.info("Enhanced scheduler loop started")
        
        last_signal_generation = None
        
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
                
                # Check if signal generation is due
                if self.enable_signal_generation and self._is_signal_generation_due(current_time, last_signal_generation):
                    self.logger.info("⚡ Running signal generation...")
                    try:
                        signals = self._generate_signals()
                        self.signals_generated += len(signals)
                        
                        if signals and self.enable_alert_generation:
                            alerts = self._generate_alerts(signals)
                            self.alerts_generated += len(alerts)
                            
                            # Send Discord alerts if enabled
                            discord_count = 0
                            if self.enable_discord_alerts and self.discord_manager and signals:
                                discord_count = self._send_discord_alerts_sync(signals)
                                self.discord_alerts_sent += discord_count
                            
                            self.logger.info(f"🚨 Generated {len(alerts)} alerts from {len(signals)} signals" + 
                                           (f", sent {discord_count} Discord alerts" if discord_count > 0 else ""))
                        
                        last_signal_generation = current_time
                        
                    except Exception as e:
                        self.logger.error(f"Signal generation failed: {e}")
                
                # Save state periodically
                self._save_state()
                
                # Wait before next check (check every minute)
                if not self._shutdown_event.wait(timeout=60):
                    continue
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in enhanced scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        self.logger.info("Enhanced scheduler loop ended")
    
    def _is_signal_generation_due(self, current_time: datetime, last_generation: Optional[datetime]) -> bool:
        """Check if signal generation is due"""
        if last_generation is None:
            return True
        
        time_since_last = (current_time - last_generation).total_seconds()
        return time_since_last >= self.signal_generation_interval
    
    def _generate_signals(self) -> List:
        """Generate trading signals using the multi-strategy generator"""
        if not self.signal_generator:
            return []
        
        try:
            signals = self.signal_generator.generate_aggregated_signals(days=30)
            self.logger.info(f"✅ Generated {len(signals)} trading signals")
            return signals
        except Exception as e:
            self.logger.error(f"Failed to generate signals: {e}")
            return []
    
    def _generate_alerts(self, signals: List) -> List:
        """Generate JSON alerts from high-confidence signals"""
        if not self.alert_system or not signals:
            return []
        
        try:
            alerts = self.alert_system.generate_alerts_from_signals(signals)
            
            if alerts:
                # Save alerts to files
                saved_files = self.alert_system.save_bulk_alerts(alerts)
                self.logger.info(f"💾 Saved {len(saved_files)} alert files")
            
            return alerts
        except Exception as e:
            self.logger.error(f"Failed to generate alerts: {e}")
            return []
    
    def _send_discord_alerts_sync(self, signals: List) -> int:
        """Send Discord alerts synchronously using asyncio"""
        if not self.discord_manager or not signals:
            return 0
        
        try:
            # Create new event loop for async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Process signals and send to Discord
                result = loop.run_until_complete(
                    self.discord_manager.process_signals(signals)
                )
                return result.get('sent', 0)
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Failed to send Discord alerts: {e}")
            return 0
    
    def _is_macro_collection_due_today(self, task: CollectionTask, current_time: datetime) -> bool:
        """Check if macro data should be collected today at the scheduled time"""
        if task.last_collection is None:
            # First run, check if it's past the scheduled time today
            scheduled_time = datetime.strptime(self.macro_collection_time, "%H:%M").time()
            return current_time.time() >= scheduled_time
        
        # Check if we already collected today at the scheduled time
        scheduled_time = datetime.strptime(self.macro_collection_time, "%H:%M").time()
        last_collection_time = task.last_collection.time()
        
        # If last collection was today and at or after scheduled time, we're done for today
        if (task.last_collection.date() == current_time.date() and 
            last_collection_time >= scheduled_time):
            return False
        
        # If it's past the scheduled time today and we haven't collected yet, collect now
        return current_time.time() >= scheduled_time

    def _get_due_tasks(self, current_time: datetime) -> List[CollectionTask]:
        """Get tasks that are due for collection"""
        due_tasks = []
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            # Check if task is due
            if task.tier == AssetTier.MACRO:
                # Macro tasks are time-based, check if it's the scheduled time
                if self._is_macro_collection_due_today(task, current_time):
                    due_tasks.append(task)
            else:
                # Standard interval-based tasks
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
        """Get current enhanced scheduler status"""
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
                'last_signal_generation': task.last_signal_generation.isoformat() if task.last_signal_generation else None,
                'next_collection': next_collection.isoformat() if next_collection else None,
                'consecutive_failures': task.consecutive_failures,
                'overdue': next_collection < current_time if next_collection else False
            }
        
        return {
            'running': self._running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': len([t for t in self.tasks.values() if t.enabled]),
            'total_api_calls': self.total_api_calls,
            'signals_generated': self.signals_generated,
            'alerts_generated': self.alerts_generated,
            'discord_alerts_sent': self.discord_alerts_sent,
            'signal_generation_enabled': self.enable_signal_generation,
            'alert_generation_enabled': self.enable_alert_generation,
            'discord_alerts_enabled': self.enable_discord_alerts,
            'collection_stats': self.collection_stats,
            'expected_daily_calls': self._calculate_daily_api_usage(),
            'task_status': task_status,
            'last_updated': current_time.isoformat()
        }
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running 
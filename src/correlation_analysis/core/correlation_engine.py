"""
Main correlation engine for correlation analysis module.
Orchestrates monitoring for all configured pairs.
"""

import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .correlation_monitor import CorrelationMonitor
from ..storage.state_manager import CorrelationStateManager
from ..storage.correlation_storage import CorrelationStorage


class CorrelationEngine:
    """
    Main correlation engine that orchestrates monitoring for all configured pairs.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the correlation engine.
        
        Args:
            config_path: Path to configuration file (defaults to monitored_pairs.json)
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config_path = config_path or "config/correlation_analysis/monitored_pairs.json"
        self.config = self._load_config()
        
        # Initialize components
        self.state_manager = CorrelationStateManager()
        self.storage = CorrelationStorage()
        
        # Track monitoring state
        self.monitors: Dict[str, CorrelationMonitor] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        self.last_mosaic_generation = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_monitoring_time': 0.0,
            'avg_monitoring_time': 0.0,
            'last_run_time': None,
            'last_successful_run': None
        }
        
        self.logger.info(f"Correlation engine initialized with {len(self.config.get('crypto_pairs', {}))} crypto pairs")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.logger.warning(f"Configuration file not found: {config_file}, using defaults")
                return self._get_default_config()
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Load Discord configuration
            discord_config = self._load_discord_config()
            if discord_config:
                config['discord_config'] = discord_config
                self.logger.info("Discord configuration loaded")
            else:
                self.logger.info("No Discord configuration found - Discord alerts disabled")
            
            self.logger.info(f"Loaded configuration from {config_file}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}, using defaults")
            return self._get_default_config()
    
    def _load_discord_config(self) -> Optional[Dict[str, Any]]:
        """Load Discord configuration from file."""
        try:
            discord_config_path = Path("config/correlation_analysis/discord_config.json")
            if not discord_config_path.exists():
                self.logger.warning("Discord configuration file not found")
                return None
            
            with open(discord_config_path, 'r') as f:
                discord_config = json.load(f)
            
            # Check if webhook URL is provided
            if not discord_config.get('discord_webhook_url'):
                self.logger.warning("No Discord webhook URL provided in configuration")
                return None
            
            return discord_config
            
        except Exception as e:
            self.logger.error(f"Failed to load Discord configuration: {e}")
            return None
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "crypto_pairs": {
                "BTC_ETH": {
                    "primary": "bitcoin",
                    "secondary": "ethereum",
                    "correlation_windows": [7, 14, 30]
                }
            },
            "macro_pairs": {},
            "monitoring_settings": {
                "update_frequency_seconds": 300,
                "data_retention_days": 365,
                "cache_ttl_seconds": 3600,
                "max_alerts_per_hour": 10
            }
        }
    
    def get_monitored_pairs(self) -> List[str]:
        """Get list of all monitored pairs."""
        pairs = []
        
        # Add crypto pairs
        crypto_pairs = self.config.get('crypto_pairs', {})
        pairs.extend(crypto_pairs.keys())
        
        # Add macro pairs
        macro_pairs = self.config.get('macro_pairs', {})
        pairs.extend(macro_pairs.keys())
        
        return pairs
    
    def start_monitoring(self, run_once: bool = False) -> bool:
        """
        Start monitoring all configured pairs.
        
        Args:
            run_once: If True, run monitoring once and return. If False, run continuously.
            
        Returns:
            bool: True if monitoring started successfully
        """
        try:
            self.logger.info("Starting correlation monitoring engine")
            
            # Get all monitored pairs
            pairs = self.get_monitored_pairs()
            if not pairs:
                self.logger.warning("No pairs configured for monitoring")
                return False
            
            self.logger.info(f"Monitoring {len(pairs)} pairs: {', '.join(pairs)}")
            
            if run_once:
                # Run monitoring once
                start_time = time.time()
                success = self._run_monitoring_cycle(pairs)
                
                # Update performance metrics for single run
                cycle_time = time.time() - start_time
                self.performance_metrics['total_monitoring_time'] += cycle_time
                self.performance_metrics['total_runs'] += 1
                
                if success:
                    self.performance_metrics['successful_runs'] += 1
                    self.performance_metrics['last_successful_run'] = datetime.now()
                else:
                    self.performance_metrics['failed_runs'] += 1
                
                self.performance_metrics['last_run_time'] = datetime.now()
                self.performance_metrics['avg_monitoring_time'] = (
                    self.performance_metrics['total_monitoring_time'] / 
                    self.performance_metrics['total_runs']
                )
                
                return success
            else:
                # Start continuous monitoring
                self.stop_monitoring.clear()
                self.monitoring_thread = threading.Thread(
                    target=self._continuous_monitoring_loop,
                    args=(pairs,),
                    daemon=True
                )
                self.monitoring_thread.start()
                
                self.logger.info("Continuous monitoring started")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self.logger.info("Stopping correlation monitoring")
        self.stop_monitoring.set()
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=30)
            self.logger.info("Monitoring stopped")
    
    def _continuous_monitoring_loop(self, pairs: List[str]) -> None:
        """Continuous monitoring loop."""
        monitoring_settings = self.config.get('monitoring_settings', {})
        update_frequency = monitoring_settings.get('update_frequency_seconds', 300)
        
        self.logger.info(f"Starting continuous monitoring loop with {update_frequency}s intervals")
        
        while not self.stop_monitoring.is_set():
            try:
                start_time = time.time()
                
                # Run monitoring cycle
                success = self._run_monitoring_cycle(pairs)
                
                # Check if daily mosaic generation is due
                self._check_and_generate_daily_mosaic()
                
                # Update performance metrics
                cycle_time = time.time() - start_time
                self.performance_metrics['total_monitoring_time'] += cycle_time
                self.performance_metrics['total_runs'] += 1
                
                if success:
                    self.performance_metrics['successful_runs'] += 1
                    self.performance_metrics['last_successful_run'] = datetime.now()
                else:
                    self.performance_metrics['failed_runs'] += 1
                
                self.performance_metrics['last_run_time'] = datetime.now()
                self.performance_metrics['avg_monitoring_time'] = (
                    self.performance_metrics['total_monitoring_time'] / 
                    self.performance_metrics['total_runs']
                )
                
                self.logger.info(f"Monitoring cycle completed in {cycle_time:.2f}s (success: {success})")
                
                # Wait for next cycle
                if not self.stop_monitoring.is_set():
                    time.sleep(update_frequency)
                    
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                if not self.stop_monitoring.is_set():
                    time.sleep(update_frequency)
    
    def _run_monitoring_cycle(self, pairs: List[str]) -> bool:
        """
        Run a single monitoring cycle for all pairs.
        
        Args:
            pairs: List of pairs to monitor
            
        Returns:
            bool: True if cycle completed successfully
        """
        try:
            self.logger.info(f"Starting monitoring cycle for {len(pairs)} pairs")
            
            # Initialize monitors for pairs that don't have them
            self._initialize_monitors(pairs)
            
            # Run monitoring in parallel using ThreadPoolExecutor
            results = {}
            with ThreadPoolExecutor(max_workers=min(len(pairs), 4)) as executor:
                # Submit monitoring tasks
                future_to_pair = {
                    executor.submit(self._monitor_single_pair, pair): pair 
                    for pair in pairs
                }
                
                # Collect results
                for future in as_completed(future_to_pair):
                    pair = future_to_pair[future]
                    try:
                        result = future.result(timeout=60)  # 60 second timeout per pair
                        results[pair] = result
                    except Exception as e:
                        self.logger.error(f"Failed to monitor {pair}: {e}")
                        results[pair] = {
                            'success': False,
                            'reason': f'monitoring_error: {str(e)}'
                        }
            
            # Process results
            successful_monitoring = 0
            total_alerts = 0
            
            for pair, result in results.items():
                if result.get('success', False):
                    successful_monitoring += 1
                    
                    # Count alerts
                    alerts_generated = len(result.get('alerts_generated', []))
                    total_alerts += alerts_generated
                    
                    if alerts_generated > 0:
                        self.logger.info(f"Generated {alerts_generated} alerts for {pair}")
                
                # Log partial failures
                partial_failures = result.get('partial_failures', [])
                if partial_failures:
                    self.logger.warning(f"Partial failures for {pair}: {partial_failures}")
            
            self.logger.info(f"Monitoring cycle completed: {successful_monitoring}/{len(pairs)} pairs successful, {total_alerts} alerts generated")
            
            return successful_monitoring > 0
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
            return False
    
    def _initialize_monitors(self, pairs: List[str]) -> None:
        """Initialize monitors for pairs that don't have them."""
        for pair in pairs:
            if pair not in self.monitors:
                try:
                    # Get pair configuration
                    pair_config = self._get_pair_config(pair)
                    
                    # Add Discord configuration if available
                    discord_config = self.config.get('discord_config')
                    if discord_config:
                        pair_config['discord_config'] = discord_config
                    
                    # Create monitor
                    monitor = CorrelationMonitor(pair, pair_config)
                    self.monitors[pair] = monitor
                    
                    self.logger.debug(f"Initialized monitor for {pair}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to initialize monitor for {pair}: {e}")
    
    def _get_pair_config(self, pair: str) -> Dict[str, Any]:
        """Get configuration for a specific pair."""
        # Check crypto pairs
        crypto_pairs = self.config.get('crypto_pairs', {})
        if pair in crypto_pairs:
            return crypto_pairs[pair]
        
        # Check macro pairs
        macro_pairs = self.config.get('macro_pairs', {})
        if pair in macro_pairs:
            return macro_pairs[pair]
        
        # Return default configuration
        return {
            'correlation_windows': [7, 14, 30],
            'min_data_points': 20,
            'z_score_threshold': 2.0,
            'monitoring_interval_minutes': 15,
            'data_lookback_days': 60,
            'alert_on_breakout': True,
            'store_correlation_history': True,
            'store_breakout_history': True
        }
    
    def _monitor_single_pair(self, pair: str) -> Dict[str, Any]:
        """Monitor a single pair."""
        try:
            monitor = self.monitors.get(pair)
            if not monitor:
                self.logger.error(f"No monitor found for {pair}")
                return {
                    'success': False,
                    'reason': 'no_monitor'
                }
            
            # Run monitoring
            result = monitor.monitor_pair(pair)
            return result
            
        except Exception as e:
            self.logger.error(f"Error monitoring {pair}: {e}")
            return {
                'success': False,
                'reason': f'monitoring_error: {str(e)}'
            }
    
    def _check_and_generate_daily_mosaic(self) -> None:
        """Check if daily mosaic generation is due and generate if needed."""
        try:
            from pytz import timezone
            
            # Get current time in Hong Kong timezone (GMT+8)
            hk_tz = timezone('Asia/Hong_Kong')
            current_time_hk = datetime.now(hk_tz)
            current_hour = current_time_hk.hour
            current_date = current_time_hk.date()
            
            # Target time: 9:00 AM HK Time
            target_hour = 9
            
            # Check if we should generate daily mosaic
            should_generate = False
            
            if self.last_mosaic_generation is None:
                # First time - generate if it's after 9 AM HK time, or if it's before 9 AM (generate previous day's)
                should_generate = True
                self.logger.info("First-time mosaic generation")
            else:
                # Convert last generation time to HK timezone for comparison
                if self.last_mosaic_generation.tzinfo is None:
                    # Assume UTC if no timezone info
                    last_gen_utc = self.last_mosaic_generation.replace(tzinfo=timezone('UTC'))
                else:
                    last_gen_utc = self.last_mosaic_generation
                
                last_gen_hk = last_gen_utc.astimezone(hk_tz)
                last_gen_date = last_gen_hk.date()
                
                # Check if it's a new day and we're at or past 9 AM HK time
                if current_date > last_gen_date and current_hour >= target_hour:
                    should_generate = True
                    self.logger.info(f"Daily mosaic due: New day ({current_date}) and past 9 AM HK time ({current_hour}:xx)")
                elif current_date > last_gen_date and current_hour < target_hour:
                    # It's a new day but before 9 AM - don't generate yet
                    should_generate = False
                else:
                    # Same day or before target time
                    should_generate = False
            
            if should_generate:
                self.logger.info("🎨 Generating daily correlation mosaic...")
                try:
                    from ..alerts.mosaic_alert_system import MosaicAlertSystem
                    
                    # Load Discord config
                    discord_config = self.config.get('discord_config')
                    
                    # Initialize mosaic alert system
                    mosaic_system = MosaicAlertSystem(discord_config=discord_config)
                    
                    # Generate daily mosaic alert
                    alert_path = mosaic_system.generate_daily_mosaic_alert(force_regeneration=False)
                    
                    if alert_path:
                        self.logger.info(f"✅ Daily mosaic alert generated: {alert_path}")
                        self.logger.info(f"📅 Next mosaic scheduled for: {(current_time_hk + timedelta(days=1)).strftime('%Y-%m-%d 09:00 HKT')}")
                        self.last_mosaic_generation = current_time_hk
                    else:
                        self.logger.warning("⚠️ Failed to generate daily mosaic alert")
                        
                except Exception as e:
                    self.logger.error(f"Error generating daily mosaic: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in daily mosaic check: {e}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get the current status of the correlation engine."""
        status = {
            'engine_running': self.monitoring_thread is not None and self.monitoring_thread.is_alive(),
            'monitored_pairs': self.get_monitored_pairs(),
            'active_monitors': len(self.monitors),
            'performance_metrics': self.performance_metrics.copy(),
            'last_config_update': datetime.fromtimestamp(Path(self.config_path).stat().st_mtime).isoformat() if Path(self.config_path).exists() else None
        }
        
        return status
    
    def get_pair_status(self, pair: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific pair."""
        if pair not in self.monitors:
            return None
        
        monitor = self.monitors[pair]
        return monitor.get_monitoring_status()
    
    def reload_config(self) -> bool:
        """Reload configuration from file."""
        try:
            self.logger.info("Reloading configuration")
            self.config = self._load_config()
            
            # Reinitialize monitors with new configuration
            pairs = self.get_monitored_pairs()
            self._initialize_monitors(pairs)
            
            self.logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            return False

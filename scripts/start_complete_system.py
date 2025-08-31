#!/usr/bin/env python3
"""
Complete System Startup Script
Starts both the enhanced scheduler (for signal alerts) and correlation analysis (for daily matrices).
"""

import sys
import os
import time
import subprocess
import signal
import threading
import json
import logging
from datetime import datetime
from typing import Dict, Optional

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class SystemManager:
    def __init__(self):
        self.processes = {}
        self.running = False
        self.logger = self._setup_logging()
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
    def _setup_logging(self):
        """Setup proper logging system."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/system_manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def load_config(self):
        """Load configuration from file or use defaults."""
        config_file = 'config/system_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}")
        
        return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration."""
        return {
            'enhanced_scheduler': {
                'command': ['python3', 'main_enhanced.py', '--background'],
                'restart_on_failure': True,
                'max_restarts': 3,
                'health_check_interval': 30
            },
            'correlation_analysis': {
                'command': ['python3', '-m', 'src.correlation_analysis', '--monitor'],
                'restart_on_failure': True,
                'max_restarts': 3,
                'health_check_interval': 30
            },
            'monitoring': {
                'health_check_interval': 60,
                'log_rotation': True,
                'max_log_size': '10MB'
            }
        }
        
    def start_enhanced_scheduler(self):
        """Start the enhanced scheduler for signal generation."""
        self.logger.info("🚀 Starting Enhanced Scheduler...")
        try:
            # Change to parent directory (project root) where main_enhanced.py is located
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use log file with absolute path
            log_file = open(os.path.join(project_root, 'logs/enhanced_scheduler.log'), 'a')
            
            process = subprocess.Popen([
                'python3', 'main_enhanced.py', '--background'
            ], stdout=log_file, stderr=subprocess.STDOUT, 
               cwd=project_root)
            
            self.processes['enhanced_scheduler'] = {
                'process': process,
                'log_file': log_file,
                'restart_count': 0,
                'start_time': datetime.now()
            }
            
            self.logger.info(f"✅ Enhanced Scheduler started (PID: {process.pid})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to start Enhanced Scheduler: {e}")
            return False
    
    def start_correlation_analysis(self):
        """Start the correlation analysis system."""
        self.logger.info("🔗 Starting Correlation Analysis...")
        try:
            # Change to parent directory (project root) where src module is located
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use log file with absolute path
            log_file = open(os.path.join(project_root, 'logs/correlation_analysis.log'), 'a')
            
            process = subprocess.Popen([
                'python3', '-m', 'src.correlation_analysis', '--monitor'
            ], stdout=log_file, stderr=subprocess.STDOUT,
               cwd=project_root)
            
            self.processes['correlation_analysis'] = {
                'process': process,
                'log_file': log_file,
                'restart_count': 0,
                'start_time': datetime.now()
            }
            
            self.logger.info(f"✅ Correlation Analysis started (PID: {process.pid})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to start Correlation Analysis: {e}")
            return False
    
    def wait_for_process_ready(self, process_name: str, max_wait: int = 30):
        """Wait for process to be ready by checking its status."""
        self.logger.info(f"⏳ Waiting for {process_name} to be ready...")
        
        for i in range(max_wait):
            if self.check_process_health(process_name):
                self.logger.info(f"✅ {process_name} is ready")
                return True
            time.sleep(1)
            
        self.logger.warning(f"⚠️ {process_name} not ready after {max_wait} seconds")
        return False
    
    def check_process_health(self, process_name: str) -> bool:
        """Check if a process is healthy."""
        if process_name not in self.processes:
            return False
            
        process_info = self.processes[process_name]
        process = process_info['process']
        
        # Check if process is still running
        if process.poll() is not None:
            return False
        
        # Check process-specific health
        try:
            # Change to project root for health checks
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            if process_name == 'enhanced_scheduler':
                result = subprocess.run([
                    'python3', 'main_enhanced.py', '--status'
                ], capture_output=True, text=True, timeout=10, cwd=project_root)
                # Just check if the process returns successfully and contains status info
                return result.returncode == 0 and "EnhancedMultiTierScheduler" in result.stdout
                
            elif process_name == 'correlation_analysis':
                result = subprocess.run([
                    'python3', '-m', 'src.correlation_analysis', '--status'
                ], capture_output=True, text=True, timeout=10, cwd=project_root)
                # Just check if the process returns successfully and contains engine info
                return result.returncode == 0 and "Correlation engine" in result.stdout
                
        except Exception as e:
            self.logger.debug(f"Health check failed for {process_name}: {e}")
            return False
        
        return True
    
    def monitor_processes(self):
        """Monitor running processes and restart if needed."""
        for name, process_info in self.processes.items():
            process = process_info['process']
            
            if process.poll() is not None:  # Process has terminated
                self.logger.warning(f"⚠️ Process {name} has crashed! (Exit code: {process.returncode})")
                
                # Close log file
                if 'log_file' in process_info:
                    process_info['log_file'].close()
                
                # Check restart policy
                config = self.load_config()
                restart_policy = config.get(name, {})
                
                if restart_policy.get('restart_on_failure', True):
                    max_restarts = restart_policy.get('max_restarts', 3)
                    
                    if process_info['restart_count'] < max_restarts:
                        self.logger.info(f"🔄 Restarting {name} (attempt {process_info['restart_count'] + 1}/{max_restarts})")
                        
                        if name == 'enhanced_scheduler':
                            if self.start_enhanced_scheduler():
                                self.processes[name]['restart_count'] += 1
                        elif name == 'correlation_analysis':
                            if self.start_correlation_analysis():
                                self.processes[name]['restart_count'] += 1
                    else:
                        self.logger.error(f"❌ {name} exceeded max restart attempts ({max_restarts})")
                else:
                    self.logger.error(f"❌ {name} restart disabled by configuration")
    
    def check_system_status(self):
        """Check the status of both systems."""
        self.logger.info("📊 System Status Check")
        
        # Check enhanced scheduler status
        self.logger.info("🔍 Checking Enhanced Scheduler...")
        try:
            # Change to project root for status checks
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            result = subprocess.run([
                'python3', 'main_enhanced.py', '--status'
            ], capture_output=True, text=True, timeout=30, cwd=project_root)
            
            if result.returncode == 0:
                output = result.stdout
                if "Signal Generation: ✅ Enabled" in output:
                    self.logger.info("✅ Signal Generation: Enabled")
                else:
                    self.logger.warning("❌ Signal Generation: Disabled")
                    
                if "Alert Generation: ✅ Enabled" in output:
                    self.logger.info("✅ Alert Generation: Enabled")
                else:
                    self.logger.warning("❌ Alert Generation: Disabled")
                    
                if "Discord Alerts: ✅ Enabled" in output:
                    self.logger.info("✅ Discord Alerts: Enabled")
                else:
                    self.logger.warning("❌ Discord Alerts: Disabled")
            else:
                self.logger.error("❌ Failed to check Enhanced Scheduler status")
                
        except Exception as e:
            self.logger.error(f"❌ Error checking Enhanced Scheduler: {e}")
        
        # Check correlation analysis status
        self.logger.info("🔍 Checking Correlation Analysis...")
        try:
            result = subprocess.run([
                'python3', '-m', 'src.correlation_analysis', '--status'
            ], capture_output=True, text=True, timeout=30, cwd=project_root)
            
            if result.returncode == 0:
                output = result.stdout
                if "Engine status: ✅ Running" in output:
                    self.logger.info("✅ Correlation Engine: Running")  
                elif "Engine status: ❌ Stopped" in output:
                    self.logger.warning("❌ Correlation Engine: Stopped")
                else:
                    self.logger.info("📊 Correlation Engine: Status unknown")
                    
                # Check for recent alerts
                if "Recent alerts:" in output:
                    for line in output.split('\n'):
                        if "Recent alerts:" in line:
                            self.logger.info(f"📊 {line.strip()}")
                            break
            else:
                self.logger.error("❌ Failed to check Correlation Analysis status")
                
        except Exception as e:
            self.logger.error(f"❌ Error checking Correlation Analysis: {e}")
    
    def generate_test_signals(self):
        """Generate a test signal to verify the system is working."""
        self.logger.info("🧪 Generating Test Signal...")
        try:
            # Change to project root for test signal generation
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Run a single correlation analysis cycle
            result = subprocess.run([
                'python3', '-m', 'src.correlation_analysis', '--run-once'
            ], capture_output=True, text=True, timeout=60, cwd=project_root)
            
            if result.returncode == 0:
                self.logger.info("✅ Test correlation analysis completed")
            else:
                self.logger.error("❌ Test correlation analysis failed")
                
        except Exception as e:
            self.logger.error(f"❌ Error generating test signal: {e}")
    
    def check_recent_alerts(self):
        """Check for recent alerts and correlation matrices."""
        self.logger.info("📋 Recent Alerts and Matrices")
        
        # Use dynamic date instead of hardcoded
        today = datetime.now().strftime('%Y%m%d')
        
        # Check signal alerts
        alerts_dir = "data/alerts"
        if os.path.exists(alerts_dir):
            alerts = [f for f in os.listdir(alerts_dir) if f.endswith('.json')]
            recent_alerts = [f for f in alerts if today in f]
            self.logger.info(f"📊 Signal Alerts: {len(recent_alerts)} today")
            for alert in recent_alerts[-5:]:  # Show last 5
                self.logger.info(f"   📄 {alert}")
        
        # Check correlation alerts
        correlation_alerts_dir = "data/correlation/alerts"
        if os.path.exists(correlation_alerts_dir):
            alerts = [f for f in os.listdir(correlation_alerts_dir) if f.endswith('.json')]
            recent_alerts = [f for f in alerts if today in f]
            self.logger.info(f"🔗 Correlation Alerts: {len(recent_alerts)} today")
            for alert in recent_alerts[-5:]:  # Show last 5
                self.logger.info(f"   📄 {alert}")
        
        # Check correlation matrices
        mosaics_dir = "data/correlation/mosaics"
        if os.path.exists(mosaics_dir):
            mosaics = [f for f in os.listdir(mosaics_dir) if f.endswith('.json')]
            recent_mosaics = [f for f in mosaics if today in f]
            self.logger.info(f"🎨 Correlation Matrices: {len(recent_mosaics)} today")
            for mosaic in recent_mosaics[-5:]:  # Show last 5
                self.logger.info(f"   📄 {mosaic}")
    
    def check_strategy_configuration(self):
        """Check and display strategy configuration information."""
        self.logger.info("🎯 Strategy Configuration Check")
        
        try:
            # Change to project root for strategy checks
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Check strategy registry
            self.logger.info("📊 Checking Strategy Registry...")
            try:
                result = subprocess.run([
                    'python3', '-c', 
                    'import sys; sys.path.append("."); from src.signals.strategies.strategy_registry import StrategyRegistry; registry = StrategyRegistry(); registry.load_strategies_from_directory("src/signals/strategies"); strategies = registry.list_strategies(); print("Available strategies:", list(strategies.keys()))'
                ], capture_output=True, text=True, timeout=30, cwd=project_root)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if "Available strategies:" in output:
                        strategies = output.split("Available strategies:")[1].strip()
                        self.logger.info(f"✅ Strategy Registry: {strategies}")
                    else:
                        self.logger.warning("⚠️ Strategy Registry: Could not parse output")
                else:
                    self.logger.warning("⚠️ Strategy Registry: Check failed")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Strategy Registry check failed: {e}")
            
            # Check multi-strategy generator configuration
            self.logger.info("🔧 Checking Multi-Strategy Generator...")
            try:
                result = subprocess.run([
                    'python3', '-c', 
                    'import sys; sys.path.append("."); from src.services.multi_strategy_generator import create_default_multi_strategy_generator; generator = create_default_multi_strategy_generator(); print("Loaded strategies:", list(generator.strategies.keys())); print("Strategy weights:", generator.aggregator_config.get("strategy_weights", {}))'
                ], capture_output=True, text=True, timeout=30, cwd=project_root)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    lines = output.split('\n')
                    
                    for line in lines:
                        if "Loaded strategies:" in line:
                            strategies = line.split("Loaded strategies:")[1].strip()
                            self.logger.info(f"✅ Loaded Strategies: {strategies}")
                        elif "Strategy weights:" in line:
                            weights = line.split("Strategy weights:")[1].strip()
                            self.logger.info(f"📊 Strategy Weights: {weights}")
                else:
                    self.logger.warning("⚠️ Multi-Strategy Generator: Check failed")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Multi-Strategy Generator check failed: {e}")
            
            # Check Discord webhook configuration
            self.logger.info("📢 Checking Discord Integration...")
            try:
                webhook_config_path = os.path.join(project_root, 'config/strategy_discord_webhooks.json')
                if os.path.exists(webhook_config_path):
                    import json
                    with open(webhook_config_path, 'r') as f:
                        webhook_config = json.load(f)
                    
                    strategy_webhooks = webhook_config.get('strategy_webhooks', {})
                    configured_strategies = list(strategy_webhooks.keys())
                    
                    self.logger.info(f"✅ Discord Webhooks: {len(configured_strategies)} strategies configured")
                    for strategy in configured_strategies:
                        config = strategy_webhooks[strategy]
                        webhook_configured = "✅" if config.get('webhook_url') else "❌"
                        min_confidence = config.get('min_confidence', 'Not set')
                        enabled_assets = len(config.get('enabled_assets', []))
                        self.logger.info(f"   {webhook_configured} {strategy}: confidence≥{min_confidence}, {enabled_assets} assets")
                else:
                    self.logger.warning("⚠️ Discord webhook configuration file not found")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Discord integration check failed: {e}")
            
            # Check environment configuration
            self.logger.info("⚙️ Checking Environment Configuration...")
            try:
                result = subprocess.run([
                    'python3', '-c', 
                    'import sys; sys.path.append("."); from config.settings import Config; config = Config(); print("Enabled strategies:", config.ENABLED_STRATEGIES); print("Strategy weights:", config.STRATEGY_WEIGHTS)'
                ], capture_output=True, text=True, timeout=30, cwd=project_root)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    lines = output.split('\n')
                    
                    for line in lines:
                        if "Enabled strategies:" in line:
                            strategies = line.split("Enabled strategies:")[1].strip()
                            self.logger.info(f"✅ Environment Strategies: {strategies}")
                        elif "Strategy weights:" in line:
                            weights = line.split("Strategy weights:")[1].strip()
                            self.logger.info(f"📊 Environment Weights: {weights}")
                else:
                    self.logger.warning("⚠️ Environment configuration check failed")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Environment configuration check failed: {e}")
            
            # Display strategy summary
            self.logger.info("📋 Strategy Summary:")
            self.logger.info("   🎯 Multi-Bucket Portfolio: Cross-sectional momentum, residual analysis, mean-reversion")
            self.logger.info("   📈 VIX Correlation: Market regime detection and volatility analysis")
            self.logger.info("   🔄 Mean Reversion: Overextended moves and drawdown analysis")
            self.logger.info("   📊 Volatility: Breakout detection and volatility regime analysis")
            self.logger.info("   🌊 Ripple: Specialized XRP analysis and momentum detection")
            self.logger.info("   📢 Discord Alerts: Real-time notifications for all strategies")
            
        except Exception as e:
            self.logger.error(f"❌ Error checking strategy configuration: {e}")
    
    def start_complete_system(self):
        """Start the complete system."""
        self.logger.info("🚀 Starting Complete MTS Data Pipeline System")
        self.logger.info(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Start enhanced scheduler
            if not self.start_enhanced_scheduler():
                self.logger.error("❌ Failed to start Enhanced Scheduler")
                return False
            
            # Wait for scheduler to be ready
            if not self.wait_for_process_ready('enhanced_scheduler'):
                self.logger.warning("⚠️ Enhanced Scheduler may not be fully ready")
            
            # Start correlation analysis
            if not self.start_correlation_analysis():
                self.logger.error("❌ Failed to start Correlation Analysis")
                return False
            
            # Wait for correlation analysis to be ready
            if not self.wait_for_process_ready('correlation_analysis'):
                self.logger.warning("⚠️ Correlation Analysis may not be fully ready")
            
            # Check initial status
            self.check_system_status()
            
            # Check strategy configuration
            self.check_strategy_configuration()
            
            # Generate a test signal
            self.generate_test_signals()
            
            # Check for recent alerts
            self.check_recent_alerts()
            
            self.logger.info("✅ Complete system started successfully!")
            self.logger.info("📋 What's now running:")
            self.logger.info("   🚀 Enhanced Scheduler: Signal generation every hour")
            self.logger.info("   🔗 Correlation Analysis: Continuous monitoring")
            self.logger.info("   📊 Daily Correlation Matrices: Generated automatically")
            self.logger.info("   🚨 Signal Alerts: Generated for high-confidence signals")
            self.logger.info("   📈 ENA Integration: High-frequency tracking (15-minute intervals)")
            self.logger.info("   🎯 Multi-Bucket Portfolio Strategy: Integrated with Discord alerts")
            
            self.logger.info("📋 How to monitor:")
            self.logger.info("   • Check status: python3 main_enhanced.py --status")
            self.logger.info("   • Check correlation: python3 -m src.correlation_analysis --status")
            self.logger.info("   • View alerts: ls -la data/alerts/")
            self.logger.info("   • View matrices: ls -la data/correlation/mosaics/")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in start_complete_system: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def stop_system(self):
        """Stop all running processes with graceful shutdown."""
        self.logger.info("🛑 Stopping system...")
        
        # First, send SIGTERM (graceful shutdown)
        for name, process_info in self.processes.items():
            try:
                process = process_info['process']
                self.logger.info(f"🔄 Sending SIGTERM to {name}...")
                process.terminate()
            except Exception as e:
                self.logger.error(f"❌ Error terminating {name}: {e}")
        
        # Wait for graceful shutdown
        self.logger.info("⏳ Waiting for graceful shutdown...")
        time.sleep(10)
        
        # Force kill if still running
        for name, process_info in self.processes.items():
            try:
                process = process_info['process']
                if process.poll() is None:  # Still running
                    self.logger.warning(f"⚠️ Force killing {name}...")
                    process.kill()
                    process.wait(timeout=5)
                
                # Close log file
                if 'log_file' in process_info:
                    process_info['log_file'].close()
                    
                self.logger.info(f"✅ Stopped {name}")
            except Exception as e:
                self.logger.error(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
        self.logger.info("✅ System stopped")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    print(f"\n🛑 Received signal {signum}...")
    if hasattr(signal_handler, 'manager'):
        signal_handler.manager.stop_system()
    sys.exit(0)

def main():
    """Main function."""
    manager = SystemManager()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal_handler.manager = manager  # Store reference for signal handler
    
    try:
        # Start the complete system
        if manager.start_complete_system():
            manager.logger.info("🎉 System is now running! Press Ctrl+C to stop.")
            
            # Keep the script running with process monitoring
            while True:
                time.sleep(60)  # Check every minute
                manager.monitor_processes()  # Monitor and restart if needed
        else:
            manager.logger.error("❌ Failed to start complete system")
            return 1
                
    except KeyboardInterrupt:
        manager.logger.info("🛑 Received stop signal...")
        manager.stop_system()
        manager.logger.info("👋 Goodbye!")

if __name__ == "__main__":
    main()

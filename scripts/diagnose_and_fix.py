#!/usr/bin/env python3
"""
Diagnose and Fix Script
Identifies why you're not getting signal alerts or daily correlation matrices and provides solutions.
"""

import sys
import os
import subprocess
import logging
from datetime import datetime

def setup_logging():
    """Setup logging for the diagnostic script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/diagnostic.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_enhanced_scheduler():
    """Check enhanced scheduler status."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Checking Enhanced Scheduler...")
    try:
        result = subprocess.run([
            'python3', 'main_enhanced.py', '--status'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout
            issues = []
            
            if "Signal Generation: ❌ Disabled" in output:
                issues.append("Signal generation is disabled")
            if "Alert Generation: ❌ Disabled" in output:
                issues.append("Alert generation is disabled")
            if "🔄 Scheduler Status: 🔴 Stopped" in output:
                issues.append("Scheduler is stopped")
            
            if issues:
                logger.warning("❌ Issues found:")
                for issue in issues:
                    logger.warning(f"   • {issue}")
                return False
            else:
                logger.info("✅ Enhanced Scheduler is properly configured")
                return True
        else:
            logger.error("❌ Failed to check Enhanced Scheduler")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Enhanced Scheduler status check timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking Enhanced Scheduler: {e}")
        return False

def check_correlation_analysis():
    """Check correlation analysis status."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Checking Correlation Analysis...")
    try:
        result = subprocess.run([
            'python3', '-m', 'src.correlation_analysis', '--status'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout
            issues = []
            
            if "Engine status: ❌ Stopped" in output:
                issues.append("Correlation engine is stopped")
            if "total_runs': 0" in output:
                issues.append("Correlation engine has never run")
            
            if issues:
                logger.warning("❌ Issues found:")
                for issue in issues:
                    logger.warning(f"   • {issue}")
                return False
            else:
                logger.info("✅ Correlation Analysis is properly configured")
                return True
        else:
            logger.error("❌ Failed to check Correlation Analysis")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Correlation Analysis status check timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking Correlation Analysis: {e}")
        return False

def check_recent_outputs():
    """Check for recent alerts and matrices."""
    logger = logging.getLogger(__name__)
    logger.info("📋 Checking Recent Outputs...")
    
    # Use dynamic date instead of hardcoded
    today = datetime.now().strftime('%Y%m%d')
    
    # Check signal alerts
    alerts_dir = "data/alerts"
    if os.path.exists(alerts_dir):
        alerts = [f for f in os.listdir(alerts_dir) if f.endswith('.json')]
        recent_alerts = [f for f in alerts if today in f]
        logger.info(f"📊 Signal Alerts: {len(recent_alerts)} today")
        if len(recent_alerts) == 0:
            logger.warning("   ⚠️ No signal alerts generated today")
    
    # Check correlation matrices
    mosaics_dir = "data/correlation/mosaics"
    if os.path.exists(mosaics_dir):
        mosaics = [f for f in os.listdir(mosaics_dir) if f.endswith('.json')]
        recent_mosaics = [f for f in mosaics if today in f]
        logger.info(f"🎨 Correlation Matrices: {len(recent_mosaics)} today")
        if len(recent_mosaics) == 0:
            logger.warning("   ⚠️ No correlation matrices generated today")

def check_system_processes():
    """Check if system processes are running."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Checking System Processes...")
    
    try:
        # Check for running Python processes
        result = subprocess.run([
            'ps', 'aux'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout
            processes_found = []
            
            if 'main_enhanced.py' in output:
                processes_found.append("Enhanced Scheduler")
            if 'correlation_analysis' in output:
                processes_found.append("Correlation Analysis")
            
            if processes_found:
                logger.info(f"✅ Running processes: {', '.join(processes_found)}")
            else:
                logger.warning("⚠️ No system processes found running")
                
        else:
            logger.error("❌ Failed to check system processes")
            
    except Exception as e:
        logger.error(f"❌ Error checking system processes: {e}")

def provide_solutions():
    """Provide step-by-step solutions."""
    logger = logging.getLogger(__name__)
    logger.info("🔧 SOLUTIONS")
    logger.info("=" * 50)
    
    logger.info("📋 Issue: You're not getting signal alerts or daily correlation matrices")
    logger.info("")
    logger.info("🎯 Root Causes:")
    logger.info("   1. Enhanced Scheduler is not running (for signal alerts)")
    logger.info("   2. Correlation Analysis is not running (for daily matrices)")
    logger.info("   3. Both systems need to be started separately")
    
    logger.info("")
    logger.info("🚀 Step-by-Step Solution:")
    logger.info("   1. Start Enhanced Scheduler for signal alerts:")
    logger.info("      python3 main_enhanced.py --background")
    logger.info("")
    logger.info("   2. Start Correlation Analysis for daily matrices:")
    logger.info("      python3 -m src.correlation_analysis --monitor")
    logger.info("")
    logger.info("   3. Or use the complete system startup script:")
    logger.info("      python3 scripts/start_complete_system.py")
    
    logger.info("")
    logger.info("📊 Monitoring Commands:")
    logger.info("   • Check Enhanced Scheduler: python3 main_enhanced.py --status")
    logger.info("   • Check Correlation Analysis: python3 -m src.correlation_analysis --status")
    logger.info("   • View recent alerts: ls -la data/alerts/")
    logger.info("   • View recent matrices: ls -la data/correlation/mosaics/")
    
    logger.info("")
    logger.info("✅ Expected Results:")
    logger.info("   • Signal alerts will be generated every hour when conditions are met")
    logger.info("   • Daily correlation matrices will be generated automatically")
    logger.info("   • ENA will be tracked at high frequency (15-minute intervals)")
    logger.info("   • All correlation pairs including ENA will be monitored")

def run_quick_test():
    """Run a quick test to generate some output."""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Running Quick Test...")
    
    # Generate a test correlation matrix
    logger.info("   📊 Generating test correlation matrix...")
    try:
        result = subprocess.run([
            'python3', '-m', 'src.correlation_analysis', '--run-once'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info("   ✅ Test correlation analysis completed")
        else:
            logger.error("   ❌ Test correlation analysis failed")
            if result.stderr:
                logger.error(f"   Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("   ❌ Test correlation analysis timed out")
    except Exception as e:
        logger.error(f"   ❌ Error running test: {e}")

def check_system_health():
    """Comprehensive system health check."""
    logger = logging.getLogger(__name__)
    logger.info("🏥 System Health Check")
    logger.info("=" * 50)
    
    # Check if logs directory exists
    if not os.path.exists('logs'):
        logger.warning("⚠️ Logs directory does not exist")
        os.makedirs('logs', exist_ok=True)
        logger.info("✅ Created logs directory")
    
    # Check if data directories exist
    required_dirs = ['data/alerts', 'data/correlation/mosaics', 'data/correlation/alerts']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            logger.warning(f"⚠️ Directory {dir_path} does not exist")
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"✅ Created directory {dir_path}")
    
    # Check database
    if not os.path.exists('data/crypto_data.db'):
        logger.warning("⚠️ Database file does not exist")
    else:
        logger.info("✅ Database file exists")

def main():
    """Main diagnostic function."""
    # Setup logging
    logger = setup_logging()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    logger.info("🔍 MTS Data Pipeline Diagnostic")
    logger.info("=" * 50)
    logger.info(f"⏰ Diagnostic run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run comprehensive health check
    check_system_health()
    
    # Check system processes
    check_system_processes()
    
    # Check enhanced scheduler
    scheduler_ok = check_enhanced_scheduler()
    
    # Check correlation analysis
    correlation_ok = check_correlation_analysis()
    
    # Check recent outputs
    check_recent_outputs()
    
    # Run quick test
    run_quick_test()
    
    # Provide solutions
    provide_solutions()
    
    logger.info("")
    logger.info("=" * 50)
    if scheduler_ok and correlation_ok:
        logger.info("✅ All systems are properly configured!")
        logger.info("💡 The issue is likely that the systems are not running.")
        logger.info("🚀 Run: python3 scripts/start_complete_system.py")
    else:
        logger.info("❌ Issues detected in system configuration.")
        logger.info("🔧 Follow the solutions above to fix the issues.")

if __name__ == "__main__":
    main()

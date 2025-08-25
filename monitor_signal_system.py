#!/usr/bin/env python3
"""
Comprehensive Signal System Monitor
Checks all aspects of the MTS signal generation system
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.sqlite_helper import CryptoDatabase
from src.services.multi_strategy_generator import create_default_multi_strategy_generator

def check_database_data():
    """Check database for fresh price data"""
    print("🔍 Database Data Check")
    print("=" * 40)
    
    try:
        db = CryptoDatabase()
        data = db.get_strategy_market_data(['bitcoin', 'ethereum'], days=1)
        
        for asset in ['bitcoin', 'ethereum']:
            if asset in data and not data[asset].empty:
                latest = data[asset].iloc[-1]
                time_diff = datetime.now() - latest['datetime']
                
                print(f"📊 {asset.upper()}:")
                print(f"   Price: ${latest['close']:,.2f}")
                print(f"   Date: {latest['date_str']}")
                print(f"   Time: {latest['datetime']}")
                print(f"   Age: {time_diff}")
                print(f"   Records (24h): {len(data[asset])}")
                print()
            else:
                print(f"❌ No data for {asset}")
                print()
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        print()

def check_signal_generation():
    """Test signal generation with current data"""
    print("🎯 Signal Generation Test")
    print("=" * 40)
    
    try:
        # Create signal generator
        generator = create_default_multi_strategy_generator()
        
        # Generate signals
        print("Generating signals...")
        signals = generator.generate_aggregated_signals(days=30)
        
        print(f"✅ Generated {len(signals)} signals")
        
        for i, signal in enumerate(signals[:3]):  # Show first 3 signals
            print(f"\n📈 Signal {i+1}:")
            print(f"   Asset: {signal.symbol}")
            print(f"   Type: {signal.signal_type.value}")
            print(f"   Price: ${signal.price:,.2f}")
            print(f"   Confidence: {signal.confidence:.1%}")
            print(f"   Strength: {signal.signal_strength.value}")
            print(f"   Strategy: {signal.strategy_name}")
            print(f"   Timestamp: {signal.timestamp}")
            
    except Exception as e:
        print(f"❌ Signal generation failed: {e}")
        print()

def check_discord_configuration():
    """Check Discord configuration"""
    print("📢 Discord Configuration Check")
    print("=" * 40)
    
    # Check environment variables
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    alerts_enabled = os.getenv('DISCORD_ALERTS_ENABLED')
    min_confidence = os.getenv('DISCORD_MIN_CONFIDENCE')
    min_strength = os.getenv('DISCORD_MIN_STRENGTH')
    rate_limit = os.getenv('DISCORD_RATE_LIMIT_SECONDS')
    
    print(f"Webhook URL: {'✅ Set' if webhook_url else '❌ Not set'}")
    print(f"Alerts Enabled: {alerts_enabled}")
    print(f"Min Confidence: {min_confidence}")
    print(f"Min Strength: {min_strength}")
    print(f"Rate Limit: {rate_limit} seconds")
    print()

def check_recent_alerts():
    """Check for recent alert files"""
    print("📄 Recent Alert Files")
    print("=" * 40)
    
    alerts_dir = Path("data/alerts")
    if not alerts_dir.exists():
        print("❌ Alerts directory not found")
        return
    
    # Find recent files (last 7 days)
    recent_files = []
    for file_path in alerts_dir.glob("*"):
        if file_path.is_file():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime > datetime.now() - timedelta(days=7):
                recent_files.append((file_path, mtime))
    
    recent_files.sort(key=lambda x: x[1], reverse=True)
    
    if recent_files:
        print(f"Found {len(recent_files)} recent alert files:")
        for file_path, mtime in recent_files[:10]:  # Show last 10
            print(f"   {file_path.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print("No recent alert files found")
    print()

def check_scheduler_status():
    """Check if scheduler is running"""
    print("🔄 Scheduler Status")
    print("=" * 40)
    
    try:
        import subprocess
        result = subprocess.run(['python3', 'main_enhanced.py', '--status'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Extract key information from status output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Scheduler Status:' in line:
                    print(f"Status: {line.strip()}")
                elif 'Total Signals Generated:' in line:
                    print(f"Signals: {line.strip()}")
                elif 'Total Discord Alerts Sent:' in line:
                    print(f"Discord Alerts: {line.strip()}")
        else:
            print("❌ Failed to get scheduler status")
            
    except Exception as e:
        print(f"❌ Scheduler status check failed: {e}")
    print()

def check_process_status():
    """Check if background processes are running"""
    print("⚙️ Process Status")
    print("=" * 40)
    
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            mts_processes = [line for line in lines if 'main_enhanced.py' in line and 'grep' not in line]
            
            if mts_processes:
                print("✅ MTS processes running:")
                for process in mts_processes:
                    parts = process.split()
                    if len(parts) >= 11:
                        pid = parts[1]
                        cmd = ' '.join(parts[10:])
                        print(f"   PID {pid}: {cmd}")
            else:
                print("❌ No MTS processes found")
        else:
            print("❌ Failed to check processes")
            
    except Exception as e:
        print(f"❌ Process check failed: {e}")
    print()

def main():
    """Run all checks"""
    print("🚀 MTS Signal System Monitor")
    print("=" * 50)
    print(f"Time: {datetime.now()}")
    print()
    
    check_database_data()
    check_signal_generation()
    check_discord_configuration()
    check_recent_alerts()
    check_scheduler_status()
    check_process_status()
    
    print("✅ Monitoring complete!")

if __name__ == "__main__":
    main()

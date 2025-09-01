#!/usr/bin/env python3
"""
Discord Alert Monitoring Script

This script helps monitor and debug Discord alert issues by:
1. Checking recent alert activity
2. Verifying deduplication state
3. Showing signal generation history
4. Detecting potential stale alert issues
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import sys

def check_alert_dedupe_state():
    """Check the current alert deduplication state"""
    print("🔍 Checking Alert Deduplication State")
    print("=" * 50)
    
    dedupe_file = Path("data/alert_dedupe_state.json")
    if not dedupe_file.exists():
        print("❌ No deduplication state file found")
        return
    
    try:
        with open(dedupe_file, 'r') as f:
            state = json.load(f)
        
        if not state:
            print("✅ No alerts in deduplication cache")
            return
        
        current_time = time.time()
        ttl_seconds = int(os.getenv('DISCORD_ALERT_DEDUPE_TTL', '3600'))
        
        print(f"📊 Current Time: {datetime.fromtimestamp(current_time)}")
        print(f"⏰ TTL Setting: {ttl_seconds} seconds ({ttl_seconds//3600}h {(ttl_seconds%3600)//60}m)")
        print()
        
        for key, timestamp in state.items():
            alert_time = datetime.fromtimestamp(timestamp)
            age_seconds = current_time - timestamp
            age_minutes = age_seconds / 60
            will_expire_in = ttl_seconds - age_seconds
            
            # Parse key components
            parts = key.split('|')
            asset = parts[2].split('=')[1] if len(parts) > 2 else 'unknown'
            signal_type = parts[3].split('=')[1] if len(parts) > 3 else 'unknown' 
            price = parts[4].split('=')[1] if len(parts) > 4 else 'unknown'
            
            status = "🟢 ACTIVE" if will_expire_in > 0 else "🔴 EXPIRED"
            
            print(f"{status} {asset.upper()} {signal_type}")
            print(f"   💰 Price: ${price}")
            print(f"   🕐 Sent: {alert_time}")
            print(f"   ⌛ Age: {age_minutes:.1f} minutes")
            if will_expire_in > 0:
                print(f"   ⏳ Expires in: {will_expire_in/60:.1f} minutes")
            print()
            
    except Exception as e:
        print(f"❌ Error reading deduplication state: {e}")

def check_recent_logs():
    """Check recent log entries for Discord activity"""
    print("📋 Checking Recent Discord Activity")
    print("=" * 50)
    
    log_files = [
        "logs/enhanced_scheduler.log",
        "logs/correlation_analysis.log", 
        "logs/app.log"
    ]
    
    for log_file in log_files:
        if not Path(log_file).exists():
            continue
            
        print(f"\n📄 {log_file}")
        print("-" * 30)
        
        # Get recent Discord-related log entries
        try:
            result = subprocess.run([
                'tail', '-n', '100', log_file
            ], capture_output=True, text=True)
            
            lines = result.stdout.split('\n')
            discord_lines = [line for line in lines if 'discord' in line.lower()]
            
            if discord_lines:
                for line in discord_lines[-5:]:  # Show last 5 Discord entries
                    print(f"   {line}")
            else:
                print("   No recent Discord activity")
                
        except Exception as e:
            print(f"   Error reading {log_file}: {e}")

def check_running_processes():
    """Check if MTS processes are currently running"""
    print("🔄 Checking Running Processes")
    print("=" * 50)
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        mts_processes = []
        for line in lines:
            if 'python' in line.lower() and any(term in line.lower() for term in ['enhanced', 'correlation', 'mts']):
                mts_processes.append(line)
        
        if mts_processes:
            print("✅ MTS processes currently running:")
            for i, process in enumerate(mts_processes, 1):
                parts = process.split()
                if len(parts) > 10:
                    pid = parts[1]
                    command = ' '.join(parts[10:])
                    print(f"   {i}. PID {pid}: {command}")
        else:
            print("❌ No MTS processes currently running")
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")

def check_signal_generation_status():
    """Check the status of signal generation"""
    print("📈 Signal Generation Status")
    print("=" * 50)
    
    # Check scheduler state
    state_file = Path("data/enhanced_multi_tier_scheduler_state.json")
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            if 'last_signal_generation' in state:
                last_gen = datetime.fromisoformat(state['last_signal_generation'])
                time_since = datetime.now() - last_gen
                print(f"🕐 Last Signal Generation: {last_gen}")
                print(f"⏰ Time Since: {time_since}")
            
            print(f"📊 Total Signals Generated: {state.get('signals_generated', 0)}")
            print(f"🚨 Total Alerts Generated: {state.get('alerts_generated', 0)}")
            print(f"💬 Total Discord Alerts Sent: {state.get('discord_alerts_sent', 0)}")
            
        except Exception as e:
            print(f"❌ Error reading scheduler state: {e}")
    else:
        print("❌ No scheduler state file found")

def main():
    print("🔍 MTS Discord Alert Diagnostic Tool")
    print("="*60)
    print(f"🕐 Current Time: {datetime.now()}")
    print()
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    check_alert_dedupe_state()
    print()
    check_running_processes()
    print()
    check_signal_generation_status()
    print()
    check_recent_logs()
    
    print("\n" + "="*60)
    print("🎯 RECOMMENDATIONS:")
    print("   • If you see alerts from today but Discord shows old timestamps,")
    print("     this might be a timezone display issue in Discord")
    print("   • If deduplication cache shows expired entries, they should")
    print("     automatically clean up on next alert check")
    print("   • Monitor logs for actual signal generation times")
    print("   • Use 'python3 scripts/check_discord_alerts.py' to rerun this check")

if __name__ == "__main__":
    main()

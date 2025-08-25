#!/usr/bin/env python3
"""
Clear Discord rate limiting cache and restart the system
"""

import os
import sys
import signal
import subprocess
from pathlib import Path

def clear_discord_cache():
    print("🧹 Clearing Discord Rate Limiting Cache")
    print("=" * 50)
    
    # Kill all Python processes that might be running Discord managers
    print("1️⃣ Killing existing processes...")
    try:
        # Kill correlation analysis process
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        processes_to_kill = []
        for line in lines:
            if 'python' in line.lower() and ('correlation' in line.lower() or 'main_enhanced' in line.lower()):
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    processes_to_kill.append(pid)
        
        for pid in processes_to_kill:
            try:
                os.kill(int(pid), signal.SIGTERM)
                print(f"   Killed process {pid}")
            except Exception as e:
                print(f"   Failed to kill process {pid}: {e}")
                
    except Exception as e:
        print(f"   Error killing processes: {e}")
    
    print()
    
    # Clear any state files that might contain cached signal data
    print("2️⃣ Clearing state files...")
    state_files = [
        "data/enhanced_multi_tier_scheduler_state.json",
        "data/scheduler_state.json", 
        "data/multi_tier_scheduler_state.json"
    ]
    
    for state_file in state_files:
        if Path(state_file).exists():
            try:
                # Backup the file
                backup_file = f"{state_file}.backup"
                if Path(backup_file).exists():
                    os.remove(backup_file)
                os.rename(state_file, backup_file)
                print(f"   Backed up: {state_file}")
            except Exception as e:
                print(f"   Failed to backup {state_file}: {e}")
    
    print()
    
    # Clear any Discord webhook cache files
    print("3️⃣ Clearing Discord cache...")
    cache_patterns = [
        "data/cache/*",
        "logs/*discord*",
        "*.cache"
    ]
    
    for pattern in cache_patterns:
        try:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    print(f"   Removed: {file_path}")
        except Exception as e:
            print(f"   Error clearing {pattern}: {e}")
    
    print()
    
    # Restart the system with clean state
    print("4️⃣ Restarting system...")
    try:
        # Start the enhanced scheduler with environment variables loaded
        cmd = "source .env && python3 main_enhanced.py --background"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   ✅ System restarted")
    except Exception as e:
        print(f"   ❌ Failed to restart system: {e}")
    
    print()
    print("🎯 Discord cache cleared and system restarted!")
    print("   • All Discord rate limiting has been reset")
    print("   • State files have been backed up")
    print("   • System is running with fresh state")
    print()
    print("📋 Next steps:")
    print("   • Monitor for new Discord alerts")
    print("   • Check if duplicate alerts are resolved")
    print("   • Use 'python3 check_system_status.py' to verify")

if __name__ == "__main__":
    clear_discord_cache()

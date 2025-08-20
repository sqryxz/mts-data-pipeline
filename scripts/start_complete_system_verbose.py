#!/usr/bin/env python3
"""
Verbose version of the complete system starter that shows output in terminal
"""
import os
import sys
import subprocess
import time
import signal
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class VerboseSystemManager:
    def __init__(self):
        self.processes = {}
        
    def start_enhanced_scheduler_verbose(self):
        """Start enhanced scheduler with output to terminal"""
        print("🚀 Starting Enhanced Scheduler (verbose)...")
        
        # Use Popen with direct output to terminal
        process = subprocess.Popen([
            'python3', 'main_enhanced.py', '--background'
        ], cwd=project_root)
        
        self.processes['enhanced_scheduler'] = process
        print(f"✅ Enhanced Scheduler started (PID: {process.pid})")
        return True
        
    def start_correlation_analysis_verbose(self):
        """Start correlation analysis with output to terminal"""
        print("🔗 Starting Correlation Analysis (verbose)...")
        
        # Use Popen with direct output to terminal  
        process = subprocess.Popen([
            'python3', '-m', 'src.correlation_analysis', '--monitor'
        ], cwd=project_root)
        
        self.processes['correlation_analysis'] = process
        print(f"✅ Correlation Analysis started (PID: {process.pid})")
        return True
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}...")
        print("🛑 Stopping system...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"🔄 Sending SIGTERM to {name}...")
                process.terminate()
                
        print("⏳ Waiting for graceful shutdown...")
        time.sleep(5)
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"🔄 Force killing {name}...")
                process.kill()
                
        print("✅ System stopped")
        sys.exit(0)
        
    def run(self):
        """Run the verbose system"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🚀 Starting Complete MTS Data Pipeline System (VERBOSE MODE)")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📺 All output will be displayed in this terminal")
        print("🔄 Press Ctrl+C to stop\n")
        
        # Start both processes
        self.start_enhanced_scheduler_verbose()
        time.sleep(2)
        self.start_correlation_analysis_verbose()
        
        print("\n🎉 Both processes started! Output will appear below:")
        print("=" * 60)
        
        # Keep running and monitor processes
        try:
            while True:
                time.sleep(10)
                # Check if processes are still running
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        print(f"⚠️ {name} has stopped, restarting...")
                        if name == 'enhanced_scheduler':
                            self.start_enhanced_scheduler_verbose()
                        else:
                            self.start_correlation_analysis_verbose()
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    manager = VerboseSystemManager()
    manager.run()

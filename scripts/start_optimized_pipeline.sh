#!/bin/bash
#
# Start Optimized MTS Crypto Data Pipeline
# 
# This script starts the multi-tier background data collection service
# with proper logging, monitoring, and graceful shutdown capabilities.
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD="python3"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/data/optimized_pipeline.pid"
LOG_FILE="$LOG_DIR/optimized_pipeline.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Function to check if pipeline is already running
check_if_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            print_warning "Stale PID file found, removing..."
            rm -f "$PID_FILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Function to start the pipeline
start_pipeline() {
    print_status "Starting Optimized MTS Crypto Data Pipeline"
    print_info "Project root: $PROJECT_ROOT"
    
    # Check if already running
    if check_if_running; then
        print_error "Pipeline is already running (PID: $(cat "$PID_FILE"))"
        print_info "Use '$0 stop' to stop it first, or '$0 status' to check status"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$PROJECT_ROOT/data"
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    # Display configuration
    print_info "Configuration:"
    print_info "  • BTC & ETH: Every 15 minutes"
    print_info "  • Other cryptos: Every 60 minutes"
    print_info "  • Macro indicators: Daily"
    print_info "  • Estimated API calls: ~393/day (86% reduction)"
    print_info "  • Log file: $LOG_FILE"
    echo
    
    # Start the pipeline in background
    print_status "Launching background service..."
    
    nohup $PYTHON_CMD main_optimized.py --background > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    
    if ps -p $pid > /dev/null 2>&1; then
        print_status "✅ Pipeline started successfully!"
        print_info "PID: $pid"
        print_info "Logs: tail -f $LOG_FILE"
        print_info "Status: $0 status"
        print_info "Stop: $0 stop"
        echo
        
        # Show initial log output
        print_info "Initial log output:"
        echo "----------------------------------------"
        tail -20 "$LOG_FILE" 2>/dev/null || true
        echo "----------------------------------------"
        
    else
        print_error "❌ Failed to start pipeline"
        rm -f "$PID_FILE"
        
        # Show error logs
        if [[ -f "$LOG_FILE" ]]; then
            print_error "Error logs:"
            tail -20 "$LOG_FILE"
        fi
        exit 1
    fi
}

# Function to stop the pipeline
stop_pipeline() {
    print_status "Stopping Optimized MTS Crypto Data Pipeline"
    
    if ! check_if_running; then
        print_warning "Pipeline is not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    print_info "Sending SIGTERM to process $pid..."
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $pid 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while ps -p $pid > /dev/null 2>&1 && [[ $count -lt 30 ]]; do
        sleep 1
        ((count++))
        if [[ $((count % 5)) -eq 0 ]]; then
            print_info "Waiting for graceful shutdown... (${count}s)"
        fi
    done
    
    # Force kill if still running
    if ps -p $pid > /dev/null 2>&1; then
        print_warning "Process still running, sending SIGKILL..."
        kill -KILL $pid 2>/dev/null || true
        sleep 2
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    if ps -p $pid > /dev/null 2>&1; then
        print_error "❌ Failed to stop pipeline"
        exit 1
    else
        print_status "✅ Pipeline stopped successfully"
    fi
}

# Function to show pipeline status
show_status() {
    print_status "Optimized MTS Crypto Data Pipeline Status"
    echo "========================================"
    
    if check_if_running; then
        local pid=$(cat "$PID_FILE")
        print_status "🟢 RUNNING (PID: $pid)"
        
        # Show process info
        print_info "Process details:"
        ps -p $pid -o pid,ppid,pcpu,pmem,etime,cmd 2>/dev/null || true
        echo
        
        # Show recent logs
        if [[ -f "$LOG_FILE" ]]; then
            print_info "Recent activity (last 10 lines):"
            echo "----------------------------------------"
            tail -10 "$LOG_FILE" 2>/dev/null || print_warning "No logs available"
            echo "----------------------------------------"
        fi
        
        # Show API call status if possible
        print_info "For detailed status: $PYTHON_CMD main_optimized.py --status"
        
    else
        print_status "🔴 STOPPED"
        
        # Show last logs if available
        if [[ -f "$LOG_FILE" ]]; then
            print_info "Last known activity:"
            echo "----------------------------------------"
            tail -5 "$LOG_FILE" 2>/dev/null || print_warning "No logs available"
            echo "----------------------------------------"
        fi
    fi
    
    echo
    print_info "Useful commands:"
    print_info "  Start:  $0 start"
    print_info "  Stop:   $0 stop"
    print_info "  Logs:   tail -f $LOG_FILE"
    print_info "  Status: $PYTHON_CMD main_optimized.py --status"
}

# Function to show logs
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        print_info "Showing live logs (Ctrl+C to exit):"
        echo "======================================="
        tail -f "$LOG_FILE"
    else
        print_warning "No log file found at $LOG_FILE"
        exit 1
    fi
}

# Function to restart pipeline
restart_pipeline() {
    print_status "Restarting Optimized MTS Crypto Data Pipeline"
    stop_pipeline
    sleep 2
    start_pipeline
}

# Main script logic
case "${1:-}" in
    start)
        start_pipeline
        ;;
    stop)
        stop_pipeline
        ;;
    restart)
        restart_pipeline
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo
        echo "Commands:"
        echo "  start    - Start the optimized pipeline background service"
        echo "  stop     - Stop the pipeline gracefully"
        echo "  restart  - Restart the pipeline"
        echo "  status   - Show current status and recent activity"
        echo "  logs     - Show live log output"
        echo
        echo "Optimized Collection Strategy:"
        echo "  • BTC & ETH: Every 15 minutes (critical pairs)"
        echo "  • Other cryptos: Every 60 minutes"
        echo "  • Macro indicators: Daily updates"
        echo "  • Total: ~393 API calls/day (86% reduction vs all-15min)"
        exit 1
        ;;
esac 
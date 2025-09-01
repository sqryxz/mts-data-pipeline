#!/bin/bash

# Fix Duplicate Discord Alerts Script
# This script identifies and kills duplicate MTS processes that cause duplicate Discord alerts

echo "🔍 Checking for duplicate MTS processes..."

# Find all main_enhanced.py processes
PROCESSES=$(ps aux | grep "main_enhanced.py" | grep -v grep | awk '{print $2}')

if [ -z "$PROCESSES" ]; then
    echo "✅ No MTS processes found running"
    exit 0
fi

# Count processes
COUNT=$(echo "$PROCESSES" | wc -l)

if [ "$COUNT" -eq 1 ]; then
    echo "✅ Only one MTS process running (PID: $PROCESSES)"
    echo "✅ No duplicate alerts issue detected"
    exit 0
fi

echo "⚠️  Found $COUNT MTS processes running:"
echo "$PROCESSES" | while read -r pid; do
    echo "   PID: $pid"
done

echo ""
echo "🔧 Killing duplicate processes..."

# Keep the newest process (highest PID) and kill the rest
NEWEST_PID=$(echo "$PROCESSES" | sort -n | tail -1)
echo "   Keeping newest process: PID $NEWEST_PID"

echo "$PROCESSES" | while read -r pid; do
    if [ "$pid" != "$NEWEST_PID" ]; then
        echo "   Killing PID $pid"
        kill "$pid"
    fi
done

echo ""
echo "✅ Duplicate processes killed"
echo "✅ Only one MTS process should now be running"

# Verify
sleep 2
REMAINING=$(ps aux | grep "main_enhanced.py" | grep -v grep | wc -l)
if [ "$REMAINING" -eq 1 ]; then
    echo "✅ Verification successful: Only one process remaining"
else
    echo "⚠️  Warning: $REMAINING processes still running"
fi

echo ""
echo "💡 To prevent this in the future:"
echo "   • Use 'python3 scripts/check_discord_alerts.py' to monitor"
echo "   • Check for multiple processes before starting new ones"
echo "   • Use this script: 'bash scripts/fix_duplicate_alerts.sh'"

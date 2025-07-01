#!/bin/bash

# Automated Data Collection Scheduler for MTS Data Pipeline
# This script loads environment variables and starts the scheduler

# Load environment variables from .env file
if [ -f .env ]; then
    echo "🔑 Loading environment variables from .env..."
    source .env
else
    echo "❌ Error: .env file not found. Please create it with your FRED_API_KEY."
    exit 1
fi

# Check if FRED API key is set (if macro collection is enabled)
if [ -z "$FRED_API_KEY" ]; then
    echo "⚠️  Warning: FRED_API_KEY not found in environment variables."
    echo "   Macro collection will be disabled if requested."
fi

# Default values
INTERVAL=${1:-60}       # Default: 60 minutes
DAYS=${2:-1}           # Default: 1 day
COLLECT_CRYPTO=${3:-true}      # Default: collect crypto
COLLECT_MACRO=${4:-false}      # Default: don't collect macro

echo "🤖 Starting automated data collection scheduler..."
echo "⏱️  Interval: $INTERVAL minutes"
echo "📅 Days per collection: $DAYS"
echo "🪙 Crypto collection: $COLLECT_CRYPTO"
echo "📈 Macro collection: $COLLECT_MACRO"
echo ""

# Build command based on parameters
CMD="python3 main.py --schedule --days $DAYS --interval $INTERVAL"

if [ "$COLLECT_CRYPTO" = "true" ]; then
    CMD="$CMD --collect"
fi

if [ "$COLLECT_MACRO" = "true" ]; then
    CMD="$CMD --collect-macro"
fi

echo "🚀 Running: $CMD"
echo "💡 Press Ctrl+C to stop the scheduler"
echo ""

# Run the scheduler
exec $CMD 
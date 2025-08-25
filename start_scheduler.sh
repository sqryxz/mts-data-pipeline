#!/bin/bash
# Startup script for MTS Enhanced Scheduler with proper environment loading

echo "🚀 Starting MTS Enhanced Scheduler..."

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found"
    exit 1
fi

# Verify critical environment variables
if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    echo "❌ DISCORD_WEBHOOK_URL not set"
    exit 1
fi

if [ -z "$DISCORD_ALERTS_ENABLED" ]; then
    echo "❌ DISCORD_ALERTS_ENABLED not set"
    exit 1
fi

echo "🔧 Configuration:"
echo "   Discord Webhook: ${DISCORD_WEBHOOK_URL:0:50}..."
echo "   Discord Alerts: $DISCORD_ALERTS_ENABLED"
echo "   Min Confidence: $DISCORD_MIN_CONFIDENCE"
echo "   Min Strength: $DISCORD_MIN_STRENGTH"
echo "   Rate Limit: $DISCORD_RATE_LIMIT_SECONDS seconds"

# Start the scheduler
echo "🚀 Starting enhanced scheduler in background..."
python3 main_enhanced.py --background

echo "✅ Scheduler started successfully!"
echo "📊 Monitor with: python3 monitor_signal_system.py"
echo "📋 Check status with: python3 main_enhanced.py --status"
